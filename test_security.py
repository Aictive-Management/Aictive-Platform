"""
Security-focused tests for Aictive Platform
Following SuperClaude testing standards
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import json
from unittest.mock import Mock, patch

from main_secure import app
from auth import auth_service, Scopes
from config import settings

# Test client
client = TestClient(app)

# Test data
TEST_API_KEY = "test_api_key_123"
TEST_USER_ID = "test_user_123"

@pytest.fixture
def auth_headers():
    """Generate test authentication headers"""
    token = auth_service.create_access_token(
        subject=TEST_USER_ID,
        scopes=Scopes.all_scopes()
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def limited_auth_headers():
    """Generate limited scope authentication headers"""
    token = auth_service.create_access_token(
        subject=TEST_USER_ID,
        scopes=[Scopes.EMAIL_READ]
    )
    return {"Authorization": f"Bearer {token}"}

class TestSecurity:
    """Security-focused test cases"""
    
    def test_unauthenticated_access(self):
        """Test that endpoints require authentication"""
        response = client.post("/api/classify-email", json={
            "sender_email": "test@example.com",
            "subject": "Test",
            "body_text": "Test email"
        })
        assert response.status_code == 403  # Forbidden without auth
    
    def test_invalid_token(self):
        """Test invalid token rejection"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.post("/api/classify-email", 
            headers=headers,
            json={
                "sender_email": "test@example.com",
                "subject": "Test",
                "body_text": "Test email"
            }
        )
        assert response.status_code == 401
    
    def test_insufficient_scopes(self, limited_auth_headers):
        """Test scope enforcement"""
        # Try to access endpoint requiring EMAIL_CLASSIFY with only EMAIL_READ
        response = client.post("/api/classify-email",
            headers=limited_auth_headers,
            json={
                "sender_email": "test@example.com",
                "subject": "Test",
                "body_text": "Test email"
            }
        )
        assert response.status_code == 403
        assert "Not enough permissions" in response.json()["detail"]
    
    def test_rate_limiting(self, auth_headers):
        """Test rate limiting enforcement"""
        # Make requests up to the limit
        for _ in range(settings.rate_limit_per_minute):
            response = client.get("/api/stats", headers=auth_headers)
            assert response.status_code == 200
        
        # Next request should be rate limited
        response = client.get("/api/stats", headers=auth_headers)
        assert response.status_code == 429
        assert "Rate limit exceeded" in response.json()["detail"]
    
    def test_cors_configuration(self):
        """Test CORS is properly configured"""
        response = client.options("/api/classify-email",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        
        # Test unauthorized origin
        response = client.options("/api/classify-email",
            headers={
                "Origin": "http://malicious.com",
                "Access-Control-Request-Method": "POST"
            }
        )
        assert "access-control-allow-origin" not in response.headers or \
               response.headers["access-control-allow-origin"] != "http://malicious.com"
    
    def test_security_headers(self):
        """Test security headers are present"""
        response = client.get("/")
        assert response.headers["x-content-type-options"] == "nosniff"
        assert response.headers["x-frame-options"] == "DENY"
        assert response.headers["x-xss-protection"] == "1; mode=block"
        assert "strict-transport-security" in response.headers

class TestInputValidation:
    """Input validation test cases"""
    
    def test_email_validation(self, auth_headers):
        """Test email format validation"""
        # Invalid email format
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json={
                "sender_email": "not-an-email",
                "subject": "Test",
                "body_text": "Test"
            }
        )
        assert response.status_code == 422
        assert "Invalid email format" in str(response.json())
    
    def test_content_size_limits(self, auth_headers):
        """Test content size validation"""
        # Exceed body_text limit
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json={
                "sender_email": "test@example.com",
                "subject": "Test",
                "body_text": "x" * 60000  # Exceeds 50KB limit
            }
        )
        assert response.status_code == 422
    
    def test_sql_injection_sanitization(self, auth_headers):
        """Test SQL injection prevention"""
        malicious_content = "'; DROP TABLE emails; --"
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json={
                "sender_email": "test@example.com",
                "subject": "Test",
                "body_text": malicious_content
            }
        )
        # Should process safely without the SQL injection
        assert response.status_code == 200
        # Verify SQL commands were sanitized
        assert "DROP TABLE" not in response.json()["keywords"]
    
    def test_script_tag_removal(self, auth_headers):
        """Test XSS prevention"""
        malicious_html = "<script>alert('XSS')</script>Normal content"
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json={
                "sender_email": "test@example.com",
                "subject": "Test",
                "body_text": "Test",
                "body_html": malicious_html
            }
        )
        assert response.status_code == 200
        # Script tags should be removed in sanitization
    
    def test_field_regex_validation(self, auth_headers):
        """Test regex field validation"""
        # Invalid urgency value
        with patch('claude_service.ClaudeService.classify_email') as mock_classify:
            mock_classify.return_value = {
                "primary_category": "maintenance",
                "confidence": 0.9,
                "keywords": ["test"],
                "urgency": "invalid_urgency",  # Not matching regex
                "sentiment": "neutral"
            }
            
            response = client.post("/api/classify-email",
                headers=auth_headers,
                json={
                    "sender_email": "test@example.com",
                    "subject": "Test",
                    "body_text": "Test"
                }
            )
            assert response.status_code == 422

class TestWebhookSecurity:
    """Webhook security test cases"""
    
    def test_webhook_authentication_required(self):
        """Test webhooks require authentication"""
        response = client.post("/api/webhook/n8n", json={
            "event_type": "email_received",
            "payload": {}
        })
        assert response.status_code == 403
    
    def test_webhook_payload_validation(self, auth_headers):
        """Test webhook payload validation"""
        # Invalid payload
        response = client.post("/api/webhook/n8n",
            headers=auth_headers,
            json={
                "event_type": "email_received",
                "payload": {
                    "invalid": "data"
                }
            }
        )
        assert response.status_code == 400
        assert "Invalid payload" in response.json()["detail"]

class TestAPIKeySecurity:
    """API key management test cases"""
    
    def test_create_api_key_requires_admin(self, auth_headers, limited_auth_headers):
        """Test only admin can create API keys"""
        # Non-admin should fail
        response = client.post("/api/admin/create-api-key",
            headers=limited_auth_headers,
            json={
                "name": "Test Key",
                "scopes": ["email:read"]
            }
        )
        assert response.status_code == 403
        
        # Admin should succeed (mock admin scope)
        admin_token = auth_service.create_access_token(
            subject=TEST_USER_ID,
            scopes=[Scopes.ADMIN]
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.post("/api/admin/create-api-key",
            headers=admin_headers,
            json={
                "name": "Test Key",
                "scopes": ["email:read"]
            }
        )
        assert response.status_code == 200
        assert "api_key" in response.json()
        assert response.json()["api_key"].startswith("sk_live_")
    
    def test_api_key_format(self):
        """Test API key generation format"""
        from auth import auth_service
        
        # Test key hashing
        test_key = "sk_live_test123"
        hashed = auth_service.hash_api_key(test_key)
        assert hashed != test_key  # Should be hashed
        assert auth_service.verify_api_key(test_key, hashed)  # Should verify
        assert not auth_service.verify_api_key("wrong_key", hashed)  # Wrong key fails

class TestErrorHandling:
    """Error handling and information disclosure tests"""
    
    def test_no_stack_trace_exposure(self, auth_headers):
        """Test that stack traces are not exposed in production"""
        # Force an error
        with patch('claude_service.ClaudeService.classify_email') as mock_classify:
            mock_classify.side_effect = Exception("Internal error")
            
            response = client.post("/api/classify-email",
                headers=auth_headers,
                json={
                    "sender_email": "test@example.com",
                    "subject": "Test",
                    "body_text": "Test"
                }
            )
            
            assert response.status_code == 500
            error_detail = response.json()["error"]
            assert "Internal error" not in error_detail  # Don't expose internal errors
            assert "stack" not in response.json()  # No stack traces
            assert error_detail == "Email classification failed"  # Generic message

if __name__ == "__main__":
    pytest.main([__file__, "-v"])