# Cursor Migration Guide for Aictive Platform

## 🎯 Overview

This guide helps you migrate your Aictive platform development to Cursor IDE, leveraging AI assistance for faster, more intelligent development.

## 📋 Prerequisites

- Cursor IDE installed
- Python 3.9+ 
- Git repository cloned
- Virtual environment ready

## 🚀 Step-by-Step Migration

### 1. Open Project in Cursor

```bash
cd /Users/garymartin/aictive-platform
cursor .
```

### 2. Verify Environment

Run the health check script:
```bash
python scripts/health_check.py
```

This will verify:
- Python version
- Dependencies installed
- Environment variables
- Database connectivity
- API endpoints

### 3. Test Core Functionality

```bash
# Test a single workflow
python scripts/test_single_workflow.py

# Run existing demos
python simple_demo.py
python workflow_demo.py
```

### 4. Explore the Codebase

Key files to understand:
- `main_secure.py` - Main FastAPI application
- `role_agents.py` - AI agent definitions
- `sop_orchestration.py` - Workflow orchestration
- `integrations.py` - External service integrations
- `config.py` - Configuration management

## 🔧 Cursor-Specific Setup

### AI Context (.cursorrules)

The `.cursorrules` file provides Cursor AI with:
- Project architecture understanding
- Coding patterns and conventions
- Security requirements
- Testing strategies

### Development Workflow

1. **Start with Demos**: Run existing demos to understand patterns
2. **Use AI Chat**: Ask questions about code structure and functionality
3. **Incremental Development**: Build new features using existing patterns
4. **Test-Driven**: Use provided test scripts for validation

## 🎯 Key Development Patterns

### 1. Agent-Based Architecture

```python
# Example: Creating a new agent
from role_agents import Agent

class MaintenanceAgent(Agent):
    def __init__(self):
        super().__init__("maintenance_analyst")
    
    async def analyze_request(self, request_data):
        # AI-powered analysis
        pass
```

### 2. Workflow Orchestration

```python
# Example: Creating a new workflow
from sop_orchestration import WorkflowOrchestrator

orchestrator = WorkflowOrchestrator()
workflow = orchestrator.create_workflow("maintenance_processing")
```

### 3. Secure API Development

```python
# Example: Adding new endpoints
from fastapi import Depends, HTTPException
from auth import get_current_user

@app.post("/api/new-endpoint")
async def new_endpoint(
    data: RequestModel,
    current_user: User = Depends(get_current_user)
):
    # Secure endpoint implementation
    pass
```

## 🧪 Testing Strategy

### 1. Unit Tests
```bash
pytest test_api.py -v
pytest test_security.py -v
```

### 2. Integration Tests
```bash
python scripts/test_single_workflow.py
```

### 3. Manual Testing
```bash
# Start development server
uvicorn main_secure:app --reload

# Test endpoints
curl http://localhost:8000/health
```

## 🔒 Security Considerations

### 1. Environment Variables
- Never commit API keys
- Use `.env` files for local development
- Rotate keys regularly

### 2. Input Validation
- All inputs validated with Pydantic
- SQL injection prevention
- XSS protection

### 3. Authentication
- JWT tokens for API access
- API key management
- Rate limiting

## 📊 Monitoring and Debugging

### 1. Logging
```python
import logging
logger = logging.getLogger(__name__)
logger.info("Operation completed")
```

### 2. Performance Monitoring
- Cache hit rates
- API response times
- Error rates

### 3. Health Checks
```bash
curl http://localhost:8000/health
```

## 🚀 Production Deployment

### 1. Environment Setup
```bash
export ENVIRONMENT=production
export LOG_LEVEL=WARNING
```

### 2. Database Migration
```bash
# Apply Supabase schema
psql -h your-db-host -U your-user -d your-db -f supabase_schema.sql
```

### 3. Service Deployment
```bash
# Using Gunicorn
gunicorn main_secure:app -w 4 -k uvicorn.workers.UvicornWorker
```

## 🎯 Next Steps

1. **Week 1**: Familiarize with existing codebase and patterns
2. **Week 2**: Build first custom workflow using AI assistance
3. **Week 3**: Integrate with real external services
4. **Week 4**: Add new agents and capabilities

## 🔧 Useful Cursor Commands

- `Cmd+K`: Quick edits and transformations
- `Cmd+L`: Chat with AI about code
- `Cmd+Shift+P`: Command palette
- `F12`: Go to definition
- `Shift+F12`: Find all references

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Claude API Documentation](https://docs.anthropic.com/)
- [Supabase Documentation](https://supabase.com/docs)
- [Cursor Documentation](https://cursor.sh/docs)

## 🆘 Troubleshooting

### Common Issues

1. **Import Errors**: Check virtual environment activation
2. **API Key Issues**: Verify environment variables
3. **Database Connection**: Check Supabase credentials
4. **CORS Errors**: Verify ALLOWED_ORIGINS configuration

### Getting Help

1. Check the health check script output
2. Review logs for error details
3. Use Cursor AI chat for code-specific questions
4. Consult the troubleshooting section in README.md

---

**Ready to build amazing AI-powered workflows! 🚀** 