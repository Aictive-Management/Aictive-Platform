# SuperClaude Configuration - Aictive Platform

## Project Overview
AI-powered property management email processing system using Claude AI for intelligent email classification, maintenance request analysis, and automated response generation.

## Architecture
- **Frontend**: React + TypeScript + Vite
- **Backend**: FastAPI + Python 3.9+
- **AI**: Anthropic Claude API (Haiku/Sonnet/Opus models)
- **Database**: Supabase (PostgreSQL)
- **Integrations**: RentVine, Slack, n8n webhooks

## Development Standards
- Evidence-based development
- Security-first approach (OWASP Top 10 compliance)
- TDD methodology
- Comprehensive documentation
- Type safety (TypeScript + Pydantic)

## Commands
### Python/FastAPI
- Lint: `source venv/bin/activate && ruff check .`
- Format: `source venv/bin/activate && black .`
- Type check: `source venv/bin/activate && mypy .`
- Test: `source venv/bin/activate && pytest`
- Run dev: `source venv/bin/activate && uvicorn main:app --reload`

### Production
- Build: `pip install gunicorn`
- Run: `gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker`

## API Endpoints
- `POST /api/classify-email` - Classify incoming emails
- `POST /api/analyze-maintenance` - Analyze maintenance requests
- `POST /api/generate-response` - Generate email responses
- `POST /api/extract-entities` - Extract entities from text
- `POST /api/check-compliance` - Check legal compliance
- `POST /api/webhook/n8n` - n8n webhook handler
- `GET /api/stats` - Platform statistics

## Key Patterns
### Email Classification
- Categories: maintenance, payment, lease, general
- Confidence scoring
- Urgency detection (low/medium/high/emergency)
- Sentiment analysis

### Maintenance Analysis
- Issue type detection
- Location mapping
- Urgency indicators
- Complexity estimation
- Parts requirement detection

### Response Generation
- Template-based system
- Context-aware responses
- Tone adjustment
- Compliance checking

## Security Notes
- API keys stored in .env (never commit)
- OWASP Top 10 compliance required
- Input validation on all endpoints
- Rate limiting recommended
- CORS configuration for production

## Performance Optimizations
- Async/await throughout
- Background task processing
- MCP caching strategies
- Model selection based on complexity

## Testing Strategy
- Unit tests for service methods
- Integration tests for API endpoints
- Mock external services (Claude, Supabase)
- E2E tests for critical workflows

## Deployment Checklist
- [ ] Environment variables configured
- [ ] Database migrations complete
- [ ] Security scan passed
- [ ] Performance benchmarks met
- [ ] Monitoring configured
- [ ] Backup strategy in place

## SuperClaude Integration
This project follows SuperClaude standards:
- Evidence-based language in all outputs
- Structured error handling
- Comprehensive logging
- Performance profiling enabled
- Security-first development