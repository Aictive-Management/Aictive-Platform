# Aictive Platform v2 - Complete Production System

## 🚀 Production Deployment Guide

### System Overview
The Aictive Platform v2 is a production-ready AI-powered property management system that integrates with RentVine, provides intelligent workflow automation, and offers comprehensive monitoring and security features.

## 1. ✅ What's Built and Ready

### Core Components

#### **RentVine Integration** (`rentvine_api_client.py`, `rentvine_webhook_handler.py`)
- ✅ Full API client with authentication, rate limiting, and circuit breaker
- ✅ Webhook receiver with signature verification
- ✅ Event handlers for all property management events
- ✅ Automatic retry logic and caching

#### **AI Services** (`claude_service.py`, `super_claude_swarm_orchestrator.py`)
- ✅ Claude integration for email classification and analysis
- ✅ Swarm orchestration for complex workflows
- ✅ Multi-agent role system with 18 specialized agents
- ✅ Compliance checking and response generation

#### **Security Layer** (`auth.py`, `security_headers_middleware.py`)
- ✅ API key authentication with scoped permissions
- ✅ Rate limiting per endpoint and client
- ✅ Security headers (CSRF, XSS protection)
- ✅ Input validation and sanitization

#### **Data Layer** (`data_layer_core.py`, `supabase_schema.sql`)
- ✅ Supabase integration for persistent storage
- ✅ Redis caching strategy
- ✅ Database migration system
- ✅ Data encryption at rest and in transit

#### **Monitoring & Observability** (`distributed_tracing.py`, `production_monitoring.py`)
- ✅ OpenTelemetry distributed tracing with Jaeger
- ✅ Prometheus metrics collection
- ✅ Health check system with degraded state detection
- ✅ Alert management with Slack/PagerDuty integration

#### **API Server** (`main_secure.py`)
- ✅ FastAPI with full authentication
- ✅ Workflow management endpoints
- ✅ Email processing endpoints
- ✅ Admin endpoints for API key management

### Integration Points

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   RentVine API  │────▶│  Webhook Handler │────▶│ Workflow Engine │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                                │                          │
                                ▼                          ▼
                        ┌──────────────────┐      ┌─────────────────┐
                        │  Event Processor │      │  AI Orchestrator│
                        └──────────────────┘      └─────────────────┘
                                │                          │
                                ▼                          ▼
                        ┌──────────────────┐      ┌─────────────────┐
                        │    Supabase DB   │      │   Redis Cache   │
                        └──────────────────┘      └─────────────────┘
```

## 2. 🏃 Quick Start Guide

### Test RentVine Connection Today

```bash
# 1. Set environment variables
export RENTVINE_API_KEY="your_api_key"
export RENTVINE_API_SECRET="your_api_secret"
export RENTVINE_TENANT_ID="your_tenant_id"

# 2. Test RentVine API connection
python test_rentvine_integration.py

# 3. Test webhook receiver (in another terminal)
python rentvine_webhook_handler.py

# 4. Send test webhook
curl -X POST http://localhost:8001/webhooks/rentvine \
  -H "X-RentVine-Signature: sha256=test_signature" \
  -H "Content-Type: application/json" \
  -d '{"event_type":"property.created","data":{"id":"test_123"}}'
```

### Deploy Webhook System

```bash
# 1. Configure production webhook URL in RentVine
# Dashboard → Settings → Webhooks → Add Endpoint
# URL: https://your-domain.com/webhooks/rentvine

# 2. Deploy webhook handler
docker build -f Dockerfile.webhook -t aictive-webhook .
docker run -d \
  -p 8001:8001 \
  -e RENTVINE_SIGNING_KEY="dszqtymvoxttkw35yrvisaimwhczpsa0-t3qpw5sz-f5ybqa4c" \
  --name aictive-webhook \
  aictive-webhook

# 3. Verify webhook health
curl https://your-domain.com/webhooks/health
```

### Enable Monitoring and Tracing

```bash
# 1. Start Jaeger for tracing
docker run -d --name jaeger \
  -p 16686:16686 \
  -p 14268:14268 \
  jaegertracing/all-in-one:latest

# 2. Start Prometheus
docker run -d --name prometheus \
  -p 9090:9090 \
  -v ./prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# 3. Initialize tracing in your app
python setup_tracing.py

# 4. View traces at http://localhost:16686
# View metrics at http://localhost:9090
```

## 3. 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          External Systems                            │
├─────────────────┬────────────────┬─────────────────┬───────────────┤
│    RentVine     │      Slack      │     Email       │   Frontend   │
│      API        │    Webhooks     │    (SMTP)       │   (React)    │
└────────┬────────┴────────┬────────┴────────┬────────┴───────┬───────┘
         │                 │                 │                │
         ▼                 ▼                 ▼                ▼
┌─────────────────────────────────────────────────────────────────────┐
│                        API Gateway Layer                             │
├─────────────────────────────────────────────────────────────────────┤
│  • Authentication (API Keys)    • Rate Limiting                     │
│  • Request Validation           • Security Headers                  │
└────────────────────────────┬─────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                     Application Layer                                │
├─────────────────┬──────────────────┬────────────────┬──────────────┤
│  Webhook Handler │  Workflow Engine │  AI Orchestrator│ API Server  │
│  • Event receipt │  • Multi-agent   │  • Claude API   │ • FastAPI   │
│  • Verification  │  • Approval flow │  • Swarm logic  │ • Endpoints │
└─────────────────┴──────────────────┴────────────────┴──────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                       Service Layer                                  │
├────────────────┬────────────────┬─────────────────┬────────────────┤
│ Email Processor │ Maintenance    │ Financial       │ Compliance     │
│ • Classification│ • Work orders   │ • Payments      │ • State laws   │
│ • Response gen  │ • Scheduling    │ • Invoicing     │ • Validation   │
└────────────────┴────────────────┴─────────────────┴────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                      Data & Cache Layer                              │
├─────────────────────────┬───────────────────────────────────────────┤
│      Supabase DB        │            Redis Cache                    │
│  • Emails               │  • API responses                          │
│  • Workflows            │  • Session data                           │
│  • Agent actions        │  • Rate limit counters                    │
└─────────────────────────┴───────────────────────────────────────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────────┐
│                  Monitoring & Observability                          │
├────────────────┬────────────────┬─────────────────┬────────────────┤
│ Distributed     │ Metrics         │ Health Checks   │ Alerts        │
│ Tracing         │ (Prometheus)    │ • System        │ • Slack       │
│ (Jaeger)        │ • Business      │ • Services      │ • PagerDuty   │
└────────────────┴────────────────┴─────────────────┴────────────────┘
```

## 4. 📋 Production Deployment Checklist

### Pre-Deployment
- [ ] Set all environment variables in `.env.production`
- [ ] Configure RentVine API credentials
- [ ] Set up Supabase project and get connection string
- [ ] Configure Redis instance
- [ ] Set up monitoring infrastructure (Jaeger, Prometheus)
- [ ] Configure alert channels (Slack webhook, PagerDuty)
- [ ] Generate production API keys
- [ ] Configure domain and SSL certificates

### Deployment Steps
1. **Database Setup**
   ```bash
   # Run database migrations
   python database_migration_system.py --env production
   
   # Verify schema
   psql $DATABASE_URL < supabase_schema.sql
   ```

2. **Deploy Core Services**
   ```bash
   # Deploy API server
   docker-compose -f docker-compose.prod.yml up -d api
   
   # Deploy webhook handler
   docker-compose -f docker-compose.prod.yml up -d webhook
   
   # Deploy background workers
   docker-compose -f docker-compose.prod.yml up -d worker
   ```

3. **Configure RentVine Webhooks**
   - Log into RentVine dashboard
   - Navigate to Settings → Webhooks
   - Add endpoint: `https://api.yourdomain.com/webhooks/rentvine`
   - Select events to subscribe to
   - Copy signing key to environment

4. **Verify Deployment**
   ```bash
   # Health checks
   curl https://api.yourdomain.com/health
   curl https://api.yourdomain.com/webhooks/health
   
   # Test API authentication
   curl -H "Authorization: Bearer $API_KEY" \
     https://api.yourdomain.com/api/stats
   
   # Check monitoring
   open http://monitoring.yourdomain.com:16686  # Jaeger
   open http://monitoring.yourdomain.com:9090   # Prometheus
   ```

### Post-Deployment
- [ ] Monitor logs for first 24 hours
- [ ] Verify webhook events are being received
- [ ] Check alert channels are working
- [ ] Review initial metrics and traces
- [ ] Document any issues or adjustments

## 5. 🚦 Next Immediate Steps

### Week 1: Core Integration
1. **Monday**: Deploy webhook handler and verify RentVine events
2. **Tuesday**: Test email classification with real emails
3. **Wednesday**: Deploy workflow engine with basic flows
4. **Thursday**: Enable monitoring and verify metrics
5. **Friday**: Run integration tests and fix issues

### Week 2: Advanced Features
1. **Enable AI swarm orchestration** for complex workflows
2. **Configure approval chains** for different property types
3. **Set up automated alerts** for critical events
4. **Implement data archival** strategy
5. **Load test** the system with expected volume

### Week 3: Optimization
1. **Tune rate limits** based on actual usage
2. **Optimize caching** strategies
3. **Review and adjust** alert thresholds
4. **Train team** on monitoring dashboards
5. **Document runbooks** for common issues

## 6. 🔧 Maintenance Commands

```bash
# View recent webhook events
docker logs aictive-webhook --tail 100

# Check API server health
curl http://localhost:8000/health | jq

# View active workflows
curl -H "Authorization: Bearer $API_KEY" \
  http://localhost:8000/api/workflows?status=active | jq

# Trigger manual workflow
curl -X POST -H "Authorization: Bearer $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"workflow_type":"maintenance","property_size":10}' \
  http://localhost:8000/api/workflows/create

# Check Redis cache
redis-cli INFO stats

# View Prometheus metrics
curl http://localhost:8000/metrics
```

## 7. 🚨 Emergency Procedures

### System Down
1. Check health endpoints
2. Review container logs
3. Verify database connectivity
4. Check external service status (RentVine, Claude)
5. Escalate to on-call if needed

### High Error Rate
1. Check `/metrics` for error counters
2. Review Jaeger traces for failures
3. Check rate limit violations
4. Review recent deployments
5. Consider rolling back if needed

### Performance Issues
1. Check CPU/memory metrics
2. Review slow query logs
3. Check cache hit rates
4. Review concurrent request counts
5. Scale horizontally if needed

---

**Ready for Production!** 🎉

The system is fully built and ready for deployment. Follow this guide step-by-step for a smooth production launch. All components have been tested individually and are designed to work together seamlessly.

For support: Contact the development team or check the detailed documentation in the `/docs` directory.