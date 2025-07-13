# Aictive Platform - AI-Powered Property Management Email Processing

## 🚀 Overview

Aictive Platform is a secure, high-performance API for intelligent email processing in property management. It leverages Claude AI to automatically classify emails, analyze maintenance requests, generate responses, and ensure legal compliance.

## ✨ Features

- **Email Classification**: Automatically categorize emails (maintenance, payment, lease, general)
- **Maintenance Analysis**: Extract detailed information from maintenance requests
- **Response Generation**: Create context-aware, compliant email responses
- **Entity Extraction**: Identify names, addresses, phone numbers, dates, and amounts
- **Compliance Checking**: Ensure messages comply with rental laws (state-specific)
- **Webhook Integration**: Support for n8n automation workflows
- **Real-time Notifications**: Slack integration for urgent issues

## 🔒 Security Features

- **JWT Authentication**: Secure token-based authentication
- **API Key Management**: Scoped API keys with bcrypt hashing
- **Rate Limiting**: Configurable per-user rate limits
- **Input Validation**: Comprehensive input sanitization and validation
- **CORS Protection**: Configurable allowed origins
- **Security Headers**: XSS, CSRF, and clickjacking protection
- **SQL Injection Prevention**: Parameterized queries and input sanitization

## 🏗️ Architecture

Built with:
- **FastAPI**: Modern, fast Python web framework
- **Claude AI**: Anthropic's AI for intelligent processing
- **Supabase**: PostgreSQL database with real-time capabilities
- **Pydantic**: Data validation using Python type annotations
- **JWT**: Secure authentication tokens
- **Async/Await**: High-performance asynchronous operations

## 📋 Requirements

- Python 3.9+
- Virtual environment (recommended)
- API keys for:
  - Anthropic (Claude AI)
  - Supabase
  - RentVine (optional)
  - Slack webhook (optional)

## 🚀 Quick Start

### 1. Clone and Setup

```bash
# Clone repository
git clone https://github.com/yourusername/aictive-platform.git
cd aictive-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

Create a `.env` file based on `.env.example`:

```bash
cp .env.example .env
# Edit .env with your API keys
```

Required environment variables:
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_ANON_KEY`: Supabase anonymous key
- `ANTHROPIC_API_KEY`: Claude AI API key
- `API_KEY`: Your API key for this service
- `SECRET_KEY`: Secret key for JWT tokens
- `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

### 3. Run Development Server

```bash
# Development mode with auto-reload
uvicorn main_secure:app --reload --host 0.0.0.0 --port 8000

# Access API documentation
open http://localhost:8000/docs
```

### 4. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest test_security.py -v
```

## 🔑 Authentication

### Getting Started

1. **Create an API Key** (requires admin access):
```bash
curl -X POST http://localhost:8000/api/admin/create-api-key \
  -H "Authorization: Bearer YOUR_ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Integration",
    "scopes": ["email:read", "email:classify"]
  }'
```

2. **Use the API Key**:
```bash
# Get JWT token
TOKEN=$(curl -X POST http://localhost:8000/api/auth/token \
  -d "api_key=YOUR_API_KEY" | jq -r .access_token)

# Make authenticated requests
curl http://localhost:8000/api/classify-email \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "sender_email": "tenant@example.com",
    "subject": "Water leak in bathroom",
    "body_text": "There is water leaking from under the sink."
  }'
```

### Available Scopes

- `email:read` - Read email data
- `email:write` - Create/update emails
- `email:classify` - Classify emails
- `maintenance:analyze` - Analyze maintenance requests
- `response:generate` - Generate email responses
- `compliance:check` - Check legal compliance
- `stats:read` - View statistics
- `webhook:write` - Create webhook events
- `admin` - Admin operations

## 📚 API Endpoints

### Public Endpoints

- `GET /` - Health check
- `GET /health` - Detailed health status

### Email Processing

- `POST /api/classify-email` - Classify an email
- `POST /api/analyze-maintenance` - Analyze maintenance request
- `POST /api/generate-response` - Generate email response
- `POST /api/extract-entities` - Extract entities from text
- `POST /api/check-compliance` - Check message compliance

### Statistics & Admin

- `GET /api/stats` - Platform statistics
- `POST /api/admin/create-api-key` - Create new API key (admin only)

### Webhooks

- `POST /api/webhook/n8n` - n8n webhook endpoint

## 🧪 Testing

The project includes comprehensive test suites:

- **Security Tests** (`test_security.py`): Authentication, authorization, input validation
- **API Tests** (`test_api.py`): Endpoint functionality, error handling
- **Performance Tests**: Caching, rate limiting

Run tests with coverage:
```bash
pytest --cov=. --cov-report=term-missing
```

## 🚀 Production Deployment

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with 4 workers
gunicorn main_secure:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Environment Variables for Production

```bash
ENVIRONMENT=production
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com
```

### Security Checklist

- [ ] Rotate all API keys
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `ALLOWED_ORIGINS`
- [ ] Enable HTTPS
- [ ] Set up monitoring
- [ ] Configure rate limits
- [ ] Enable audit logging
- [ ] Set up backup strategy

## 📊 Performance

- **Caching**: Intelligent caching for Claude responses
- **Rate Limiting**: 60 requests/minute per user (configurable)
- **Async Operations**: All I/O operations are asynchronous
- **Background Tasks**: Email storage and notifications run in background

## 🔧 Configuration

See `config.py` for all configuration options:

```python
# Performance settings
CACHE_TTL_SECONDS=3600  # 1 hour cache
MAX_CLAUDE_RETRIES=3
CLAUDE_TIMEOUT_SECONDS=30

# Security settings
RATE_LIMIT_PER_MINUTE=60
MAX_REQUEST_SIZE=1048576  # 1MB
TOKEN_EXPIRY_HOURS=24
```

## 🐛 Troubleshooting

### Common Issues

1. **"Exposed API key detected"**: Rotate your keys immediately
2. **Rate limit exceeded**: Wait 1 minute or increase limits
3. **CORS errors**: Check `ALLOWED_ORIGINS` configuration
4. **Database connection failed**: Verify Supabase credentials

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG uvicorn main_secure:app --reload
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests and ensure coverage
4. Submit a pull request

## 📝 License

[MIT License](LICENSE)

## 🙏 Acknowledgments

- Built with [SuperClaude](https://github.com/superclaude) standards
- Powered by [Anthropic Claude AI](https://anthropic.com)
- Database by [Supabase](https://supabase.com)

---

**Security Notice**: Never commit `.env` files or expose API keys. Always use environment variables for sensitive configuration.