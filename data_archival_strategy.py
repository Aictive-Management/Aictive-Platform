"""
Data Archival Strategy for Aictive Platform
Implements time-based archival rules, cold storage integration,
data retention policies, archive restoration, and compliance auditing
"""

import asyncio
import logging
import json
import gzip
import pickle
from typing import Dict, List, Any, Optional, Tuple, Callable, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import hashlib
import boto3
from google.cloud import storage as gcs
import aiofiles

from data_layer_core import db_manager, get_db_connection, execute_query

logger = logging.getLogger(__name__)


class ArchivalStatus(Enum):
    """Status of archival operations"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"
    EXPIRED = "expired"


class StorageProvider(Enum):
    """Supported cold storage providers"""
    AWS_S3 = "aws_s3"
    GOOGLE_CLOUD = "google_cloud"
    AZURE_BLOB = "azure_blob"
    LOCAL_FILESYSTEM = "local_filesystem"


class DataCategory(Enum):
    """Categories of data for different retention policies"""
    FINANCIAL = "financial"        # 7+ years retention
    OPERATIONAL = "operational"    # 3-5 years retention
    ANALYTICS = "analytics"        # 1-2 years retention
    LOGS = "logs"                 # 90 days retention
    CACHE = "cache"               # 30 days retention
    TEMPORARY = "temporary"       # 7 days retention


class CompressionType(Enum):
    """Compression types for archived data"""
    NONE = "none"
    GZIP = "gzip"
    BZIP2 = "bzip2"
    LZMA = "lzma"


@dataclass
class RetentionPolicy:
    """Data retention policy configuration"""
    policy_id: str
    name: str
    description: str
    data_category: DataCategory
    retention_days: int
    archive_after_days: int
    delete_after_days: Optional[int]  # None for permanent retention
    table_patterns: List[str]  # Regex patterns for table names
    column_filters: Dict[str, Any] = field(default_factory=dict)  # Additional filters
    compression: CompressionType = CompressionType.GZIP
    storage_class: str = "STANDARD_IA"  # Storage class (S3/GCS specific)
    enabled: bool = True
    compliance_tags: List[str] = field(default_factory=list)


@dataclass
class ArchivalRule:
    """Specific archival rule for a table/entity"""
    rule_id: str
    table_name: str
    date_column: str  # Column used for date-based archival
    retention_policy: RetentionPolicy
    batch_size: int = 1000
    partition_column: Optional[str] = None  # For partitioned archival
    where_clause: Optional[str] = None  # Additional filtering
    dependencies: List[str] = field(default_factory=list)  # Other tables to check
    post_archive_actions: List[str] = field(default_factory=list)  # Cleanup actions


@dataclass
class ArchivalExecution:
    """Record of archival execution"""
    execution_id: str
    rule_id: str
    table_name: str
    status: ArchivalStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    rows_archived: int = 0
    bytes_archived: int = 0
    archive_location: Optional[str] = None
    checksum: Optional[str] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StorageConfig:
    """Configuration for cold storage provider"""
    provider: StorageProvider
    bucket_name: str
    region: Optional[str] = None
    access_key: Optional[str] = None
    secret_key: Optional[str] = None
    endpoint_url: Optional[str] = None
    encryption: bool = True
    versioning: bool = True
    lifecycle_rules: List[Dict] = field(default_factory=list)


class StorageBackend:
    """Abstract base class for storage backends"""
    
    async def upload(self, key: str, data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Upload data to storage"""
        raise NotImplementedError
    
    async def download(self, key: str) -> bytes:
        """Download data from storage"""
        raise NotImplementedError
    
    async def delete(self, key: str) -> bool:
        """Delete data from storage"""
        raise NotImplementedError
    
    async def list_objects(self, prefix: str) -> List[Dict[str, Any]]:
        """List objects with prefix"""
        raise NotImplementedError
    
    async def get_metadata(self, key: str) -> Dict[str, Any]:
        """Get object metadata"""
        raise NotImplementedError


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.client = boto3.client(
            's3',
            aws_access_key_id=config.access_key,
            aws_secret_access_key=config.secret_key,
            endpoint_url=config.endpoint_url,
            region_name=config.region
        )
    
    async def upload(self, key: str, data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Upload data to S3"""
        try:
            extra_args = {}
            
            if metadata:
                extra_args['Metadata'] = {str(k): str(v) for k, v in metadata.items()}
            
            if self.config.encryption:
                extra_args['ServerSideEncryption'] = 'AES256'
            
            # Upload in background thread for async compatibility
            import asyncio
            loop = asyncio.get_event_loop()
            
            await loop.run_in_executor(
                None,
                lambda: self.client.put_object(
                    Bucket=self.config.bucket_name,
                    Key=key,
                    Body=data,
                    **extra_args
                )
            )
            
            return f"s3://{self.config.bucket_name}/{key}"
            
        except Exception as e:
            logger.error(f"S3 upload failed for key {key}: {str(e)}")
            raise
    
    async def download(self, key: str) -> bytes:
        """Download data from S3"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.get_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            
            return response['Body'].read()
            
        except Exception as e:
            logger.error(f"S3 download failed for key {key}: {str(e)}")
            raise
    
    async def delete(self, key: str) -> bool:
        """Delete data from S3"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            await loop.run_in_executor(
                None,
                lambda: self.client.delete_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            
            return True
            
        except Exception as e:
            logger.error(f"S3 delete failed for key {key}: {str(e)}")
            return False
    
    async def list_objects(self, prefix: str) -> List[Dict[str, Any]]:
        """List objects with prefix"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.list_objects_v2(
                    Bucket=self.config.bucket_name,
                    Prefix=prefix
                )
            )
            
            return response.get('Contents', [])
            
        except Exception as e:
            logger.error(f"S3 list failed for prefix {prefix}: {str(e)}")
            return []
    
    async def get_metadata(self, key: str) -> Dict[str, Any]:
        """Get object metadata"""
        try:
            import asyncio
            loop = asyncio.get_event_loop()
            
            response = await loop.run_in_executor(
                None,
                lambda: self.client.head_object(
                    Bucket=self.config.bucket_name,
                    Key=key
                )
            )
            
            return response.get('Metadata', {})
            
        except Exception as e:
            logger.error(f"S3 metadata failed for key {key}: {str(e)}")
            return {}


class LocalFilesystemBackend(StorageBackend):
    """Local filesystem storage backend"""
    
    def __init__(self, config: StorageConfig):
        self.config = config
        self.base_path = Path(config.bucket_name)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    async def upload(self, key: str, data: bytes, metadata: Dict[str, Any] = None) -> str:
        """Upload data to local filesystem"""
        try:
            file_path = self.base_path / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(data)
            
            # Store metadata separately
            if metadata:
                metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
                async with aiofiles.open(metadata_path, 'w') as f:
                    await f.write(json.dumps(metadata))
            
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Local upload failed for key {key}: {str(e)}")
            raise
    
    async def download(self, key: str) -> bytes:
        """Download data from local filesystem"""
        try:
            file_path = self.base_path / key
            
            async with aiofiles.open(file_path, 'rb') as f:
                return await f.read()
                
        except Exception as e:
            logger.error(f"Local download failed for key {key}: {str(e)}")
            raise
    
    async def delete(self, key: str) -> bool:
        """Delete data from local filesystem"""
        try:
            file_path = self.base_path / key
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            
            if file_path.exists():
                file_path.unlink()
            
            if metadata_path.exists():
                metadata_path.unlink()
            
            return True
            
        except Exception as e:
            logger.error(f"Local delete failed for key {key}: {str(e)}")
            return False
    
    async def list_objects(self, prefix: str) -> List[Dict[str, Any]]:
        """List objects with prefix"""
        try:
            prefix_path = self.base_path / prefix
            objects = []
            
            if prefix_path.is_dir():
                for file_path in prefix_path.rglob('*'):
                    if file_path.is_file() and not file_path.suffix == '.meta':
                        relative_path = file_path.relative_to(self.base_path)
                        objects.append({
                            'Key': str(relative_path),
                            'Size': file_path.stat().st_size,
                            'LastModified': datetime.fromtimestamp(file_path.stat().st_mtime)
                        })
            
            return objects
            
        except Exception as e:
            logger.error(f"Local list failed for prefix {prefix}: {str(e)}")
            return []
    
    async def get_metadata(self, key: str) -> Dict[str, Any]:
        """Get object metadata"""
        try:
            file_path = self.base_path / key
            metadata_path = file_path.with_suffix(file_path.suffix + '.meta')
            
            if metadata_path.exists():
                async with aiofiles.open(metadata_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            
            return {}
            
        except Exception as e:
            logger.error(f"Local metadata failed for key {key}: {str(e)}")
            return {}


class DataCompressor:
    """Handles data compression for archival"""
    
    @staticmethod
    def compress(data: bytes, compression_type: CompressionType) -> bytes:
        """Compress data using specified method"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.compress(data)
        elif compression_type == CompressionType.BZIP2:
            import bz2
            return bz2.compress(data)
        elif compression_type == CompressionType.LZMA:
            import lzma
            return lzma.compress(data)
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")
    
    @staticmethod
    def decompress(data: bytes, compression_type: CompressionType) -> bytes:
        """Decompress data using specified method"""
        if compression_type == CompressionType.NONE:
            return data
        elif compression_type == CompressionType.GZIP:
            return gzip.decompress(data)
        elif compression_type == CompressionType.BZIP2:
            import bz2
            return bz2.decompress(data)
        elif compression_type == CompressionType.LZMA:
            import lzma
            return lzma.decompress(data)
        else:
            raise ValueError(f"Unsupported compression type: {compression_type}")


class ArchivalEngine:
    """Core archival engine that executes archival rules"""
    
    def __init__(self, storage_backend: StorageBackend):
        self.storage_backend = storage_backend
        self.compressor = DataCompressor()
    
    async def archive_data(
        self, 
        rule: ArchivalRule, 
        cutoff_date: datetime,
        dry_run: bool = False
    ) -> ArchivalExecution:
        """Archive data according to the specified rule"""
        
        execution_id = f"{rule.rule_id}_{int(datetime.utcnow().timestamp())}"
        execution = ArchivalExecution(
            execution_id=execution_id,
            rule_id=rule.rule_id,
            table_name=rule.table_name,
            status=ArchivalStatus.IN_PROGRESS,
            started_at=datetime.utcnow()
        )
        
        try:
            # Build query to select data for archival
            query = self._build_archival_query(rule, cutoff_date)
            
            if dry_run:
                # Just count rows that would be archived
                count_query = f"SELECT COUNT(*) as row_count FROM ({query}) as archival_data"
                async with get_db_connection() as conn:
                    result = await conn.fetchone(count_query)
                    execution.rows_archived = result['row_count'] if result else 0
                
                execution.status = ArchivalStatus.COMPLETED
                execution.completed_at = datetime.utcnow()
                logger.info(f"DRY RUN: Would archive {execution.rows_archived} rows from {rule.table_name}")
                return execution
            
            # Execute archival in batches
            total_rows = 0
            total_bytes = 0
            batch_number = 0
            
            while True:
                # Get batch of data
                batch_query = f"{query} LIMIT {rule.batch_size} OFFSET {batch_number * rule.batch_size}"
                
                async with get_db_connection() as conn:
                    batch_data = await conn.fetchall(batch_query)
                
                if not batch_data:
                    break  # No more data
                
                # Serialize and compress batch
                serialized_data = pickle.dumps(batch_data)
                compressed_data = self.compressor.compress(
                    serialized_data, 
                    rule.retention_policy.compression
                )
                
                # Generate archive key
                archive_key = self._generate_archive_key(rule, cutoff_date, batch_number)
                
                # Upload to storage
                metadata = {
                    'table_name': rule.table_name,
                    'rule_id': rule.rule_id,
                    'cutoff_date': cutoff_date.isoformat(),
                    'batch_number': batch_number,
                    'row_count': len(batch_data),
                    'compression': rule.retention_policy.compression.value,
                    'archived_at': datetime.utcnow().isoformat(),
                    'checksum': hashlib.sha256(compressed_data).hexdigest()
                }
                
                archive_location = await self.storage_backend.upload(
                    archive_key, 
                    compressed_data, 
                    metadata
                )
                
                total_rows += len(batch_data)
                total_bytes += len(compressed_data)
                batch_number += 1
                
                logger.info(f"Archived batch {batch_number} for {rule.table_name}: {len(batch_data)} rows")
                
                # Small delay to avoid overwhelming the database
                await asyncio.sleep(0.1)
            
            if total_rows > 0:
                # Delete archived data from primary database
                await self._delete_archived_data(rule, cutoff_date)
                
                # Execute post-archive actions
                await self._execute_post_archive_actions(rule)
            
            execution.rows_archived = total_rows
            execution.bytes_archived = total_bytes
            execution.archive_location = f"{rule.table_name}/{cutoff_date.strftime('%Y/%m/%d')}"
            execution.status = ArchivalStatus.COMPLETED
            execution.completed_at = datetime.utcnow()
            
            logger.info(
                f"Archival completed for {rule.table_name}: "
                f"{total_rows} rows, {total_bytes} bytes in {batch_number} batches"
            )
            
        except Exception as e:
            execution.status = ArchivalStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            
            logger.error(f"Archival failed for {rule.table_name}: {str(e)}")
        
        return execution
    
    def _build_archival_query(self, rule: ArchivalRule, cutoff_date: datetime) -> str:
        """Build SQL query to select data for archival"""
        base_query = f"SELECT * FROM {rule.table_name}"
        
        conditions = [f"{rule.date_column} < '{cutoff_date.isoformat()}'"]
        
        if rule.where_clause:
            conditions.append(rule.where_clause)
        
        if rule.partition_column:
            # Add partition-specific logic if needed
            pass
        
        where_clause = " AND ".join(conditions)
        return f"{base_query} WHERE {where_clause}"
    
    async def _delete_archived_data(self, rule: ArchivalRule, cutoff_date: datetime):
        """Delete archived data from primary database"""
        delete_query = f"""
        DELETE FROM {rule.table_name} 
        WHERE {rule.date_column} < '{cutoff_date.isoformat()}'
        """
        
        if rule.where_clause:
            delete_query += f" AND {rule.where_clause}"
        
        try:
            async with get_db_connection() as conn:
                result = await conn.execute(delete_query)
                logger.info(f"Deleted archived data from {rule.table_name}")
                
        except Exception as e:
            logger.error(f"Failed to delete archived data from {rule.table_name}: {str(e)}")
            raise
    
    async def _execute_post_archive_actions(self, rule: ArchivalRule):
        """Execute post-archival actions"""
        for action in rule.post_archive_actions:
            try:
                async with get_db_connection() as conn:
                    await conn.execute(action)
                logger.info(f"Executed post-archive action: {action}")
                
            except Exception as e:
                logger.error(f"Post-archive action failed: {action} - {str(e)}")
    
    def _generate_archive_key(self, rule: ArchivalRule, cutoff_date: datetime, batch_number: int) -> str:
        """Generate storage key for archived data"""
        date_path = cutoff_date.strftime('%Y/%m/%d')
        return f"archives/{rule.table_name}/{date_path}/{rule.rule_id}_batch_{batch_number:04d}.dat"
    
    async def restore_data(
        self, 
        table_name: str, 
        date_range: Tuple[datetime, datetime],
        target_table: str = None
    ) -> Dict[str, Any]:
        """Restore archived data back to the database"""
        
        start_date, end_date = date_range
        target_table = target_table or f"{table_name}_restored"
        
        # Find archive files in date range
        archive_prefix = f"archives/{table_name}/"
        archived_objects = await self.storage_backend.list_objects(archive_prefix)
        
        restored_rows = 0
        restored_batches = 0
        
        for obj in archived_objects:
            key = obj['Key']
            
            # Parse date from key to check if in range
            # This is simplified - would need proper date parsing
            if self._is_key_in_date_range(key, start_date, end_date):
                try:
                    # Download and decompress data
                    compressed_data = await self.storage_backend.download(key)
                    metadata = await self.storage_backend.get_metadata(key)
                    
                    compression_type = CompressionType(metadata.get('compression', 'gzip'))
                    serialized_data = self.compressor.decompress(compressed_data, compression_type)
                    batch_data = pickle.loads(serialized_data)
                    
                    # Insert data into target table
                    await self._insert_restored_data(target_table, batch_data)
                    
                    restored_rows += len(batch_data)
                    restored_batches += 1
                    
                    logger.info(f"Restored batch from {key}: {len(batch_data)} rows")
                    
                except Exception as e:
                    logger.error(f"Failed to restore from {key}: {str(e)}")
        
        return {
            "table_name": target_table,
            "restored_rows": restored_rows,
            "restored_batches": restored_batches,
            "date_range": [start_date.isoformat(), end_date.isoformat()]
        }
    
    def _is_key_in_date_range(self, key: str, start_date: datetime, end_date: datetime) -> bool:
        """Check if archive key falls within date range"""
        # Extract date from path like "archives/table/2023/12/15/batch.dat"
        import re
        date_pattern = r'(\d{4})/(\d{2})/(\d{2})'
        match = re.search(date_pattern, key)
        
        if match:
            year, month, day = map(int, match.groups())
            key_date = datetime(year, month, day)
            return start_date <= key_date <= end_date
        
        return False
    
    async def _insert_restored_data(self, table_name: str, batch_data: List[Dict]):
        """Insert restored data into target table"""
        if not batch_data:
            return
        
        # Create table if it doesn't exist (simplified)
        # In practice, you'd want proper schema management
        
        # Build insert query
        columns = list(batch_data[0].keys())
        column_list = ', '.join(columns)
        placeholders = ', '.join(['%s'] * len(columns))
        
        insert_query = f"INSERT INTO {table_name} ({column_list}) VALUES ({placeholders})"
        
        # Convert batch data to tuples
        values = [tuple(row[col] for col in columns) for row in batch_data]
        
        async with get_db_connection() as conn:
            # Execute batch insert
            for value_tuple in values:
                await conn.execute(insert_query, value_tuple)


class ArchivalManager:
    """Main archival management system"""
    
    def __init__(self, storage_config: StorageConfig):
        self.storage_config = storage_config
        self.storage_backend = self._create_storage_backend(storage_config)
        self.engine = ArchivalEngine(self.storage_backend)
        self.retention_policies: Dict[str, RetentionPolicy] = {}
        self.archival_rules: Dict[str, ArchivalRule] = {}
        self.execution_history: List[ArchivalExecution] = []
        
        # Default retention policies for RentVine data
        self._setup_default_policies()
        
        # Background archival task
        self._archival_task = None
    
    def _create_storage_backend(self, config: StorageConfig) -> StorageBackend:
        """Create appropriate storage backend"""
        if config.provider == StorageProvider.AWS_S3:
            return S3StorageBackend(config)
        elif config.provider == StorageProvider.LOCAL_FILESYSTEM:
            return LocalFilesystemBackend(config)
        else:
            raise ValueError(f"Unsupported storage provider: {config.provider}")
    
    def _setup_default_policies(self):
        """Setup default retention policies for common data types"""
        
        # Financial data - 7 years retention
        financial_policy = RetentionPolicy(
            policy_id="financial_7yr",
            name="Financial Data - 7 Year Retention",
            description="Financial transactions and accounting data",
            data_category=DataCategory.FINANCIAL,
            retention_days=7 * 365,  # 7 years
            archive_after_days=2 * 365,  # Archive after 2 years
            delete_after_days=None,  # Permanent retention
            table_patterns=["transactions", "payments", "invoices", "accounting_*"],
            compression=CompressionType.GZIP,
            compliance_tags=["SOX", "GAAP", "financial_records"]
        )
        self.retention_policies[financial_policy.policy_id] = financial_policy
        
        # Operational data - 3 years retention
        operational_policy = RetentionPolicy(
            policy_id="operational_3yr",
            name="Operational Data - 3 Year Retention",
            description="Property management and operational records",
            data_category=DataCategory.OPERATIONAL,
            retention_days=3 * 365,
            archive_after_days=365,  # Archive after 1 year
            delete_after_days=3 * 365,
            table_patterns=["work_orders", "maintenance_*", "tenant_communications"],
            compression=CompressionType.GZIP
        )
        self.retention_policies[operational_policy.policy_id] = operational_policy
        
        # Analytics data - 1 year retention
        analytics_policy = RetentionPolicy(
            policy_id="analytics_1yr",
            name="Analytics Data - 1 Year Retention",
            description="Analytics and reporting data",
            data_category=DataCategory.ANALYTICS,
            retention_days=365,
            archive_after_days=90,  # Archive after 3 months
            delete_after_days=365,
            table_patterns=["analytics_*", "reports_*", "metrics_*"],
            compression=CompressionType.GZIP
        )
        self.retention_policies[analytics_policy.policy_id] = analytics_policy
        
        # Log data - 90 days retention
        logs_policy = RetentionPolicy(
            policy_id="logs_90d",
            name="Log Data - 90 Day Retention",
            description="Application and system logs",
            data_category=DataCategory.LOGS,
            retention_days=90,
            archive_after_days=30,  # Archive after 1 month
            delete_after_days=90,
            table_patterns=["logs", "audit_*", "*_log"],
            compression=CompressionType.GZIP
        )
        self.retention_policies[logs_policy.policy_id] = logs_policy
    
    async def initialize(self):
        """Initialize the archival system"""
        await self._ensure_archival_tables()
        self._archival_task = asyncio.create_task(self._background_archival())
        logger.info("Archival system initialized")
    
    async def shutdown(self):
        """Shutdown the archival system"""
        if self._archival_task:
            self._archival_task.cancel()
            try:
                await self._archival_task
            except asyncio.CancelledError:
                pass
        logger.info("Archival system shutdown complete")
    
    async def _ensure_archival_tables(self):
        """Ensure archival tracking tables exist"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS archival_executions (
            execution_id VARCHAR(255) PRIMARY KEY,
            rule_id VARCHAR(255) NOT NULL,
            table_name VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            rows_archived INTEGER DEFAULT 0,
            bytes_archived BIGINT DEFAULT 0,
            archive_location TEXT,
            checksum VARCHAR(64),
            error_message TEXT,
            metadata JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_archival_executions_rule_id 
        ON archival_executions(rule_id);
        
        CREATE INDEX IF NOT EXISTS idx_archival_executions_table_name 
        ON archival_executions(table_name);
        
        CREATE INDEX IF NOT EXISTS idx_archival_executions_status 
        ON archival_executions(status);
        """
        
        try:
            async with get_db_connection() as conn:
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    await conn.execute(statement)
            
            logger.info("Archival tracking tables ensured")
        except Exception as e:
            logger.error(f"Failed to create archival tables: {str(e)}")
            raise
    
    def add_archival_rule(self, rule: ArchivalRule):
        """Add an archival rule"""
        self.archival_rules[rule.rule_id] = rule
        logger.info(f"Added archival rule: {rule.rule_id} for table {rule.table_name}")
    
    def add_retention_policy(self, policy: RetentionPolicy):
        """Add a retention policy"""
        self.retention_policies[policy.policy_id] = policy
        logger.info(f"Added retention policy: {policy.policy_id}")
    
    async def run_archival(self, rule_id: str = None, dry_run: bool = False) -> List[ArchivalExecution]:
        """Run archival for specific rule or all rules"""
        executions = []
        
        if rule_id:
            if rule_id not in self.archival_rules:
                raise ValueError(f"Archival rule {rule_id} not found")
            rules_to_run = [self.archival_rules[rule_id]]
        else:
            rules_to_run = list(self.archival_rules.values())
        
        for rule in rules_to_run:
            if not rule.retention_policy.enabled:
                continue
            
            # Calculate cutoff date
            cutoff_date = datetime.utcnow() - timedelta(days=rule.retention_policy.archive_after_days)
            
            try:
                execution = await self.engine.archive_data(rule, cutoff_date, dry_run)
                executions.append(execution)
                
                # Record execution
                await self._record_execution(execution)
                
            except Exception as e:
                logger.error(f"Archival failed for rule {rule.rule_id}: {str(e)}")
        
        return executions
    
    async def _record_execution(self, execution: ArchivalExecution):
        """Record archival execution in database"""
        query = """
        INSERT INTO archival_executions 
        (execution_id, rule_id, table_name, status, started_at, completed_at,
         rows_archived, bytes_archived, archive_location, checksum, error_message, metadata)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        status = VALUES(status),
        completed_at = VALUES(completed_at),
        rows_archived = VALUES(rows_archived),
        bytes_archived = VALUES(bytes_archived),
        archive_location = VALUES(archive_location),
        checksum = VALUES(checksum),
        error_message = VALUES(error_message),
        metadata = VALUES(metadata)
        """
        
        params = (
            execution.execution_id,
            execution.rule_id,
            execution.table_name,
            execution.status.value,
            execution.started_at,
            execution.completed_at,
            execution.rows_archived,
            execution.bytes_archived,
            execution.archive_location,
            execution.checksum,
            execution.error_message,
            json.dumps(execution.metadata)
        )
        
        try:
            async with get_db_connection() as conn:
                await conn.execute(query, params)
        except Exception as e:
            logger.error(f"Failed to record archival execution: {str(e)}")
    
    async def _background_archival(self):
        """Background task for automatic archival"""
        while True:
            try:
                # Run archival daily at 2 AM
                await asyncio.sleep(24 * 3600)  # 24 hours
                
                current_hour = datetime.utcnow().hour
                if current_hour == 2:  # 2 AM UTC
                    logger.info("Starting scheduled archival run")
                    await self.run_archival()
                    logger.info("Scheduled archival run completed")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background archival: {str(e)}")
    
    async def restore_data(
        self, 
        table_name: str, 
        start_date: datetime, 
        end_date: datetime,
        target_table: str = None
    ) -> Dict[str, Any]:
        """Restore archived data for a specific date range"""
        return await self.engine.restore_data(table_name, (start_date, end_date), target_table)
    
    async def get_archival_status(self) -> Dict[str, Any]:
        """Get comprehensive archival system status"""
        # Get recent executions
        query = """
        SELECT * FROM archival_executions 
        ORDER BY started_at DESC 
        LIMIT 50
        """
        
        try:
            async with get_db_connection() as conn:
                recent_executions = await conn.fetchall(query)
        except Exception as e:
            logger.error(f"Failed to get archival status: {str(e)}")
            recent_executions = []
        
        # Calculate statistics
        total_rules = len(self.archival_rules)
        enabled_policies = len([p for p in self.retention_policies.values() if p.enabled])
        
        successful_executions = len([e for e in recent_executions if e['status'] == 'completed'])
        failed_executions = len([e for e in recent_executions if e['status'] == 'failed'])
        
        return {
            "system_status": {
                "total_rules": total_rules,
                "enabled_policies": enabled_policies,
                "storage_provider": self.storage_config.provider.value,
                "storage_bucket": self.storage_config.bucket_name
            },
            "execution_summary": {
                "recent_successful": successful_executions,
                "recent_failed": failed_executions,
                "success_rate": (successful_executions / max(1, len(recent_executions))) * 100
            },
            "retention_policies": [
                {
                    "policy_id": p.policy_id,
                    "name": p.name,
                    "data_category": p.data_category.value,
                    "retention_days": p.retention_days,
                    "archive_after_days": p.archive_after_days,
                    "enabled": p.enabled
                }
                for p in self.retention_policies.values()
            ],
            "recent_executions": [
                {
                    "execution_id": e['execution_id'],
                    "table_name": e['table_name'],
                    "status": e['status'],
                    "started_at": e['started_at'].isoformat() if e['started_at'] else None,
                    "rows_archived": e['rows_archived'],
                    "bytes_archived": e['bytes_archived']
                }
                for e in recent_executions[:10]
            ]
        }
    
    def setup_rentvine_archival_rules(self):
        """Setup archival rules for RentVine data"""
        
        # Financial transactions
        transactions_rule = ArchivalRule(
            rule_id="rentvine_transactions",
            table_name="transactions",
            date_column="transaction_date",
            retention_policy=self.retention_policies["financial_7yr"],
            batch_size=500,
            where_clause="status = 'completed'"
        )
        self.add_archival_rule(transactions_rule)
        
        # Work orders
        work_orders_rule = ArchivalRule(
            rule_id="rentvine_work_orders",
            table_name="work_orders",
            date_column="completed_date",
            retention_policy=self.retention_policies["operational_3yr"],
            batch_size=1000,
            where_clause="status = 'completed'",
            post_archive_actions=[
                "UPDATE work_orders_summary SET archived_count = archived_count + @rows_archived WHERE date = CURDATE()"
            ]
        )
        self.add_archival_rule(work_orders_rule)
        
        # Tenant communications
        communications_rule = ArchivalRule(
            rule_id="rentvine_communications",
            table_name="tenant_communications",
            date_column="created_at",
            retention_policy=self.retention_policies["operational_3yr"],
            batch_size=2000
        )
        self.add_archival_rule(communications_rule)
        
        # Analytics data
        analytics_rule = ArchivalRule(
            rule_id="rentvine_analytics",
            table_name="analytics_events",
            date_column="event_timestamp",
            retention_policy=self.retention_policies["analytics_1yr"],
            batch_size=5000
        )
        self.add_archival_rule(analytics_rule)


# Global archival manager
archival_manager: Optional[ArchivalManager] = None


async def initialize_archival_system(storage_config: StorageConfig) -> ArchivalManager:
    """Initialize the global archival system"""
    global archival_manager
    
    archival_manager = ArchivalManager(storage_config)
    await archival_manager.initialize()
    
    # Setup RentVine-specific archival rules
    archival_manager.setup_rentvine_archival_rules()
    
    return archival_manager


async def run_archival(rule_id: str = None, dry_run: bool = False):
    """Run archival process"""
    if not archival_manager:
        raise RuntimeError("Archival system not initialized")
    
    return await archival_manager.run_archival(rule_id, dry_run)


async def restore_archived_data(table_name: str, start_date: datetime, end_date: datetime):
    """Restore archived data"""
    if not archival_manager:
        raise RuntimeError("Archival system not initialized")
    
    return await archival_manager.restore_data(table_name, start_date, end_date)


def get_archival_status():
    """Get archival system status"""
    if not archival_manager:
        raise RuntimeError("Archival system not initialized")
    
    return archival_manager.get_archival_status()