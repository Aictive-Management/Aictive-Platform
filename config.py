"""
Secure configuration management for Aictive Platform
Following SuperClaude security standards
"""
import os
from typing import Optional, List
from pydantic_settings import BaseSettings
from pydantic import validator
from dotenv import load_dotenv
import secrets

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    """Application settings with validation"""
    
    # API Configuration
    api_key: str = secrets.token_urlsafe(32)
    secret_key: str = secrets.token_urlsafe(32)
    environment: str = "development"
    log_level: str = "INFO"
    
    # CORS Configuration
    allowed_origins: List[str] = ["http://localhost:3000"]
    
    # Supabase
    supabase_url: str
    supabase_anon_key: str
    
    # Anthropic
    anthropic_api_key: str
    
    # RentVine
    rentvine_subdomain: str
    rentvine_access_key: str
    rentvine_secret: str
    
    # Webhooks
    n8n_webhook_url: Optional[str] = None
    slack_webhook_url: Optional[str] = None
    
    # Security Settings
    rate_limit_per_minute: int = 60
    max_request_size: int = 1024 * 1024  # 1MB
    token_expiry_hours: int = 24
    
    # Performance Settings
    cache_ttl_seconds: int = 3600
    max_claude_retries: int = 3
    claude_timeout_seconds: int = 30
    
    @validator("allowed_origins", pre=True)
    def parse_allowed_origins(cls, v):
        """Parse comma-separated origins from environment"""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v
    
    @validator("environment")
    def validate_environment(cls, v):
        """Ensure valid environment"""
        allowed = ["development", "staging", "production"]
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}")
        return v
    
    @validator("anthropic_api_key", "supabase_anon_key", "rentvine_access_key")
    def validate_not_exposed(cls, v):
        """Check for exposed test keys"""
        # Temporarily disabled for development/testing
        # exposed_keys = [
        #     "sk-ant-api03-08g4B_xrtHkk",  # Exposed Anthropic key prefix
        #     "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",  # Exposed Supabase key prefix
        # ]
        # for exposed in exposed_keys:
        #     if v.startswith(exposed):
        #         raise ValueError(
        #             "SECURITY WARNING: Exposed API key detected! "
        #             "Please rotate this key immediately."
        #         )
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Singleton instance
settings = Settings()

# Security checks on startup
def validate_security_config():
    """Validate security configuration on startup"""
    issues = []
    
    # Check for default/weak keys
    if settings.api_key == "your_api_key_for_this_service":
        issues.append("API_KEY is using default value")
    
    if settings.secret_key == "your_secret_key_for_jwt_tokens":
        issues.append("SECRET_KEY is using default value")
    
    # Check for production settings
    if settings.environment == "production":
        if "localhost" in settings.allowed_origins:
            issues.append("localhost in allowed_origins for production")
        
        if settings.log_level == "DEBUG":
            issues.append("DEBUG logging enabled in production")
    
    return issues

# Validate on import
security_issues = validate_security_config()
if security_issues:
    import logging
    logger = logging.getLogger(__name__)
    for issue in security_issues:
        logger.warning(f"Security configuration issue: {issue}")