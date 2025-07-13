"""
Security Headers Middleware for Aictive Platform
Implements OWASP security headers and API security configurations.
"""
import re
import json
import hashlib
import base64
from typing import Dict, List, Optional, Set, Union, Callable
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from urllib.parse import urlparse
import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import asyncio

logger = structlog.get_logger()


class SecurityHeaderLevel(Enum):
    """Security header enforcement levels"""
    STRICT = "strict"
    MODERATE = "moderate"
    RELAXED = "relaxed"
    CUSTOM = "custom"


class CSPDirective(Enum):
    """Content Security Policy directives"""
    DEFAULT_SRC = "default-src"
    SCRIPT_SRC = "script-src"
    STYLE_SRC = "style-src"
    IMG_SRC = "img-src"
    FONT_SRC = "font-src"
    CONNECT_SRC = "connect-src"
    MEDIA_SRC = "media-src"
    OBJECT_SRC = "object-src"
    FRAME_SRC = "frame-src"
    FRAME_ANCESTORS = "frame-ancestors"
    BASE_URI = "base-uri"
    FORM_ACTION = "form-action"
    MANIFEST_SRC = "manifest-src"
    WORKER_SRC = "worker-src"
    NAVIGATE_TO = "navigate-to"


@dataclass
class SecurityHeaderConfig:
    """Configuration for security headers"""
    # HSTS (HTTP Strict Transport Security)
    hsts_enabled: bool = True
    hsts_max_age: int = 31536000  # 1 year
    hsts_include_subdomains: bool = True
    hsts_preload: bool = True
    
    # X-Frame-Options
    x_frame_options: str = "DENY"  # DENY, SAMEORIGIN, ALLOW-FROM uri
    
    # X-Content-Type-Options
    x_content_type_options: bool = True  # nosniff
    
    # X-XSS-Protection (deprecated but still used by some browsers)
    x_xss_protection: bool = True
    x_xss_protection_mode: str = "1; mode=block"
    
    # Referrer-Policy
    referrer_policy: str = "strict-origin-when-cross-origin"
    
    # Permissions-Policy (formerly Feature-Policy)
    permissions_policy: Dict[str, List[str]] = field(default_factory=lambda: {
        "accelerometer": [],
        "camera": [],
        "geolocation": [],
        "gyroscope": [],
        "magnetometer": [],
        "microphone": [],
        "payment": [],
        "usb": []
    })
    
    # Content-Security-Policy
    csp_enabled: bool = True
    csp_report_only: bool = False
    csp_report_uri: Optional[str] = None
    csp_directives: Dict[CSPDirective, List[str]] = field(default_factory=dict)
    
    # CORS settings
    cors_enabled: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    cors_methods: List[str] = field(default_factory=lambda: ["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    cors_headers: List[str] = field(default_factory=lambda: ["*"])
    cors_credentials: bool = False
    cors_max_age: int = 86400  # 24 hours
    
    # Additional security headers
    expect_ct_enabled: bool = True
    expect_ct_max_age: int = 86400
    expect_ct_enforce: bool = False
    expect_ct_report_uri: Optional[str] = None
    
    # Custom headers
    custom_headers: Dict[str, str] = field(default_factory=dict)


class SecurityHeaderPresets:
    """Predefined security header configurations"""
    
    @staticmethod
    def strict() -> SecurityHeaderConfig:
        """Strict security configuration"""
        return SecurityHeaderConfig(
            hsts_enabled=True,
            hsts_max_age=63072000,  # 2 years
            hsts_include_subdomains=True,
            hsts_preload=True,
            x_frame_options="DENY",
            x_content_type_options=True,
            x_xss_protection=True,
            referrer_policy="no-referrer",
            permissions_policy={
                "accelerometer": [],
                "camera": [],
                "geolocation": [],
                "gyroscope": [],
                "magnetometer": [],
                "microphone": [],
                "payment": [],
                "usb": [],
                "interest-cohort": []  # FLoC opt-out
            },
            csp_enabled=True,
            csp_directives={
                CSPDirective.DEFAULT_SRC: ["'self'"],
                CSPDirective.SCRIPT_SRC: ["'self'", "'strict-dynamic'"],
                CSPDirective.STYLE_SRC: ["'self'", "'unsafe-inline'"],
                CSPDirective.IMG_SRC: ["'self'", "data:", "https:"],
                CSPDirective.FONT_SRC: ["'self'"],
                CSPDirective.CONNECT_SRC: ["'self'"],
                CSPDirective.FRAME_ANCESTORS: ["'none'"],
                CSPDirective.BASE_URI: ["'self'"],
                CSPDirective.FORM_ACTION: ["'self'"]
            },
            cors_enabled=True,
            cors_origins=["https://app.aictive.com"],
            cors_credentials=True
        )
    
    @staticmethod
    def moderate() -> SecurityHeaderConfig:
        """Moderate security configuration"""
        return SecurityHeaderConfig(
            hsts_enabled=True,
            hsts_max_age=31536000,  # 1 year
            x_frame_options="SAMEORIGIN",
            referrer_policy="strict-origin-when-cross-origin",
            csp_enabled=True,
            csp_directives={
                CSPDirective.DEFAULT_SRC: ["'self'"],
                CSPDirective.SCRIPT_SRC: ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
                CSPDirective.STYLE_SRC: ["'self'", "'unsafe-inline'"],
                CSPDirective.IMG_SRC: ["'self'", "data:", "https:"],
                CSPDirective.CONNECT_SRC: ["'self'", "https:"]
            }
        )
    
    @staticmethod
    def api_only() -> SecurityHeaderConfig:
        """Configuration for API-only services"""
        return SecurityHeaderConfig(
            hsts_enabled=True,
            x_frame_options="DENY",
            x_content_type_options=True,
            csp_enabled=False,  # CSP not needed for pure APIs
            cors_enabled=True,
            cors_origins=["*"],
            cors_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
            custom_headers={
                "X-API-Version": "1.0",
                "X-RateLimit-Limit": "1000",
                "X-RateLimit-Remaining": "1000",
                "X-RateLimit-Reset": "0"
            }
        )


class ContentSecurityPolicy:
    """Content Security Policy builder and manager"""
    
    def __init__(self, config: SecurityHeaderConfig):
        self.config = config
        self.nonce_generator = self._generate_nonce
        self._dynamic_sources: Dict[CSPDirective, Set[str]] = {}
    
    def _generate_nonce(self) -> str:
        """Generate a cryptographic nonce for inline scripts/styles"""
        random_bytes = base64.b64encode(hashlib.sha256(
            str(datetime.utcnow().timestamp()).encode()
        ).digest()).decode()
        return random_bytes[:16]
    
    def add_source(self, directive: CSPDirective, source: str):
        """Add a source to a CSP directive"""
        if directive not in self._dynamic_sources:
            self._dynamic_sources[directive] = set()
        self._dynamic_sources[directive].add(source)
    
    def remove_source(self, directive: CSPDirective, source: str):
        """Remove a source from a CSP directive"""
        if directive in self._dynamic_sources:
            self._dynamic_sources[directive].discard(source)
    
    def build_policy(self, request: Optional[Request] = None) -> str:
        """Build the CSP header value"""
        policy_parts = []
        
        # Combine configured and dynamic sources
        all_directives = {}
        
        # Start with configured directives
        for directive, sources in self.config.csp_directives.items():
            all_directives[directive] = set(sources)
        
        # Add dynamic sources
        for directive, sources in self._dynamic_sources.items():
            if directive not in all_directives:
                all_directives[directive] = set()
            all_directives[directive].update(sources)
        
        # Generate nonce if needed
        nonce = None
        if request and hasattr(request.state, 'csp_nonce'):
            nonce = request.state.csp_nonce
        elif CSPDirective.SCRIPT_SRC in all_directives:
            # Check if we need a nonce
            script_sources = all_directives[CSPDirective.SCRIPT_SRC]
            if "'strict-dynamic'" in script_sources or "'nonce-'" in str(script_sources):
                nonce = self.nonce_generator()
        
        # Build policy string
        for directive, sources in all_directives.items():
            directive_sources = list(sources)
            
            # Add nonce to script-src if generated
            if nonce and directive == CSPDirective.SCRIPT_SRC:
                directive_sources.append(f"'nonce-{nonce}'")
            
            policy_parts.append(f"{directive.value} {' '.join(directive_sources)}")
        
        # Add report-uri if configured
        if self.config.csp_report_uri:
            policy_parts.append(f"report-uri {self.config.csp_report_uri}")
        
        return "; ".join(policy_parts)
    
    def validate_policy(self) -> List[str]:
        """Validate CSP configuration"""
        warnings = []
        
        # Check for unsafe directives
        for directive, sources in self.config.csp_directives.items():
            unsafe_sources = [s for s in sources if 'unsafe' in s]
            if unsafe_sources:
                warnings.append(
                    f"CSP {directive.value} contains unsafe sources: {unsafe_sources}"
                )
        
        # Check for wildcard sources
        for directive, sources in self.config.csp_directives.items():
            if '*' in sources:
                warnings.append(
                    f"CSP {directive.value} contains wildcard source"
                )
        
        # Check for missing important directives
        important_directives = [
            CSPDirective.DEFAULT_SRC,
            CSPDirective.SCRIPT_SRC,
            CSPDirective.FRAME_ANCESTORS
        ]
        
        for directive in important_directives:
            if directive not in self.config.csp_directives:
                warnings.append(f"Missing important CSP directive: {directive.value}")
        
        return warnings


class SecurityHeadersMiddleware:
    """Main security headers middleware"""
    
    def __init__(
        self,
        app,
        config: Optional[SecurityHeaderConfig] = None,
        level: SecurityHeaderLevel = SecurityHeaderLevel.MODERATE
    ):
        self.app = app
        
        # Set configuration based on level
        if config:
            self.config = config
        elif level == SecurityHeaderLevel.STRICT:
            self.config = SecurityHeaderPresets.strict()
        elif level == SecurityHeaderLevel.MODERATE:
            self.config = SecurityHeaderPresets.moderate()
        elif level == SecurityHeaderLevel.RELAXED:
            self.config = SecurityHeaderPresets.api_only()
        else:
            self.config = SecurityHeaderConfig()
        
        self.csp = ContentSecurityPolicy(self.config)
        self._header_validators = self._init_validators()
        
        # Validate configuration on startup
        self._validate_configuration()
    
    def _init_validators(self) -> Dict[str, Callable]:
        """Initialize header validators"""
        return {
            'Strict-Transport-Security': self._validate_hsts,
            'X-Frame-Options': self._validate_x_frame_options,
            'Content-Security-Policy': self._validate_csp,
            'Referrer-Policy': self._validate_referrer_policy
        }
    
    def _validate_configuration(self):
        """Validate security configuration on startup"""
        # Validate CSP
        csp_warnings = self.csp.validate_policy()
        for warning in csp_warnings:
            logger.warning(f"CSP validation warning: {warning}")
        
        # Validate CORS origins
        if self.config.cors_enabled and "*" in self.config.cors_origins:
            logger.warning(
                "CORS configured with wildcard origin - "
                "consider restricting to specific origins in production"
            )
        
        # Check for conflicting settings
        if self.config.cors_credentials and "*" in self.config.cors_origins:
            logger.error(
                "CORS credentials enabled with wildcard origin - "
                "this is a security risk!"
            )
    
    async def __call__(self, request: Request, call_next):
        """Process request and add security headers"""
        # Handle preflight CORS requests
        if request.method == "OPTIONS" and self.config.cors_enabled:
            return self._handle_preflight(request)
        
        # Generate CSP nonce if needed
        if self.config.csp_enabled:
            request.state.csp_nonce = self.csp.nonce_generator()
        
        # Process request
        response = await call_next(request)
        
        # Add security headers
        self._add_security_headers(request, response)
        
        # Add CORS headers if enabled
        if self.config.cors_enabled:
            self._add_cors_headers(request, response)
        
        return response
    
    def _add_security_headers(self, request: Request, response: Response):
        """Add security headers to response"""
        # HSTS
        if self.config.hsts_enabled:
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # X-Frame-Options
        response.headers["X-Frame-Options"] = self.config.x_frame_options
        
        # X-Content-Type-Options
        if self.config.x_content_type_options:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection
        if self.config.x_xss_protection:
            response.headers["X-XSS-Protection"] = self.config.x_xss_protection_mode
        
        # Referrer-Policy
        response.headers["Referrer-Policy"] = self.config.referrer_policy
        
        # Permissions-Policy
        if self.config.permissions_policy:
            policy_parts = []
            for feature, allowlist in self.config.permissions_policy.items():
                if not allowlist:
                    policy_parts.append(f"{feature}=()")
                else:
                    sources = ' '.join(f'"{s}"' if s != "self" else s for s in allowlist)
                    policy_parts.append(f"{feature}=({sources})")
            response.headers["Permissions-Policy"] = ", ".join(policy_parts)
        
        # Content-Security-Policy
        if self.config.csp_enabled:
            csp_header = "Content-Security-Policy-Report-Only" if self.config.csp_report_only else "Content-Security-Policy"
            response.headers[csp_header] = self.csp.build_policy(request)
        
        # Expect-CT
        if self.config.expect_ct_enabled:
            expect_ct_value = f"max-age={self.config.expect_ct_max_age}"
            if self.config.expect_ct_enforce:
                expect_ct_value += ", enforce"
            if self.config.expect_ct_report_uri:
                expect_ct_value += f', report-uri="{self.config.expect_ct_report_uri}"'
            response.headers["Expect-CT"] = expect_ct_value
        
        # Custom headers
        for header, value in self.config.custom_headers.items():
            response.headers[header] = value
        
        # Security headers for API responses
        if response.headers.get("Content-Type", "").startswith("application/json"):
            response.headers["X-Content-Type-Options"] = "nosniff"
            response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
            response.headers["Pragma"] = "no-cache"
    
    def _add_cors_headers(self, request: Request, response: Response):
        """Add CORS headers to response"""
        origin = request.headers.get("Origin")
        
        # Check if origin is allowed
        if origin:
            if "*" in self.config.cors_origins:
                response.headers["Access-Control-Allow-Origin"] = "*"
            elif origin in self.config.cors_origins:
                response.headers["Access-Control-Allow-Origin"] = origin
            elif any(self._match_origin_pattern(origin, pattern) for pattern in self.config.cors_origins):
                response.headers["Access-Control-Allow-Origin"] = origin
        
        # Add other CORS headers
        if "Access-Control-Allow-Origin" in response.headers:
            response.headers["Access-Control-Allow-Methods"] = ", ".join(self.config.cors_methods)
            response.headers["Access-Control-Allow-Headers"] = ", ".join(self.config.cors_headers)
            response.headers["Access-Control-Max-Age"] = str(self.config.cors_max_age)
            
            if self.config.cors_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # Expose custom headers
            exposed_headers = ["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"]
            response.headers["Access-Control-Expose-Headers"] = ", ".join(exposed_headers)
    
    def _handle_preflight(self, request: Request) -> Response:
        """Handle CORS preflight requests"""
        response = Response(status_code=204)
        self._add_cors_headers(request, response)
        return response
    
    def _match_origin_pattern(self, origin: str, pattern: str) -> bool:
        """Match origin against pattern (supports wildcards)"""
        if pattern.startswith("*."):
            # Subdomain wildcard
            domain = pattern[2:]
            parsed_origin = urlparse(origin)
            return parsed_origin.hostname.endswith(domain)
        elif pattern.startswith("http://localhost:"):
            # Local development
            return origin.startswith("http://localhost:")
        else:
            return origin == pattern
    
    # Validators
    def _validate_hsts(self, value: str) -> bool:
        """Validate HSTS header"""
        pattern = re.compile(r'^max-age=\d+(?:;\s*(?:includeSubDomains|preload))*$')
        return bool(pattern.match(value))
    
    def _validate_x_frame_options(self, value: str) -> bool:
        """Validate X-Frame-Options header"""
        valid_values = ["DENY", "SAMEORIGIN"]
        if value in valid_values:
            return True
        if value.startswith("ALLOW-FROM "):
            return True
        return False
    
    def _validate_csp(self, value: str) -> bool:
        """Validate CSP header"""
        # Basic validation - check for proper directive format
        directives = value.split(";")
        for directive in directives:
            parts = directive.strip().split()
            if not parts:
                continue
            if not parts[0].endswith("-src") and parts[0] not in [
                "default-src", "base-uri", "form-action", 
                "frame-ancestors", "report-uri", "report-to"
            ]:
                return False
        return True
    
    def _validate_referrer_policy(self, value: str) -> bool:
        """Validate Referrer-Policy header"""
        valid_values = [
            "no-referrer", "no-referrer-when-downgrade", "origin",
            "origin-when-cross-origin", "same-origin", "strict-origin",
            "strict-origin-when-cross-origin", "unsafe-url"
        ]
        return value in valid_values
    
    def update_config(self, config: SecurityHeaderConfig):
        """Update security header configuration"""
        self.config = config
        self.csp = ContentSecurityPolicy(config)
        self._validate_configuration()
        logger.info("Security header configuration updated")
    
    def get_config(self) -> SecurityHeaderConfig:
        """Get current security header configuration"""
        return self.config


class SecurityHeaderTester:
    """Test and validate security headers"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.test_results = []
    
    async def run_tests(self) -> Dict[str, Any]:
        """Run security header tests"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            # Test various endpoints
            endpoints = ["/", "/api/v1/health", "/api/v1/test"]
            
            for endpoint in endpoints:
                try:
                    response = await client.get(f"{self.base_url}{endpoint}")
                    result = self._analyze_headers(endpoint, response.headers)
                    self.test_results.append(result)
                except Exception as e:
                    self.test_results.append({
                        'endpoint': endpoint,
                        'error': str(e),
                        'score': 0
                    })
        
        return self._generate_report()
    
    def _analyze_headers(self, endpoint: str, headers: Dict[str, str]) -> Dict[str, Any]:
        """Analyze security headers"""
        result = {
            'endpoint': endpoint,
            'headers_present': {},
            'headers_missing': [],
            'warnings': [],
            'score': 0
        }
        
        # Required security headers
        required_headers = [
            'Strict-Transport-Security',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Referrer-Policy',
            'Content-Security-Policy'
        ]
        
        # Check each header
        max_score = len(required_headers) * 20
        
        for header in required_headers:
            if header in headers:
                result['headers_present'][header] = headers[header]
                result['score'] += 20
                
                # Additional validation
                if header == 'Strict-Transport-Security':
                    if 'max-age=0' in headers[header]:
                        result['warnings'].append("HSTS max-age is 0")
                        result['score'] -= 10
                    elif 'preload' not in headers[header]:
                        result['warnings'].append("HSTS preload not enabled")
                
                elif header == 'Content-Security-Policy':
                    if 'unsafe-inline' in headers[header]:
                        result['warnings'].append("CSP contains unsafe-inline")
                        result['score'] -= 5
                    if 'unsafe-eval' in headers[header]:
                        result['warnings'].append("CSP contains unsafe-eval")
                        result['score'] -= 5
            else:
                result['headers_missing'].append(header)
        
        # Calculate percentage score
        result['score_percentage'] = (result['score'] / max_score) * 100
        
        return result
    
    def _generate_report(self) -> Dict[str, Any]:
        """Generate security header test report"""
        total_score = sum(r.get('score', 0) for r in self.test_results)
        max_possible_score = len(self.test_results) * 100
        
        return {
            'summary': {
                'total_endpoints_tested': len(self.test_results),
                'average_score': total_score / len(self.test_results) if self.test_results else 0,
                'overall_grade': self._calculate_grade(total_score / max_possible_score * 100 if max_possible_score > 0 else 0)
            },
            'detailed_results': self.test_results,
            'recommendations': self._generate_recommendations()
        }
    
    def _calculate_grade(self, percentage: float) -> str:
        """Calculate security grade"""
        if percentage >= 90:
            return 'A'
        elif percentage >= 80:
            return 'B'
        elif percentage >= 70:
            return 'C'
        elif percentage >= 60:
            return 'D'
        else:
            return 'F'
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Analyze common issues
        missing_headers = set()
        for result in self.test_results:
            missing_headers.update(result.get('headers_missing', []))
        
        if missing_headers:
            recommendations.append(
                f"Add missing security headers: {', '.join(missing_headers)}"
            )
        
        # Check for warnings
        all_warnings = []
        for result in self.test_results:
            all_warnings.extend(result.get('warnings', []))
        
        if 'unsafe-inline' in str(all_warnings):
            recommendations.append(
                "Remove 'unsafe-inline' from CSP and use nonces or hashes instead"
            )
        
        if 'HSTS preload not enabled' in all_warnings:
            recommendations.append(
                "Enable HSTS preload for maximum security"
            )
        
        return recommendations


# Example usage
def setup_security_headers(app, level: SecurityHeaderLevel = SecurityHeaderLevel.MODERATE):
    """Setup security headers middleware"""
    
    # Create custom configuration if needed
    if level == SecurityHeaderLevel.CUSTOM:
        config = SecurityHeaderConfig(
            csp_directives={
                CSPDirective.DEFAULT_SRC: ["'self'"],
                CSPDirective.SCRIPT_SRC: ["'self'", "'nonce-'", "https://cdn.jsdelivr.net"],
                CSPDirective.STYLE_SRC: ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"],
                CSPDirective.FONT_SRC: ["'self'", "https://fonts.gstatic.com"],
                CSPDirective.IMG_SRC: ["'self'", "data:", "https:"],
                CSPDirective.CONNECT_SRC: ["'self'", "https://api.aictive.com"]
            },
            cors_origins=["https://app.aictive.com", "http://localhost:3000"],
            cors_credentials=True
        )
    else:
        config = None
    
    # Add middleware
    app.add_middleware(
        SecurityHeadersMiddleware,
        config=config,
        level=level
    )
    
    logger.info(f"Security headers middleware configured with {level.value} level")