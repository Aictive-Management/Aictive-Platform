"""
Comprehensive Audit Logging System for Aictive Platform
Provides structured logging, compliance reporting, and real-time security event detection.
"""
import asyncio
import json
import time
import uuid
import hashlib
import re
from typing import Dict, List, Optional, Any, Set, Union
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field, asdict
import logging
from pathlib import Path
import gzip
import aiofiles
from collections import defaultdict
import redis.asyncio as redis
from fastapi import Request, Response
from cryptography.fernet import Fernet
import structlog
from pythonjsonlogger import jsonlogger

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


class AuditEventType(Enum):
    """Types of audit events"""
    # Authentication events
    AUTH_LOGIN_SUCCESS = "auth.login.success"
    AUTH_LOGIN_FAILED = "auth.login.failed"
    AUTH_LOGOUT = "auth.logout"
    AUTH_TOKEN_CREATED = "auth.token.created"
    AUTH_TOKEN_REVOKED = "auth.token.revoked"
    
    # API events
    API_REQUEST = "api.request"
    API_RESPONSE = "api.response"
    API_ERROR = "api.error"
    API_RATE_LIMIT = "api.rate_limit"
    
    # Data events
    DATA_READ = "data.read"
    DATA_CREATE = "data.create"
    DATA_UPDATE = "data.update"
    DATA_DELETE = "data.delete"
    DATA_EXPORT = "data.export"
    
    # Security events
    SECURITY_VIOLATION = "security.violation"
    SECURITY_PERMISSION_DENIED = "security.permission_denied"
    SECURITY_SUSPICIOUS_ACTIVITY = "security.suspicious_activity"
    SECURITY_DATA_BREACH_ATTEMPT = "security.data_breach_attempt"
    
    # System events
    SYSTEM_CONFIG_CHANGE = "system.config_change"
    SYSTEM_ERROR = "system.error"
    SYSTEM_MAINTENANCE = "system.maintenance"
    
    # Compliance events
    COMPLIANCE_DATA_ACCESS = "compliance.data_access"
    COMPLIANCE_CONSENT_GRANTED = "compliance.consent_granted"
    COMPLIANCE_CONSENT_REVOKED = "compliance.consent_revoked"
    COMPLIANCE_DATA_RETENTION = "compliance.data_retention"


class ComplianceStandard(Enum):
    """Supported compliance standards"""
    GDPR = "gdpr"
    CCPA = "ccpa"
    HIPAA = "hipaa"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"


@dataclass
class AuditEvent:
    """Structured audit event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: AuditEventType = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    
    # Actor information
    actor_id: Optional[str] = None
    actor_type: str = "user"  # user, system, api_key
    actor_ip: Optional[str] = None
    actor_user_agent: Optional[str] = None
    
    # Target information
    target_type: Optional[str] = None  # user, property, tenant, etc.
    target_id: Optional[str] = None
    
    # Context
    tenant_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    
    # Event details
    action: str = ""
    result: str = "success"  # success, failure, error
    error_message: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Security context
    risk_score: float = 0.0
    security_context: Dict[str, Any] = field(default_factory=dict)
    
    # Compliance flags
    contains_pii: bool = False
    compliance_standards: List[ComplianceStandard] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with proper serialization"""
        data = asdict(self)
        data['event_type'] = self.event_type.value if self.event_type else None
        data['timestamp'] = self.timestamp.isoformat()
        data['compliance_standards'] = [s.value for s in self.compliance_standards]
        return data
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())


class DataMasker:
    """Handles sensitive data masking and PII protection"""
    
    # PII patterns
    PII_PATTERNS = {
        'email': re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        'phone': re.compile(r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'),
        'ssn': re.compile(r'\b(?!000|666|9\d{2})\d{3}[-\s]?(?!00)\d{2}[-\s]?(?!0000)\d{4}\b'),
        'credit_card': re.compile(r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\d{3})\d{11})\b'),
        'ip_address': re.compile(r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'),
    }
    
    # Fields to always mask
    SENSITIVE_FIELDS = {
        'password', 'secret', 'token', 'api_key', 'private_key',
        'access_token', 'refresh_token', 'client_secret', 'encryption_key'
    }
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.fernet = Fernet(self.encryption_key)
    
    def mask_pii(self, text: str) -> str:
        """Mask PII in text"""
        masked_text = text
        
        for pii_type, pattern in self.PII_PATTERNS.items():
            masked_text = pattern.sub(f'[MASKED_{pii_type.upper()}]', masked_text)
        
        return masked_text
    
    def mask_dict(self, data: Dict[str, Any], deep: bool = True) -> Dict[str, Any]:
        """Mask sensitive data in dictionary"""
        masked_data = {}
        
        for key, value in data.items():
            # Check if field is sensitive
            if any(sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS):
                masked_data[key] = '[MASKED]'
            elif isinstance(value, str):
                # Mask PII in string values
                masked_data[key] = self.mask_pii(value)
            elif isinstance(value, dict) and deep:
                # Recursively mask nested dictionaries
                masked_data[key] = self.mask_dict(value, deep=True)
            elif isinstance(value, list) and deep:
                # Handle lists
                masked_data[key] = [
                    self.mask_dict(item, deep=True) if isinstance(item, dict)
                    else self.mask_pii(str(item)) if isinstance(item, str)
                    else item
                    for item in value
                ]
            else:
                masked_data[key] = value
        
        return masked_data
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for storage"""
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        return self.fernet.decrypt(encrypted_data.encode()).decode()


class AuditLogger:
    """Main audit logging service"""
    
    def __init__(
        self, 
        redis_url: str = "redis://localhost:6379",
        log_dir: Path = Path("./audit_logs"),
        encryption_key: Optional[bytes] = None,
        retention_days: int = 90
    ):
        self.redis_url = redis_url
        self.redis_client = None
        self.log_dir = log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.masker = DataMasker(encryption_key)
        self.retention_days = retention_days
        
        # Correlation tracking
        self.correlation_store: Dict[str, str] = {}
        
        # Security event patterns
        self.security_patterns = self._init_security_patterns()
        
        # Real-time event handlers
        self.event_handlers: Dict[AuditEventType, List[callable]] = defaultdict(list)
        
        # Compliance configurations
        self.compliance_config = self._init_compliance_config()
        
    def _init_security_patterns(self) -> Dict[str, re.Pattern]:
        """Initialize patterns for security event detection"""
        return {
            'sql_injection': re.compile(
                r"(\bUNION\b.*\bSELECT\b|\bOR\b.*=.*|'.*\bOR\b.*'='|--|\||;)",
                re.IGNORECASE
            ),
            'xss_attempt': re.compile(
                r"(<script|javascript:|onerror=|onload=|<iframe|<embed)",
                re.IGNORECASE
            ),
            'path_traversal': re.compile(r"\.\./|\.\.\\"),
            'command_injection': re.compile(r"[;&|`$]|\$\(|&&|\|\|"),
            'excessive_requests': re.compile(r"rate_limit|too_many_requests"),
        }
    
    def _init_compliance_config(self) -> Dict[ComplianceStandard, Dict[str, Any]]:
        """Initialize compliance configurations"""
        return {
            ComplianceStandard.GDPR: {
                'pii_retention_days': 30,
                'require_consent': True,
                'right_to_erasure': True,
                'data_portability': True
            },
            ComplianceStandard.CCPA: {
                'pii_retention_days': 45,
                'require_opt_out': True,
                'data_sale_prohibition': True
            },
            ComplianceStandard.HIPAA: {
                'phi_encryption': True,
                'access_logging': True,
                'minimum_necessary': True
            },
            ComplianceStandard.SOC2: {
                'access_control': True,
                'encryption_required': True,
                'monitoring_required': True
            }
        }
    
    async def initialize(self):
        """Initialize Redis connection and start background tasks"""
        self.redis_client = await redis.from_url(
            self.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Start background tasks
        asyncio.create_task(self._retention_worker())
        asyncio.create_task(self._compression_worker())
        
        logger.info("Audit logger initialized")
    
    async def close(self):
        """Close connections and cleanup"""
        if self.redis_client:
            await self.redis_client.close()
    
    def set_correlation_id(self, request_id: str, correlation_id: str):
        """Set correlation ID for request tracking"""
        self.correlation_store[request_id] = correlation_id
    
    def get_correlation_id(self, request_id: str) -> Optional[str]:
        """Get correlation ID for request"""
        return self.correlation_store.get(request_id)
    
    async def log_event(self, event: AuditEvent) -> str:
        """Log an audit event"""
        # Detect security issues
        await self._detect_security_issues(event)
        
        # Mask sensitive data
        if event.metadata:
            event.metadata = self.masker.mask_dict(event.metadata)
        
        # Determine compliance standards
        if event.contains_pii:
            event.compliance_standards = [
                ComplianceStandard.GDPR,
                ComplianceStandard.CCPA
            ]
        
        # Log to multiple destinations
        await self._log_to_redis(event)
        await self._log_to_file(event)
        
        # Trigger real-time handlers
        await self._trigger_handlers(event)
        
        # Return event ID for tracking
        return event.event_id
    
    async def _detect_security_issues(self, event: AuditEvent):
        """Detect potential security issues in event"""
        # Check event metadata for security patterns
        event_str = json.dumps(event.metadata)
        
        for pattern_name, pattern in self.security_patterns.items():
            if pattern.search(event_str):
                event.security_context['detected_pattern'] = pattern_name
                event.risk_score = max(event.risk_score, 0.8)
                
                # Log security event
                security_event = AuditEvent(
                    event_type=AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
                    correlation_id=event.correlation_id,
                    actor_id=event.actor_id,
                    metadata={
                        'original_event_id': event.event_id,
                        'pattern': pattern_name,
                        'risk_score': event.risk_score
                    }
                )
                await self._log_to_redis(security_event)
    
    async def _log_to_redis(self, event: AuditEvent):
        """Log event to Redis for real-time processing"""
        # Store in Redis with TTL
        key = f"audit:event:{event.event_id}"
        await self.redis_client.setex(
            key,
            timedelta(days=7),  # Keep in Redis for 7 days
            event.to_json()
        )
        
        # Add to event type index
        index_key = f"audit:index:{event.event_type.value}:{event.timestamp.strftime('%Y%m%d')}"
        await self.redis_client.sadd(index_key, event.event_id)
        await self.redis_client.expire(index_key, timedelta(days=30))
        
        # Add to tenant index if applicable
        if event.tenant_id:
            tenant_key = f"audit:tenant:{event.tenant_id}:{event.timestamp.strftime('%Y%m%d')}"
            await self.redis_client.sadd(tenant_key, event.event_id)
            await self.redis_client.expire(tenant_key, timedelta(days=30))
        
        # Publish for real-time processing
        await self.redis_client.publish(
            f"audit:stream:{event.event_type.value}",
            event.to_json()
        )
    
    async def _log_to_file(self, event: AuditEvent):
        """Log event to file for long-term storage"""
        # Organize by date and event type
        date_str = event.timestamp.strftime('%Y-%m-%d')
        file_path = self.log_dir / date_str / f"{event.event_type.value}.jsonl"
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Append to file
        async with aiofiles.open(file_path, 'a') as f:
            await f.write(event.to_json() + '\n')
    
    async def _trigger_handlers(self, event: AuditEvent):
        """Trigger registered event handlers"""
        handlers = self.event_handlers.get(event.event_type, [])
        
        for handler in handlers:
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler: {e}", event_id=event.event_id)
    
    def register_handler(self, event_type: AuditEventType, handler: callable):
        """Register a real-time event handler"""
        self.event_handlers[event_type].append(handler)
    
    async def query_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: Optional[List[AuditEventType]] = None,
        tenant_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        limit: int = 1000
    ) -> List[AuditEvent]:
        """Query audit events"""
        events = []
        
        # Build query pattern
        if event_types:
            type_patterns = [et.value for et in event_types]
        else:
            type_patterns = ['*']
        
        # Query from Redis indices
        for date in self._date_range(start_time, end_time):
            date_str = date.strftime('%Y%m%d')
            
            for type_pattern in type_patterns:
                if tenant_id:
                    pattern = f"audit:tenant:{tenant_id}:{date_str}"
                else:
                    pattern = f"audit:index:{type_pattern}:{date_str}"
                
                # Get event IDs
                event_ids = await self.redis_client.smembers(pattern)
                
                # Retrieve events
                for event_id in event_ids:
                    event_data = await self.redis_client.get(f"audit:event:{event_id}")
                    if event_data:
                        event_dict = json.loads(event_data)
                        event = self._dict_to_event(event_dict)
                        
                        # Apply filters
                        if actor_id and event.actor_id != actor_id:
                            continue
                        
                        events.append(event)
                        
                        if len(events) >= limit:
                            return events
        
        return events
    
    def _date_range(self, start: datetime, end: datetime):
        """Generate date range"""
        current = start.date()
        end_date = end.date()
        
        while current <= end_date:
            yield current
            current += timedelta(days=1)
    
    def _dict_to_event(self, data: Dict[str, Any]) -> AuditEvent:
        """Convert dictionary to AuditEvent"""
        data['event_type'] = AuditEventType(data['event_type'])
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['compliance_standards'] = [
            ComplianceStandard(s) for s in data.get('compliance_standards', [])
        ]
        return AuditEvent(**data)
    
    async def generate_compliance_report(
        self,
        standard: ComplianceStandard,
        start_time: datetime,
        end_time: datetime,
        tenant_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate compliance report"""
        config = self.compliance_config[standard]
        
        # Query relevant events
        compliance_events = await self.query_events(
            start_time=start_time,
            end_time=end_time,
            tenant_id=tenant_id
        )
        
        # Filter by compliance standard
        relevant_events = [
            e for e in compliance_events 
            if standard in e.compliance_standards
        ]
        
        # Analyze events
        report = {
            'standard': standard.value,
            'period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat()
            },
            'tenant_id': tenant_id,
            'summary': {
                'total_events': len(relevant_events),
                'pii_access_events': sum(1 for e in relevant_events if e.contains_pii),
                'security_events': sum(
                    1 for e in relevant_events 
                    if e.event_type.value.startswith('security.')
                ),
                'data_operations': self._count_by_type(relevant_events)
            },
            'compliance_status': self._check_compliance_status(
                relevant_events, config
            ),
            'recommendations': self._generate_recommendations(
                relevant_events, standard
            )
        }
        
        return report
    
    def _count_by_type(self, events: List[AuditEvent]) -> Dict[str, int]:
        """Count events by type"""
        counts = defaultdict(int)
        for event in events:
            counts[event.event_type.value] += 1
        return dict(counts)
    
    def _check_compliance_status(
        self, 
        events: List[AuditEvent], 
        config: Dict[str, Any]
    ) -> Dict[str, bool]:
        """Check compliance status based on events"""
        status = {}
        
        # Check various compliance requirements
        if 'require_consent' in config:
            consent_events = [
                e for e in events 
                if e.event_type == AuditEventType.COMPLIANCE_CONSENT_GRANTED
            ]
            status['consent_tracking'] = len(consent_events) > 0
        
        if 'access_logging' in config:
            access_events = [
                e for e in events 
                if e.event_type == AuditEventType.DATA_READ
            ]
            status['access_logging'] = len(access_events) > 0
        
        return status
    
    def _generate_recommendations(
        self, 
        events: List[AuditEvent], 
        standard: ComplianceStandard
    ) -> List[str]:
        """Generate compliance recommendations"""
        recommendations = []
        
        # Analyze patterns
        high_risk_events = [e for e in events if e.risk_score > 0.7]
        if high_risk_events:
            recommendations.append(
                f"Review {len(high_risk_events)} high-risk events detected"
            )
        
        # Check for missing compliance events
        if standard == ComplianceStandard.GDPR:
            consent_events = [
                e for e in events 
                if e.event_type in [
                    AuditEventType.COMPLIANCE_CONSENT_GRANTED,
                    AuditEventType.COMPLIANCE_CONSENT_REVOKED
                ]
            ]
            if not consent_events:
                recommendations.append(
                    "Implement consent tracking for GDPR compliance"
                )
        
        return recommendations
    
    async def _retention_worker(self):
        """Background worker for data retention"""
        while True:
            try:
                # Clean up old logs
                cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
                
                # Remove old files
                for date_dir in self.log_dir.iterdir():
                    if date_dir.is_dir():
                        try:
                            dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                            if dir_date < cutoff_date:
                                # Archive before deletion
                                await self._archive_logs(date_dir)
                                # Then remove
                                import shutil
                                shutil.rmtree(date_dir)
                                logger.info(f"Removed old audit logs: {date_dir}")
                        except ValueError:
                            pass
                
                # Sleep for 24 hours
                await asyncio.sleep(86400)
                
            except Exception as e:
                logger.error(f"Error in retention worker: {e}")
                await asyncio.sleep(3600)  # Retry in 1 hour
    
    async def _compression_worker(self):
        """Background worker for log compression"""
        while True:
            try:
                # Compress logs older than 1 day
                cutoff = datetime.utcnow() - timedelta(days=1)
                
                for date_dir in self.log_dir.iterdir():
                    if date_dir.is_dir():
                        try:
                            dir_date = datetime.strptime(date_dir.name, '%Y-%m-%d')
                            if dir_date < cutoff:
                                await self._compress_logs(date_dir)
                        except ValueError:
                            pass
                
                # Sleep for 6 hours
                await asyncio.sleep(21600)
                
            except Exception as e:
                logger.error(f"Error in compression worker: {e}")
                await asyncio.sleep(3600)
    
    async def _compress_logs(self, date_dir: Path):
        """Compress log files in directory"""
        for log_file in date_dir.glob("*.jsonl"):
            compressed_file = log_file.with_suffix('.jsonl.gz')
            
            if not compressed_file.exists():
                async with aiofiles.open(log_file, 'rb') as f_in:
                    content = await f_in.read()
                
                async with aiofiles.open(compressed_file, 'wb') as f_out:
                    await f_out.write(gzip.compress(content))
                
                # Remove original file
                log_file.unlink()
                logger.info(f"Compressed audit log: {log_file}")
    
    async def _archive_logs(self, date_dir: Path):
        """Archive logs before deletion"""
        # This would typically upload to S3 or other long-term storage
        # For now, just log the action
        logger.info(f"Archiving audit logs: {date_dir}")


# Middleware for FastAPI
class AuditLoggingMiddleware:
    """FastAPI middleware for audit logging"""
    
    def __init__(self, app, audit_logger: AuditLogger):
        self.app = app
        self.audit_logger = audit_logger
    
    async def __call__(self, request: Request, call_next):
        # Generate correlation ID if not present
        correlation_id = request.headers.get(
            'X-Correlation-ID',
            str(uuid.uuid4())
        )
        
        # Extract request details
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        request.state.correlation_id = correlation_id
        
        # Set correlation ID
        self.audit_logger.set_correlation_id(request_id, correlation_id)
        
        # Create request event
        request_event = AuditEvent(
            event_type=AuditEventType.API_REQUEST,
            correlation_id=correlation_id,
            request_id=request_id,
            actor_ip=request.client.host if request.client else None,
            actor_user_agent=request.headers.get('User-Agent'),
            action=f"{request.method} {request.url.path}",
            metadata={
                'method': request.method,
                'path': request.url.path,
                'query_params': dict(request.query_params),
                'headers': dict(request.headers)
            }
        )
        
        # Extract actor info if available
        if hasattr(request.state, 'user'):
            request_event.actor_id = request.state.user.id
            request_event.tenant_id = request.state.user.tenant_id
        
        # Log request
        await self.audit_logger.log_event(request_event)
        
        # Process request
        start_time = time.time()
        response = None
        error = None
        
        try:
            response = await call_next(request)
            return response
            
        except Exception as e:
            error = e
            raise
            
        finally:
            # Log response
            duration = time.time() - start_time
            
            response_event = AuditEvent(
                event_type=AuditEventType.API_RESPONSE if not error else AuditEventType.API_ERROR,
                correlation_id=correlation_id,
                request_id=request_id,
                actor_id=request_event.actor_id,
                tenant_id=request_event.tenant_id,
                action=f"{request.method} {request.url.path}",
                result="success" if not error else "error",
                error_message=str(error) if error else None,
                metadata={
                    'status_code': response.status_code if response else 500,
                    'duration_ms': round(duration * 1000, 2),
                    'method': request.method,
                    'path': request.url.path
                }
            )
            
            await self.audit_logger.log_event(response_event)


# Example usage
async def setup_audit_logging(app, redis_url: str = "redis://localhost:6379"):
    """Setup audit logging for FastAPI app"""
    # Initialize audit logger
    audit_logger = AuditLogger(redis_url=redis_url)
    await audit_logger.initialize()
    
    # Add middleware
    app.add_middleware(AuditLoggingMiddleware, audit_logger=audit_logger)
    
    # Register security event handler
    async def handle_security_event(event: AuditEvent):
        if event.risk_score > 0.8:
            logger.warning(
                "High risk security event detected",
                event_id=event.event_id,
                risk_score=event.risk_score
            )
    
    audit_logger.register_handler(
        AuditEventType.SECURITY_SUSPICIOUS_ACTIVITY,
        handle_security_event
    )
    
    # Add cleanup on shutdown
    @app.on_event("shutdown")
    async def shutdown():
        await audit_logger.close()
    
    return audit_logger