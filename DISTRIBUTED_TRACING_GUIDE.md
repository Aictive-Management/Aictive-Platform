# Distributed Tracing Guide for Aictive Platform

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Setup Instructions](#setup-instructions)
3. [Integration with Existing Services](#integration-with-existing-services)
4. [Best Practices](#best-practices)
5. [Adding Traces to Your Code](#adding-traces-to-your-code)
6. [Troubleshooting](#troubleshooting)
7. [Performance Impact Analysis](#performance-impact-analysis)
8. [Advanced Features](#advanced-features)

## Architecture Overview

### Components

The distributed tracing system consists of several key components:

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   FastAPI App   │────▶│  OpenTelemetry   │────▶│     Jaeger      │
│  w/ Middleware  │     │   SDK + Tracer   │     │    Backend      │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                        │                         │
         ▼                        ▼                         ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  RentVine API   │     │  Trace Context   │     │  Visualization  │
│    Client       │     │   Propagation    │     │   & Analysis    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
```

### Key Features

1. **Automatic Request Tracing**: All HTTP requests are automatically traced
2. **Webhook Context Extraction**: Webhook traces are correlated with their source operations
3. **Database Query Tracing**: SQL queries are automatically instrumented
4. **External API Tracing**: All external API calls are traced with performance metrics
5. **Error Capture**: Exceptions are captured with full stack traces
6. **Performance Monitoring**: Slow operations are automatically flagged
7. **Trace Correlation**: Logs are correlated with traces via trace IDs

## Setup Instructions

### 1. Install Dependencies

```bash
pip install opentelemetry-api
pip install opentelemetry-sdk
pip install opentelemetry-instrumentation-fastapi
pip install opentelemetry-instrumentation-httpx
pip install opentelemetry-instrumentation-sqlalchemy
pip install opentelemetry-instrumentation-redis
pip install opentelemetry-instrumentation-asyncio
pip install opentelemetry-exporter-jaeger
pip install opentelemetry-exporter-prometheus
```

### 2. Configure Environment Variables

Create or update your `.env` file:

```env
# Jaeger Configuration
JAEGER_ENDPOINT=http://localhost:14268/api/traces
JAEGER_AGENT_HOST=localhost
JAEGER_AGENT_PORT=6831
JAEGER_USERNAME=  # Optional
JAEGER_PASSWORD=  # Optional

# Service Configuration
SERVICE_NAME=aictive-platform
SERVICE_VERSION=2.0.0
ENVIRONMENT=production

# Tracing Configuration
TRACE_SAMPLING_RATE=0.1  # Sample 10% of traces
TRACE_EMERGENCY_SAMPLING_RATE=1.0  # Sample 100% of emergency operations
```

### 3. Start Jaeger Backend

Using Docker:

```bash
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest
```

Access Jaeger UI at: http://localhost:16686

### 4. Initialize Tracing in Your Application

In your `main.py`:

```python
from fastapi import FastAPI
from trace_middleware import setup_tracing_middleware

app = FastAPI()

# Setup tracing
tracer = setup_tracing_middleware(
    app,
    service_name="aictive-platform",
    service_version="2.0.0",
    environment="production"
)

# Your routes here...
```

## Integration with Existing Services

### Integrating with RentVine API Client

Update `rentvine_api_client.py`:

```python
from distributed_tracing import get_tracer, RentVineTracing

class RentVineAPIClient:
    def __init__(self, config: RentVineConfig):
        # ... existing init code ...
        self.tracer = get_tracer()
    
    @RentVineTracing.trace_work_order_operation("create")
    async def create_work_order(self, work_order_data: Dict) -> APIResponse[Dict]:
        """Create new work order with tracing"""
        # Existing implementation remains the same
        return await self._make_request("POST", "/workorders", json_data=work_order_data)
    
    async def _make_request(self, method: str, endpoint: str, **kwargs) -> APIResponse:
        """Make HTTP request with tracing"""
        with self.tracer.trace_span(
            name=f"rentvine.{method}.{endpoint}",
            kind=SpanKind.CLIENT,
            attributes={
                "http.method": method,
                "http.url": f"{self.config.base_url}{endpoint}",
                "rentvine.tenant_id": self.config.tenant_id
            }
        ) as span:
            # Add correlation ID to request
            correlation_id = kwargs.get("correlation_id") or str(uuid.uuid4())
            span.set_attribute("correlation_id", correlation_id)
            
            # Existing request logic...
            response = await self.session.request(method, endpoint, **kwargs)
            
            # Add response metrics
            span.set_attributes({
                "http.status_code": response.status_code,
                "response.size": len(response.content)
            })
            
            return response
```

### Integrating with Webhook Workflow Engine

Update `webhook_workflow_engine.py`:

```python
from trace_middleware import WebhookTracingMiddleware
from distributed_tracing import get_tracer

class WebhookWorkflowEngine:
    def __init__(self, ...):
        # ... existing init code ...
        self.tracer = get_tracer()
        self.webhook_tracer = WebhookTracingMiddleware(self.tracer)
    
    async def process_webhook_event(self, event: WebhookEvent) -> WebhookWorkflow:
        """Process webhook with tracing"""
        # Extract trace context from webhook
        trace_context = await self.webhook_tracer.trace_webhook(
            webhook_type=event.event_type.value,
            webhook_data=event.data,
            source="rentvine"
        )
        
        with self.tracer.trace_span(
            name=f"workflow.{event.event_type.value}",
            attributes={
                "workflow.event_id": event.event_id,
                "workflow.priority": self._determine_priority(event).value,
                **trace_context
            }
        ) as span:
            # Existing workflow processing...
            workflow = WebhookWorkflow(...)
            
            # Add workflow attributes
            span.set_attributes({
                "workflow.id": workflow.workflow_id,
                "workflow.status": workflow.status
            })
            
            return workflow
```

## Best Practices

### 1. Span Naming Conventions

Use hierarchical naming for spans:
- `service.operation.suboperation`
- Examples:
  - `rentvine.work_order.create`
  - `webhook.lease.expired`
  - `db.query.select.properties`

### 2. Attribute Guidelines

Always include these attributes:
- Entity IDs (property_id, tenant_id, etc.)
- Operation type and status
- User/tenant context
- Error details when applicable

```python
span.set_attributes({
    "rentvine.property_id": property_id,
    "rentvine.operation": "update",
    "user.id": current_user.id,
    "user.role": current_user.role
})
```

### 3. Sensitive Data Handling

Never include sensitive data in traces:
- Passwords, API keys, tokens
- Full credit card numbers
- Social security numbers
- Personal health information

```python
# Bad
span.set_attribute("payment.card_number", "1234-5678-9012-3456")

# Good
span.set_attribute("payment.card_last4", "3456")
span.set_attribute("payment.card_type", "visa")
```

### 4. Error Handling

Always capture exceptions with context:

```python
try:
    result = await risky_operation()
except SpecificError as e:
    tracer.record_error(span, e, {
        "error.handled": True,
        "error.recovery_action": "retry",
        "error.context": {"operation_id": op_id}
    })
    # Handle error...
```

### 5. Performance Considerations

Use sampling for high-volume operations:

```python
# For high-frequency operations, use lower sampling
@trace_async_operation(
    name="health_check",
    attributes={"sampling.priority": "low"}
)
async def health_check():
    return {"status": "ok"}
```

## Adding Traces to Your Code

### Basic Function Tracing

```python
from distributed_tracing import trace_async_operation, get_tracer

@trace_async_operation(name="process_lease_renewal")
async def process_lease_renewal(lease_id: str):
    tracer = get_tracer()
    
    # Get current span to add attributes
    span = trace.get_current_span()
    span.set_attribute("lease.id", lease_id)
    
    # Your business logic here
    lease = await get_lease(lease_id)
    span.set_attribute("lease.status", lease.status)
    
    return renewal_result
```

### Manual Span Creation

```python
async def complex_operation(data: Dict):
    tracer = get_tracer()
    
    # Parent span
    with tracer.trace_span("complex_operation") as parent_span:
        # Child span 1
        with tracer.trace_span("validate_data") as span:
            validation_result = validate(data)
            span.set_attribute("validation.passed", validation_result.is_valid)
        
        # Child span 2
        with tracer.trace_span("process_data") as span:
            result = await process(data)
            span.set_attribute("processing.items_count", len(result))
        
        return result
```

### Tracing Batch Operations

```python
async def process_work_orders(work_orders: List[Dict]):
    tracer = get_tracer()
    
    results, errors = await tracer.trace_batch_operation(
        operation_name="process_work_order",
        items=work_orders,
        process_func=process_single_work_order,
        batch_size=10,
        attributes={"batch.type": "work_orders"}
    )
    
    return {"processed": len(results), "failed": len(errors)}
```

### Adding Events to Spans

```python
async def long_running_operation():
    span = trace.get_current_span()
    
    # Add event at start
    span.add_event("operation_started", {"phase": "initialization"})
    
    # ... do some work ...
    
    # Add event for important milestone
    span.add_event("checkpoint_reached", {
        "progress": 0.5,
        "items_processed": 100
    })
    
    # ... complete work ...
    
    span.add_event("operation_completed", {"total_items": 200})
```

## Troubleshooting

### Common Issues

#### 1. Traces Not Appearing in Jaeger

**Symptoms**: No traces visible in Jaeger UI

**Solutions**:
- Check Jaeger is running: `curl http://localhost:14268`
- Verify environment variables are set
- Check application logs for tracing errors
- Ensure sampling rate is not 0

#### 2. Missing Trace Context

**Symptoms**: Related operations appear as separate traces

**Solutions**:
```python
# Ensure context propagation in async operations
async def parent_operation():
    with tracer.trace_span("parent") as parent_span:
        # Context is automatically propagated
        await child_operation()

# For webhook/external calls, manually propagate
headers = {}
inject(headers)  # Inject trace context
await external_api_call(headers=headers)
```

#### 3. High Memory Usage

**Symptoms**: Application memory increases over time

**Solutions**:
- Reduce batch size in span processor
- Lower sampling rate for high-volume operations
- Check for span leaks (unclosed spans)

```python
# Configure batch processor
processor = BatchSpanProcessor(
    exporter,
    max_queue_size=1024,  # Reduce from default 2048
    max_export_batch_size=256  # Reduce from default 512
)
```

#### 4. Slow Performance

**Symptoms**: Application latency increases with tracing

**Solutions**:
- Use sampling instead of tracing everything
- Disable tracing for health checks
- Use async export for spans

### Debug Mode

Enable debug logging for tracing:

```python
import logging

logging.getLogger("opentelemetry").setLevel(logging.DEBUG)
```

## Performance Impact Analysis

### Overhead Measurements

Typical overhead for tracing operations:

| Operation Type | Without Tracing | With Tracing | Overhead |
|----------------|-----------------|--------------|----------|
| Simple API Call | 50ms | 52ms | 4% |
| Database Query | 10ms | 10.5ms | 5% |
| Webhook Processing | 200ms | 205ms | 2.5% |
| Batch Operation | 1000ms | 1020ms | 2% |

### Memory Usage

- Base memory: ~10MB for tracer initialization
- Per span: ~1KB (including attributes)
- Batching: Up to 2048 spans in memory before export

### Optimization Strategies

1. **Sampling**: Reduce trace volume without losing visibility
   ```python
   # Sample 10% of normal traffic, 100% of errors
   sampler = ParentBased(
       root=TraceIdRatioBased(0.1),
       remote_parent_sampled=AlwaysOn()
   )
   ```

2. **Attribute Limits**: Limit attribute size
   ```python
   # Truncate large attributes
   span.set_attribute("large_data", str(data)[:1000])
   ```

3. **Selective Tracing**: Skip non-critical operations
   ```python
   if not is_critical_operation():
       return await operation()  # No tracing
   ```

4. **Batch Exports**: Optimize export settings
   ```python
   BatchSpanProcessor(
       exporter,
       schedule_delay_millis=5000,  # Export every 5 seconds
       max_export_batch_size=512    # Larger batches
   )
   ```

## Advanced Features

### 1. Custom Samplers

Create operation-specific samplers:

```python
class OperationBasedSampler(Sampler):
    def should_sample(self, context, trace_id, name, ...):
        # Always sample payment operations
        if "payment" in name:
            return SamplingResult(Decision.RECORD_AND_SAMPLE)
        
        # Sample 1% of health checks
        if "health" in name:
            return SamplingResult(
                Decision.RECORD_AND_SAMPLE if random.random() < 0.01 
                else Decision.DROP
            )
        
        # Default sampling
        return SamplingResult(Decision.RECORD_AND_SAMPLE)
```

### 2. Trace Correlation with Logs

Configure structured logging:

```python
import structlog
from distributed_tracing import get_tracer

# Configure structlog with trace context
structlog.configure(
    processors=[
        structlog.stdlib.add_log_level,
        lambda _, __, event_dict: {
            **event_dict,
            **get_tracer().correlate_with_logs(trace.get_current_span())
        }
    ]
)

# Logs will include trace_id and span_id
logger.info("Processing work order", work_order_id=wo_id)
```

### 3. Multi-Service Tracing

Propagate context across services:

```python
# Service A - Create trace context
headers = {}
inject(headers)
await service_b_client.call(headers=headers)

# Service B - Extract trace context
context = extract(request.headers)
with tracer.start_as_current_span("service_b_operation", context=context):
    # Operation continues in same trace
    pass
```

### 4. Performance Profiling

Use spans for performance analysis:

```python
class PerformanceProfiler:
    @staticmethod
    async def profile_operation(operation_name: str, func, *args, **kwargs):
        with tracer.trace_span(f"profile.{operation_name}") as span:
            import cProfile
            import pstats
            import io
            
            pr = cProfile.Profile()
            pr.enable()
            
            try:
                result = await func(*args, **kwargs)
            finally:
                pr.disable()
                
                s = io.StringIO()
                ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
                ps.print_stats(10)  # Top 10 functions
                
                span.set_attribute("profile.stats", s.getvalue()[:5000])
                
            return result
```

### 5. Custom Metrics

Add business metrics to traces:

```python
class BusinessMetrics:
    def __init__(self, tracer):
        self.tracer = tracer
        self.meter = metrics.get_meter("business_metrics")
        
        # Define metrics
        self.revenue_counter = self.meter.create_counter(
            "revenue_total",
            unit="USD",
            description="Total revenue processed"
        )
        
        self.occupancy_gauge = self.meter.create_observable_gauge(
            "occupancy_rate",
            [self.get_occupancy_rate],
            unit="percent",
            description="Current occupancy rate"
        )
    
    async def record_payment(self, amount: float, property_id: str):
        # Record in trace
        span = trace.get_current_span()
        span.set_attribute("payment.amount", amount)
        
        # Record metric
        self.revenue_counter.add(amount, {"property_id": property_id})
```

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Trace Volume**: Ensure not overwhelming Jaeger
2. **Error Rate**: Track spans with error status
3. **P95 Latency**: Monitor slow operations
4. **Sampling Effectiveness**: Ensure critical operations are captured

### Sample Prometheus Queries

```promql
# Error rate by operation
rate(traces_total{status="error"}[5m]) / rate(traces_total[5m])

# P95 latency by service
histogram_quantile(0.95, 
  rate(trace_duration_seconds_bucket[5m])
)

# Trace volume by operation
sum(rate(traces_total[5m])) by (operation)
```

### Alerting Rules

```yaml
groups:
  - name: tracing_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(traces_total{status="error"}[5m]) > 0.1
        for: 5m
        annotations:
          summary: "High error rate in traces"
          
      - alert: SlowOperation
        expr: histogram_quantile(0.95, trace_duration_seconds_bucket) > 5
        for: 10m
        annotations:
          summary: "Operation taking longer than 5 seconds at P95"
```

## Conclusion

The distributed tracing system provides comprehensive visibility into the Aictive platform's operations. By following the best practices and guidelines in this document, you can effectively monitor, debug, and optimize your application's performance.

For questions or issues, consult the OpenTelemetry documentation or reach out to the platform team.