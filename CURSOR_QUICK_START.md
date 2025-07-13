# Cursor Quick Start - Aictive Platform

## ⚡ Get Up and Running in 10 Minutes

### 1. Open in Cursor (1 min)
```bash
cd /Users/garymartin/aictive-platform
cursor .
```

### 2. Activate Virtual Environment (30 sec)
```bash
source venv/bin/activate
```

### 3. Run Health Check (2 min)
```bash
python scripts/health_check.py
```

### 4. Test a Workflow (3 min)
```bash
python scripts/test_single_workflow.py
```

### 5. Start Development Server (1 min)
```bash
uvicorn main_secure:app --reload
```

### 6. View API Documentation (30 sec)
Open: http://localhost:8000/docs

### 7. Run Demo (2 min)
```bash
python simple_demo.py
```

## 🎯 What You Can Do Now

### Test Existing Workflows
- Email classification
- Maintenance request analysis
- Response generation
- Entity extraction

### Explore the Codebase
- `main_secure.py` - Main application
- `role_agents.py` - AI agents
- `sop_orchestration.py` - Workflows
- `integrations.py` - External services

### Use Cursor AI
- `Cmd+L` - Ask questions about code
- `Cmd+K` - Quick edits and transformations
- Highlight code + `Cmd+K` - Refactor and improve

## 🚀 Next Steps

1. **Understand Patterns**: Study existing workflows
2. **Build Something**: Create a custom workflow
3. **Add Integrations**: Connect to real services
4. **Deploy**: Move to production

## 🔧 Essential Commands

```bash
# Development
uvicorn main_secure:app --reload
python simple_demo.py
python workflow_demo.py

# Testing
pytest test_api.py -v
pytest test_security.py -v

# Health checks
curl http://localhost:8000/health
```

## 💡 Pro Tips

- Start with demos to understand patterns
- Use Cursor AI for code explanations
- Build incrementally using existing agents
- Test frequently with provided scripts

**You're ready to build! 🚀** 