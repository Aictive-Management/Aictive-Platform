"""
Data Encryption System for Aictive Platform
Provides encryption at rest, field-level encryption, and secure credential storage.
"""
import os
import base64
import json
import hashlib
import secrets
from typing import Dict, Any, Optional, List, Union, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
import asyncio
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import aiofiles
import redis.asyncio as redis
from sqlalchemy import event, Column, String, DateTime, Integer, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.types import TypeDecorator, String as SQLString
import structlog

logger = structlog.get_logger()

Base = declarative_base()


class EncryptionMethod(Enum):
    """Supported encryption methods"""
    AES_256_GCM = "aes_256_gcm"
    AES_256_CBC = "aes_256_cbc"
    FERNET = "fernet"
    RSA_4096 = "rsa_4096"
    CHACHA20_POLY1305 = "chacha20_poly1305"


class KeyPurpose(Enum):
    """Key purposes for key management"""
    MASTER = "master"
    DATA_ENCRYPTION = "data_encryption"
    FIELD_ENCRYPTION = "field_encryption"
    CREDENTIAL_ENCRYPTION = "credential_encryption"
    BACKUP_ENCRYPTION = "backup_encryption"
    TRANSIT_ENCRYPTION = "transit_encryption"


@dataclass
class EncryptionKey:
    """Encryption key metadata"""
    key_id: str
    purpose: KeyPurpose
    algorithm: EncryptionMethod
    created_at: datetime
    rotated_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    is_active: bool = True
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if key is expired"""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'key_id': self.key_id,
            'purpose': self.purpose.value,
            'algorithm': self.algorithm.value,
            'created_at': self.created_at.isoformat(),
            'rotated_at': self.rotated_at.isoformat() if self.rotated_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'version': self.version,
            'metadata': self.metadata
        }


class KeyDerivation:
    """Key derivation functions"""
    
    @staticmethod
    def derive_key(
        master_key: bytes,
        salt: bytes,
        info: bytes,
        key_length: int = 32
    ) -> bytes:
        """Derive a key using PBKDF2"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=key_length,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        return kdf.derive(master_key)
    
    @staticmethod
    def generate_salt(length: int = 16) -> bytes:
        """Generate a random salt"""
        return secrets.token_bytes(length)


class AESEncryption:
    """AES encryption implementation"""
    
    @staticmethod
    def encrypt_aes_gcm(
        plaintext: bytes,
        key: bytes,
        associated_data: Optional[bytes] = None
    ) -> Tuple[bytes, bytes, bytes]:
        """Encrypt using AES-256-GCM"""
        # Generate random nonce
        nonce = secrets.token_bytes(12)
        
        # Create cipher
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce),
            backend=default_backend()
        )
        encryptor = cipher.encryptor()
        
        # Add associated data if provided
        if associated_data:
            encryptor.authenticate_additional_data(associated_data)
        
        # Encrypt
        ciphertext = encryptor.update(plaintext) + encryptor.finalize()
        
        return nonce, ciphertext, encryptor.tag
    
    @staticmethod
    def decrypt_aes_gcm(
        nonce: bytes,
        ciphertext: bytes,
        tag: bytes,
        key: bytes,
        associated_data: Optional[bytes] = None
    ) -> bytes:
        """Decrypt using AES-256-GCM"""
        cipher = Cipher(
            algorithms.AES(key),
            modes.GCM(nonce, tag),
            backend=default_backend()
        )
        decryptor = cipher.decryptor()
        
        if associated_data:
            decryptor.authenticate_additional_data(associated_data)
        
        return decryptor.update(ciphertext) + decryptor.finalize()


class KeyManager:
    """Secure key management system"""
    
    def __init__(
        self,
        key_store_path: Path = Path("./keys"),
        redis_url: str = "redis://localhost:6379"
    ):
        self.key_store_path = key_store_path
        self.key_store_path.mkdir(exist_ok=True, mode=0o700)
        self.redis_url = redis_url
        self.redis_client = None
        
        # In-memory cache for frequently used keys
        self._key_cache: Dict[str, bytes] = {}
        self._key_metadata: Dict[str, EncryptionKey] = {}
        
        # Master key (in production, use HSM or KMS)
        self._master_key = self._load_or_create_master_key()
    
    def _load_or_create_master_key(self) -> bytes:
        """Load or create master key"""
        master_key_file = self.key_store_path / "master.key"
        
        if master_key_file.exists():
            with open(master_key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new master key
            master_key = secrets.token_bytes(32)
            
            # Save securely (in production, use HSM)
            with open(master_key_file, 'wb') as f:
                f.write(master_key)
            
            # Set restrictive permissions
            os.chmod(master_key_file, 0o600)
            
            logger.info("Generated new master key")
            return master_key
    
    async def initialize(self):
        """Initialize key manager"""
        self.redis_client = await redis.from_url(self.redis_url)
        await self._load_keys()
        
        # Start key rotation scheduler
        asyncio.create_task(self._key_rotation_scheduler())
        
        logger.info("Key manager initialized")
    
    async def _load_keys(self):
        """Load encryption keys from storage"""
        # Load key metadata from Redis
        keys = await self.redis_client.keys("keystore:metadata:*")
        
        for key in keys:
            metadata_str = await self.redis_client.get(key)
            if metadata_str:
                metadata = json.loads(metadata_str)
                key_obj = EncryptionKey(
                    key_id=metadata['key_id'],
                    purpose=KeyPurpose(metadata['purpose']),
                    algorithm=EncryptionMethod(metadata['algorithm']),
                    created_at=datetime.fromisoformat(metadata['created_at']),
                    rotated_at=datetime.fromisoformat(metadata['rotated_at']) if metadata.get('rotated_at') else None,
                    expires_at=datetime.fromisoformat(metadata['expires_at']) if metadata.get('expires_at') else None,
                    is_active=metadata['is_active'],
                    version=metadata['version'],
                    metadata=metadata.get('metadata', {})
                )
                self._key_metadata[key_obj.key_id] = key_obj
    
    async def generate_key(
        self,
        purpose: KeyPurpose,
        algorithm: EncryptionMethod = EncryptionMethod.AES_256_GCM,
        expires_in_days: Optional[int] = 365
    ) -> str:
        """Generate a new encryption key"""
        key_id = f"{purpose.value}_{secrets.token_urlsafe(16)}"
        
        # Generate key based on algorithm
        if algorithm in [EncryptionMethod.AES_256_GCM, EncryptionMethod.AES_256_CBC]:
            key_material = secrets.token_bytes(32)  # 256 bits
        elif algorithm == EncryptionMethod.FERNET:
            key_material = Fernet.generate_key()
        elif algorithm == EncryptionMethod.RSA_4096:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=4096,
                backend=default_backend()
            )
            key_material = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
        
        # Derive key from master key
        salt = KeyDerivation.generate_salt()
        derived_key = KeyDerivation.derive_key(
            self._master_key,
            salt,
            key_id.encode()
        )
        
        # Encrypt key material
        fernet = Fernet(base64.urlsafe_b64encode(derived_key))
        encrypted_key = fernet.encrypt(key_material)
        
        # Store encrypted key
        key_file = self.key_store_path / f"{key_id}.enc"
        async with aiofiles.open(key_file, 'wb') as f:
            await f.write(salt + encrypted_key)
        
        # Create metadata
        key_metadata = EncryptionKey(
            key_id=key_id,
            purpose=purpose,
            algorithm=algorithm,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + timedelta(days=expires_in_days) if expires_in_days else None
        )
        
        # Store metadata in Redis
        await self.redis_client.setex(
            f"keystore:metadata:{key_id}",
            timedelta(days=365 * 10),  # Keep metadata for 10 years
            json.dumps(key_metadata.to_dict())
        )
        
        self._key_metadata[key_id] = key_metadata
        logger.info(f"Generated new key: {key_id}")
        
        return key_id
    
    async def get_key(self, key_id: str) -> bytes:
        """Retrieve an encryption key"""
        # Check cache
        if key_id in self._key_cache:
            return self._key_cache[key_id]
        
        # Check if key exists
        if key_id not in self._key_metadata:
            raise KeyError(f"Key not found: {key_id}")
        
        metadata = self._key_metadata[key_id]
        
        # Check if key is active and not expired
        if not metadata.is_active:
            raise ValueError(f"Key is inactive: {key_id}")
        
        if metadata.is_expired():
            raise ValueError(f"Key has expired: {key_id}")
        
        # Load encrypted key
        key_file = self.key_store_path / f"{key_id}.enc"
        if not key_file.exists():
            raise FileNotFoundError(f"Key file not found: {key_id}")
        
        async with aiofiles.open(key_file, 'rb') as f:
            data = await f.read()
        
        # Extract salt and encrypted key
        salt = data[:16]
        encrypted_key = data[16:]
        
        # Derive decryption key
        derived_key = KeyDerivation.derive_key(
            self._master_key,
            salt,
            key_id.encode()
        )
        
        # Decrypt key
        fernet = Fernet(base64.urlsafe_b64encode(derived_key))
        key_material = fernet.decrypt(encrypted_key)
        
        # Cache for performance
        self._key_cache[key_id] = key_material
        
        return key_material
    
    async def rotate_key(self, old_key_id: str) -> str:
        """Rotate an encryption key"""
        if old_key_id not in self._key_metadata:
            raise KeyError(f"Key not found: {old_key_id}")
        
        old_metadata = self._key_metadata[old_key_id]
        
        # Generate new key
        new_key_id = await self.generate_key(
            purpose=old_metadata.purpose,
            algorithm=old_metadata.algorithm
        )
        
        # Update old key metadata
        old_metadata.is_active = False
        old_metadata.rotated_at = datetime.utcnow()
        
        # Store updated metadata
        await self.redis_client.setex(
            f"keystore:metadata:{old_key_id}",
            timedelta(days=365 * 10),
            json.dumps(old_metadata.to_dict())
        )
        
        # Update new key version
        new_metadata = self._key_metadata[new_key_id]
        new_metadata.version = old_metadata.version + 1
        new_metadata.metadata['rotated_from'] = old_key_id
        
        await self.redis_client.setex(
            f"keystore:metadata:{new_key_id}",
            timedelta(days=365 * 10),
            json.dumps(new_metadata.to_dict())
        )
        
        logger.info(f"Rotated key: {old_key_id} -> {new_key_id}")
        
        return new_key_id
    
    async def _key_rotation_scheduler(self):
        """Background task for automatic key rotation"""
        while True:
            try:
                # Check keys that need rotation
                for key_id, metadata in self._key_metadata.items():
                    if metadata.is_active and metadata.expires_at:
                        # Rotate keys 30 days before expiration
                        rotation_date = metadata.expires_at - timedelta(days=30)
                        if datetime.utcnow() >= rotation_date:
                            await self.rotate_key(key_id)
                
                # Run every 24 hours
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in key rotation scheduler: {e}")
                await asyncio.sleep(3600)


class DataEncryptor:
    """Main data encryption service"""
    
    def __init__(self, key_manager: KeyManager):
        self.key_manager = key_manager
        self._field_keys: Dict[str, str] = {}  # field -> key_id mapping
    
    async def encrypt_data(
        self,
        data: bytes,
        key_id: Optional[str] = None,
        purpose: KeyPurpose = KeyPurpose.DATA_ENCRYPTION,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Encrypt data using specified key"""
        # Get or generate key
        if not key_id:
            key_id = await self.key_manager.generate_key(purpose)
        
        key = await self.key_manager.get_key(key_id)
        key_metadata = self.key_manager._key_metadata[key_id]
        
        # Encrypt based on algorithm
        if key_metadata.algorithm == EncryptionMethod.AES_256_GCM:
            # Add metadata as associated data
            associated_data = json.dumps(metadata).encode() if metadata else None
            nonce, ciphertext, tag = AESEncryption.encrypt_aes_gcm(
                data, key[:32], associated_data
            )
            
            return {
                'ciphertext': base64.b64encode(ciphertext).decode(),
                'nonce': base64.b64encode(nonce).decode(),
                'tag': base64.b64encode(tag).decode(),
                'key_id': key_id,
                'algorithm': key_metadata.algorithm.value,
                'metadata': metadata
            }
            
        elif key_metadata.algorithm == EncryptionMethod.FERNET:
            fernet = Fernet(key)
            ciphertext = fernet.encrypt(data)
            
            return {
                'ciphertext': ciphertext.decode(),
                'key_id': key_id,
                'algorithm': key_metadata.algorithm.value,
                'metadata': metadata
            }
        
        else:
            raise ValueError(f"Unsupported algorithm: {key_metadata.algorithm}")
    
    async def decrypt_data(self, encrypted_data: Dict[str, Any]) -> bytes:
        """Decrypt data"""
        key_id = encrypted_data['key_id']
        key = await self.key_manager.get_key(key_id)
        algorithm = EncryptionMethod(encrypted_data['algorithm'])
        
        if algorithm == EncryptionMethod.AES_256_GCM:
            ciphertext = base64.b64decode(encrypted_data['ciphertext'])
            nonce = base64.b64decode(encrypted_data['nonce'])
            tag = base64.b64decode(encrypted_data['tag'])
            
            # Reconstruct associated data
            metadata = encrypted_data.get('metadata')
            associated_data = json.dumps(metadata).encode() if metadata else None
            
            return AESEncryption.decrypt_aes_gcm(
                nonce, ciphertext, tag, key[:32], associated_data
            )
            
        elif algorithm == EncryptionMethod.FERNET:
            fernet = Fernet(key)
            return fernet.decrypt(encrypted_data['ciphertext'].encode())
        
        else:
            raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    async def set_field_encryption_key(self, field_name: str, key_id: str):
        """Set encryption key for a specific field"""
        self._field_keys[field_name] = key_id
        
        # Store mapping in Redis
        await self.key_manager.redis_client.hset(
            "field_encryption_keys",
            field_name,
            key_id
        )
    
    async def encrypt_field(self, field_name: str, value: Any) -> str:
        """Encrypt a field value"""
        # Get field-specific key
        key_id = self._field_keys.get(field_name)
        if not key_id:
            # Generate new key for field
            key_id = await self.key_manager.generate_key(
                purpose=KeyPurpose.FIELD_ENCRYPTION
            )
            await self.set_field_encryption_key(field_name, key_id)
        
        # Serialize value
        serialized = json.dumps(value).encode()
        
        # Encrypt
        encrypted = await self.encrypt_data(
            serialized,
            key_id=key_id,
            metadata={'field': field_name}
        )
        
        # Return as base64 string
        return base64.b64encode(json.dumps(encrypted).encode()).decode()
    
    async def decrypt_field(self, field_name: str, encrypted_value: str) -> Any:
        """Decrypt a field value"""
        # Decode
        encrypted_data = json.loads(base64.b64decode(encrypted_value))
        
        # Decrypt
        decrypted = await self.decrypt_data(encrypted_data)
        
        # Deserialize
        return json.loads(decrypted)


# SQLAlchemy encrypted field types
class EncryptedType(TypeDecorator):
    """SQLAlchemy type for encrypted fields"""
    impl = Text
    cache_ok = True
    
    def __init__(self, encryptor: DataEncryptor, field_name: str):
        self.encryptor = encryptor
        self.field_name = field_name
        super().__init__()
    
    def process_bind_param(self, value, dialect):
        """Encrypt value before storing"""
        if value is None:
            return None
        
        # Run encryption in async context
        loop = asyncio.get_event_loop()
        encrypted = loop.run_until_complete(
            self.encryptor.encrypt_field(self.field_name, value)
        )
        return encrypted
    
    def process_result_value(self, value, dialect):
        """Decrypt value after loading"""
        if value is None:
            return None
        
        # Run decryption in async context
        loop = asyncio.get_event_loop()
        decrypted = loop.run_until_complete(
            self.encryptor.decrypt_field(self.field_name, value)
        )
        return decrypted


class SecureCredentialStore:
    """Secure storage for credentials and secrets"""
    
    def __init__(self, encryptor: DataEncryptor):
        self.encryptor = encryptor
        self._credential_key_id = None
    
    async def initialize(self):
        """Initialize credential store"""
        # Generate or get credential encryption key
        keys = [
            k for k, v in self.encryptor.key_manager._key_metadata.items()
            if v.purpose == KeyPurpose.CREDENTIAL_ENCRYPTION and v.is_active
        ]
        
        if keys:
            self._credential_key_id = keys[0]
        else:
            self._credential_key_id = await self.encryptor.key_manager.generate_key(
                purpose=KeyPurpose.CREDENTIAL_ENCRYPTION,
                algorithm=EncryptionMethod.AES_256_GCM
            )
    
    async def store_credential(
        self,
        credential_id: str,
        credential_data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store encrypted credential"""
        # Serialize credential data
        serialized = json.dumps(credential_data).encode()
        
        # Encrypt
        encrypted = await self.encryptor.encrypt_data(
            serialized,
            key_id=self._credential_key_id,
            metadata={
                'credential_id': credential_id,
                'stored_at': datetime.utcnow().isoformat(),
                **(metadata or {})
            }
        )
        
        # Store in Redis with TTL
        await self.encryptor.key_manager.redis_client.setex(
            f"credentials:{credential_id}",
            timedelta(days=365),  # 1 year TTL
            json.dumps(encrypted)
        )
        
        logger.info(f"Stored encrypted credential: {credential_id}")
    
    async def retrieve_credential(self, credential_id: str) -> Dict[str, Any]:
        """Retrieve and decrypt credential"""
        # Get from Redis
        encrypted_str = await self.encryptor.key_manager.redis_client.get(
            f"credentials:{credential_id}"
        )
        
        if not encrypted_str:
            raise KeyError(f"Credential not found: {credential_id}")
        
        # Decrypt
        encrypted_data = json.loads(encrypted_str)
        decrypted = await self.encryptor.decrypt_data(encrypted_data)
        
        return json.loads(decrypted)
    
    async def delete_credential(self, credential_id: str) -> bool:
        """Delete credential"""
        result = await self.encryptor.key_manager.redis_client.delete(
            f"credentials:{credential_id}"
        )
        
        if result:
            logger.info(f"Deleted credential: {credential_id}")
        
        return bool(result)
    
    async def rotate_credentials(self) -> Dict[str, str]:
        """Rotate all stored credentials to new encryption key"""
        # Generate new key
        new_key_id = await self.encryptor.key_manager.rotate_key(
            self._credential_key_id
        )
        
        # Get all credentials
        pattern = "credentials:*"
        cursor = 0
        rotated = {}
        
        while True:
            cursor, keys = await self.encryptor.key_manager.redis_client.scan(
                cursor, match=pattern
            )
            
            for key in keys:
                credential_id = key.decode().split(':', 1)[1]
                
                try:
                    # Retrieve with old key
                    credential_data = await self.retrieve_credential(credential_id)
                    
                    # Update key reference
                    old_key = self._credential_key_id
                    self._credential_key_id = new_key_id
                    
                    # Re-encrypt with new key
                    await self.store_credential(
                        credential_id,
                        credential_data,
                        metadata={'rotated_from': old_key}
                    )
                    
                    rotated[credential_id] = new_key_id
                    
                except Exception as e:
                    logger.error(f"Failed to rotate credential {credential_id}: {e}")
            
            if cursor == 0:
                break
        
        logger.info(f"Rotated {len(rotated)} credentials to new key")
        return rotated


class EncryptionMonitor:
    """Monitor encryption operations and performance"""
    
    def __init__(self, encryptor: DataEncryptor):
        self.encryptor = encryptor
        self.metrics = {
            'encryptions': 0,
            'decryptions': 0,
            'key_rotations': 0,
            'errors': 0,
            'performance': []
        }
    
    async def track_operation(
        self,
        operation: str,
        duration_ms: float,
        success: bool,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track encryption operation"""
        # Update counters
        if operation == 'encrypt':
            self.metrics['encryptions'] += 1
        elif operation == 'decrypt':
            self.metrics['decryptions'] += 1
        elif operation == 'rotate':
            self.metrics['key_rotations'] += 1
        
        if not success:
            self.metrics['errors'] += 1
        
        # Track performance
        self.metrics['performance'].append({
            'operation': operation,
            'duration_ms': duration_ms,
            'timestamp': datetime.utcnow().isoformat(),
            'success': success,
            'metadata': metadata
        })
        
        # Keep only last 1000 entries
        if len(self.metrics['performance']) > 1000:
            self.metrics['performance'] = self.metrics['performance'][-1000:]
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get encryption metrics"""
        # Calculate performance stats
        if self.metrics['performance']:
            durations = [p['duration_ms'] for p in self.metrics['performance']]
            avg_duration = sum(durations) / len(durations)
            max_duration = max(durations)
            min_duration = min(durations)
        else:
            avg_duration = max_duration = min_duration = 0
        
        return {
            'total_encryptions': self.metrics['encryptions'],
            'total_decryptions': self.metrics['decryptions'],
            'total_key_rotations': self.metrics['key_rotations'],
            'total_errors': self.metrics['errors'],
            'performance': {
                'average_duration_ms': avg_duration,
                'max_duration_ms': max_duration,
                'min_duration_ms': min_duration
            },
            'active_keys': len([
                k for k, v in self.encryptor.key_manager._key_metadata.items()
                if v.is_active
            ])
        }


# Database encryption example
class EncryptedModel(Base):
    """Example SQLAlchemy model with encrypted fields"""
    __tablename__ = 'encrypted_data'
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Regular fields
    name = Column(String(255))
    
    # Encrypted fields (initialized later with encryptor)
    ssn = Column(Text)  # Will be wrapped with EncryptedType
    credit_card = Column(Text)  # Will be wrapped with EncryptedType
    personal_data = Column(Text)  # Will be wrapped with EncryptedType


def setup_database_encryption(encryptor: DataEncryptor, Base):
    """Setup transparent database encryption"""
    
    # Wrap encrypted columns
    EncryptedModel.ssn = Column(EncryptedType(encryptor, 'ssn'))
    EncryptedModel.credit_card = Column(EncryptedType(encryptor, 'credit_card'))
    EncryptedModel.personal_data = Column(EncryptedType(encryptor, 'personal_data'))
    
    logger.info("Database encryption configured")


# Example usage
async def setup_encryption(redis_url: str = "redis://localhost:6379"):
    """Setup encryption system"""
    # Initialize key manager
    key_manager = KeyManager(redis_url=redis_url)
    await key_manager.initialize()
    
    # Initialize encryptor
    encryptor = DataEncryptor(key_manager)
    
    # Initialize credential store
    credential_store = SecureCredentialStore(encryptor)
    await credential_store.initialize()
    
    # Setup monitoring
    monitor = EncryptionMonitor(encryptor)
    
    return encryptor, credential_store, monitor