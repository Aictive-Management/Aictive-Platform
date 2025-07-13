"""
Authentication and authorization for Aictive Platform
Following SuperClaude security standards
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from fastapi import HTTPException, Security, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
import bcrypt
from pydantic import BaseModel
import logging

from config import settings

logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

class TokenData(BaseModel):
    """JWT token payload"""
    sub: str  # Subject (user/api_key id)
    exp: datetime
    scopes: List[str] = []
    
class APIKey(BaseModel):
    """API Key model"""
    key_id: str
    key_hash: str
    name: str
    scopes: List[str]
    created_at: datetime
    last_used: Optional[datetime] = None
    is_active: bool = True

class AuthService:
    """Authentication service with security best practices"""
    
    def __init__(self):
        self.algorithm = "HS256"
        self.secret_key = settings.secret_key
        
    def create_access_token(
        self, 
        subject: str, 
        scopes: List[str] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Create JWT access token"""
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(hours=settings.token_expiry_hours)
        
        to_encode = {
            "sub": subject,
            "exp": expire,
            "scopes": scopes or []
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> TokenData:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return TokenData(**payload)
        except JWTError as e:
            logger.warning(f"JWT verification failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def hash_api_key(self, api_key: str) -> str:
        """Hash API key using bcrypt"""
        return bcrypt.hashpw(api_key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_api_key(self, api_key: str, hashed_key: str) -> bool:
        """Verify API key against hash"""
        return bcrypt.checkpw(api_key.encode('utf-8'), hashed_key.encode('utf-8'))

# Initialize service
auth_service = AuthService()

# Dependency functions
async def get_current_token(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> TokenData:
    """Get current token from request"""
    token = credentials.credentials
    return auth_service.verify_token(token)

async def require_scopes(required_scopes: List[str]):
    """Require specific scopes for endpoint access"""
    async def scope_checker(token_data: TokenData = Depends(get_current_token)):
        for scope in required_scopes:
            if scope not in token_data.scopes:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required scope: {scope}"
                )
        return token_data
    return scope_checker

# Scope definitions
class Scopes:
    """API scope definitions"""
    EMAIL_READ = "email:read"
    EMAIL_WRITE = "email:write"
    EMAIL_CLASSIFY = "email:classify"
    MAINTENANCE_ANALYZE = "maintenance:analyze"
    RESPONSE_GENERATE = "response:generate"
    COMPLIANCE_CHECK = "compliance:check"
    STATS_READ = "stats:read"
    WEBHOOK_WRITE = "webhook:write"
    ADMIN = "admin"
    
    @classmethod
    def all_scopes(cls) -> List[str]:
        """Get all available scopes"""
        return [
            cls.EMAIL_READ, cls.EMAIL_WRITE, cls.EMAIL_CLASSIFY,
            cls.MAINTENANCE_ANALYZE, cls.RESPONSE_GENERATE,
            cls.COMPLIANCE_CHECK, cls.STATS_READ, cls.WEBHOOK_WRITE,
            cls.ADMIN
        ]
    
    @classmethod
    def default_scopes(cls) -> List[str]:
        """Get default scopes for new API keys"""
        return [
            cls.EMAIL_READ, cls.EMAIL_CLASSIFY,
            cls.MAINTENANCE_ANALYZE, cls.RESPONSE_GENERATE
        ]

# Rate limiting storage (in production, use Redis)
rate_limit_storage: Dict[str, List[datetime]] = {}

async def check_rate_limit(
    token_data: TokenData = Depends(get_current_token)
) -> None:
    """Check rate limit for current user"""
    user_id = token_data.sub
    now = datetime.utcnow()
    
    # Clean old entries
    if user_id in rate_limit_storage:
        rate_limit_storage[user_id] = [
            timestamp for timestamp in rate_limit_storage[user_id]
            if now - timestamp < timedelta(minutes=1)
        ]
    else:
        rate_limit_storage[user_id] = []
    
    # Check limit
    if len(rate_limit_storage[user_id]) >= settings.rate_limit_per_minute:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later."
        )
    
    # Add current request
    rate_limit_storage[user_id].append(now)

# Security headers middleware
async def security_headers(request, call_next):
    """Add security headers to responses"""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response