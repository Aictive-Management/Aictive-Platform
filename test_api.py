"""
API functionality tests for Aictive Platform
Following SuperClaude testing standards
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock
import json

from main_secure import app
from auth import auth_service, Scopes

# Test client
client = TestClient(app)

# Test fixtures
@pytest.fixture
def auth_headers():
    """Generate full access authentication headers"""
    token = auth_service.create_access_token(
        subject="test_user",
        scopes=Scopes.all_scopes()
    )
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def mock_claude_service():
    """Mock Claude service responses"""
    with patch('main_secure.claude_service') as mock:
        # Setup default responses
        mock.classify_email = AsyncMock(return_value={
            "primary_category": "maintenance",
            "confidence": 0.95,
            "secondary_category": None,
            "keywords": ["leak", "plumbing", "urgent"],
            "urgency": "high",
            "sentiment": "negative"
        })
        
        mock.analyze_maintenance_request = AsyncMock(return_value={
            "issue_type": "plumbing",
            "specific_issue": "Water leak in bathroom",
            "location": {
                "unit_area": "bathroom",
                "details": "Under sink"
            },
            "urgency_indicators": {
                "has_water_damage": True,
                "no_utilities": False,
                "safety_hazard": False,
                "multiple_units_affected": False
            },
            "urgency_level": "high",
            "tenant_impact": "inconvenient",
            "estimated_repair_complexity": "moderate",
            "tenant_availability": "Weekdays after 5pm",
            "special_instructions": None,
            "detected_appliances": ["sink"],
            "requires_parts": True,
            "confidence_score": 0.9
        })
        
        mock.generate_response = AsyncMock(return_value=
            "Thank you for reporting the water leak. A maintenance technician will be scheduled."
        )
        
        mock.extract_entities = AsyncMock(return_value={
            "names": ["John Doe"],
            "addresses": ["Apt 101"],
            "phone_numbers": ["555-1234"],
            "dates_times": ["tomorrow at 3pm"],
            "amounts": ["$500"]
        })
        
        mock.check_compliance = AsyncMock(return_value={
            "is_compliant": True,
            "issues": [],
            "suggestions": [],
            "risk_level": "low"
        })
        
        yield mock

@pytest.fixture
def mock_supabase():
    """Mock Supabase client"""
    with patch('main_secure.supabase') as mock:
        # Mock table operations
        mock_table = Mock()
        mock_table.insert.return_value.execute.return_value = Mock(data=[{"id": "123"}])
        mock_table.select.return_value.execute.return_value = Mock(data=[
            {"primary_category": "maintenance"},
            {"primary_category": "maintenance"},
            {"primary_category": "payment"}
        ])
        mock.table.return_value = mock_table
        yield mock

class TestHealthEndpoints:
    """Test health check endpoints"""
    
    def test_root_endpoint(self):
        """Test root health check"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "active"
        assert data["service"] == "Aictive Platform API"
        assert "timestamp" in data
        assert "environment" in data
    
    def test_health_endpoint(self):
        """Test detailed health check"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "degraded"]
        assert "services" in data
        assert all(service in data["services"] for service in ["api", "supabase", "claude", "slack"])

class TestEmailClassification:
    """Test email classification endpoint"""
    
    def test_classify_email_success(self, auth_headers, mock_claude_service, mock_supabase):
        """Test successful email classification"""
        email_data = {
            "sender_email": "tenant@example.com",
            "subject": "Water leak in bathroom",
            "body_text": "There's a water leak under the sink in my bathroom. Please help!"
        }
        
        response = client.post("/api/classify-email", 
            headers=auth_headers,
            json=email_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["primary_category"] == "maintenance"
        assert data["confidence"] == 0.95
        assert data["urgency"] == "high"
        assert "email_id" in data
        assert "processing_time" in data
        
        # Verify Claude service was called
        mock_claude_service.classify_email.assert_called_once()
    
    def test_classify_email_with_attachments(self, auth_headers, mock_claude_service):
        """Test email classification with attachments"""
        email_data = {
            "sender_email": "tenant@example.com",
            "subject": "Maintenance request",
            "body_text": "See attached photos",
            "attachments": [
                {"filename": "leak.jpg", "size": 1024},
                {"filename": "damage.pdf", "size": 2048}
            ]
        }
        
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json=email_data
        )
        
        assert response.status_code == 200
        assert len(email_data["attachments"]) == 2
    
    def test_classify_email_validation_errors(self, auth_headers):
        """Test email validation errors"""
        # Missing required fields
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json={"sender_email": "test@example.com"}
        )
        assert response.status_code == 422
        
        # Invalid email format
        response = client.post("/api/classify-email",
            headers=auth_headers,
            json={
                "sender_email": "invalid-email",
                "subject": "Test",
                "body_text": "Test"
            }
        )
        assert response.status_code == 422

class TestMaintenanceAnalysis:
    """Test maintenance analysis endpoint"""
    
    def test_analyze_maintenance_success(self, auth_headers, mock_claude_service):
        """Test successful maintenance analysis"""
        response = client.post("/api/analyze-maintenance",
            headers=auth_headers,
            json={
                "email_content": "Water is leaking from under the bathroom sink. It's getting worse."
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["issue_type"] == "plumbing"
        assert data["urgency_level"] == "high"
        assert data["location"]["unit_area"] == "bathroom"
        assert data["urgency_indicators"]["has_water_damage"] is True
        
        mock_claude_service.analyze_maintenance_request.assert_called_once()
    
    def test_analyze_maintenance_emergency(self, auth_headers, mock_claude_service):
        """Test emergency maintenance detection"""
        # Mock emergency response
        mock_claude_service.analyze_maintenance_request.return_value = {
            **mock_claude_service.analyze_maintenance_request.return_value,
            "urgency_level": "emergency"
        }
        
        response = client.post("/api/analyze-maintenance",
            headers=auth_headers,
            json={
                "email_content": "Water flooding apartment! Help!"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["urgency_level"] == "emergency"

class TestResponseGeneration:
    """Test response generation endpoint"""
    
    def test_generate_response_success(self, auth_headers, mock_claude_service):
        """Test successful response generation"""
        request_data = {
            "template_type": "maintenance_acknowledgment",
            "context": {
                "ticket_id": "TKT-12345",
                "issue": "Water leak",
                "timeline": "24 hours"
            },
            "tone": "professional"
        }
        
        response = client.post("/api/generate-response",
            headers=auth_headers,
            json=request_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert data["template_used"] == "maintenance_acknowledgment"
        assert "generated_at" in data
        
        mock_claude_service.generate_response.assert_called_once()
    
    def test_generate_response_compliance_check(self, auth_headers, mock_claude_service):
        """Test response compliance checking in production"""
        with patch('main_secure.settings.environment', 'production'):
            request_data = {
                "template_type": "payment_balance",
                "context": {
                    "balance": "$1,200",
                    "due_date": "2024-02-01"
                }
            }
            
            response = client.post("/api/generate-response",
                headers=auth_headers,
                json=request_data
            )
            
            assert response.status_code == 200
            # Compliance check should have been called
            mock_claude_service.check_compliance.assert_called()

class TestEntityExtraction:
    """Test entity extraction endpoint"""
    
    def test_extract_entities_success(self, auth_headers, mock_claude_service):
        """Test successful entity extraction"""
        response = client.post("/api/extract-entities",
            headers=auth_headers,
            json={
                "text": "John Doe from Apt 101 called at 555-1234 about a $500 repair needed tomorrow at 3pm"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "entities" in data
        entities = data["entities"]
        assert "John Doe" in entities["names"]
        assert "Apt 101" in entities["addresses"]
        assert "555-1234" in entities["phone_numbers"]
        assert "$500" in entities["amounts"]

class TestComplianceCheck:
    """Test compliance checking endpoint"""
    
    def test_check_compliance_success(self, auth_headers, mock_claude_service):
        """Test successful compliance check"""
        response = client.post("/api/check-compliance",
            headers=auth_headers,
            json={
                "message": "Your rent is due. Please pay within 3 days.",
                "state": "CA"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["compliance"]["is_compliant"] is True
        assert data["state"] == "CA"
        assert "checked_at" in data
    
    def test_check_compliance_invalid_state(self, auth_headers):
        """Test invalid state code validation"""
        response = client.post("/api/check-compliance",
            headers=auth_headers,
            json={
                "message": "Test message",
                "state": "ZZ"  # Invalid state
            }
        )
        
        assert response.status_code == 400
        assert "Invalid state code" in response.json()["detail"]

class TestWebhookEndpoint:
    """Test webhook endpoint"""
    
    def test_webhook_email_received(self, auth_headers, mock_claude_service, mock_supabase):
        """Test webhook for email received event"""
        webhook_data = {
            "event_type": "email_received",
            "payload": {
                "sender_email": "tenant@example.com",
                "subject": "Maintenance Request",
                "body_text": "Need help with plumbing"
            }
        }
        
        response = client.post("/api/webhook/n8n",
            headers=auth_headers,
            json=webhook_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "received"
        assert data["event_type"] == "email_received"
        
        # Verify email was processed
        mock_claude_service.classify_email.assert_called_once()

class TestStatsEndpoint:
    """Test statistics endpoint"""
    
    def test_get_stats_success(self, auth_headers, mock_supabase):
        """Test successful stats retrieval"""
        response = client.get("/api/stats", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_emails"] == 3
        assert data["by_category"]["maintenance"] == 2
        assert data["by_category"]["payment"] == 1
        assert "timestamp" in data

class TestAdminEndpoints:
    """Test admin endpoints"""
    
    def test_create_api_key_success(self, auth_headers):
        """Test API key creation"""
        # Create admin token
        admin_token = auth_service.create_access_token(
            subject="admin_user",
            scopes=[Scopes.ADMIN]
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.post("/api/admin/create-api-key",
            headers=admin_headers,
            json={
                "name": "Test Integration",
                "scopes": [Scopes.EMAIL_READ, Scopes.EMAIL_CLASSIFY]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["api_key"].startswith("sk_live_")
        assert data["name"] == "Test Integration"
        assert Scopes.EMAIL_READ in data["scopes"]
        assert "warning" in data
    
    def test_create_api_key_invalid_scope(self):
        """Test API key creation with invalid scope"""
        admin_token = auth_service.create_access_token(
            subject="admin_user",
            scopes=[Scopes.ADMIN]
        )
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        response = client.post("/api/admin/create-api-key",
            headers=admin_headers,
            json={
                "name": "Test",
                "scopes": ["invalid:scope"]
            }
        )
        
        assert response.status_code == 400
        assert "Invalid scope" in response.json()["detail"]

if __name__ == "__main__":
    pytest.main([__file__, "-v"])