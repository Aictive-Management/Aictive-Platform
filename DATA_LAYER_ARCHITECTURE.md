# Data Layer Architecture - Aictive Platform

## Executive Summary

The Aictive Platform Data Layer provides a comprehensive, production-ready data management system designed for high availability, performance, and scalability. This architecture supports the RentVine integration and webhook systems while ensuring zero-downtime deployments and enterprise-grade reliability.

## System Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER                            │
├─────────────────────────────────────────────────────────────────┤
│  RentVine API Client │ Webhook Handlers │ Claude Service      │
└─────────────────────┬─────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│                  DATA LAYER CORE                              │
├───────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│ │ Multi-Tier      │ │ Connection      │ │ Query           │  │
│ │ Caching         │ │ Pooling         │ │ Optimization    │  │
│ │                 │ │                 │ │                 │  │
│ │ L1: Memory      │ │ PostgreSQL      │ │ Analytics       │  │
│ │ L2: Redis       │ │ MySQL Support   │ │ Monitoring      │  │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘  │
├───────────────────────────────────────────────────────────────┤
│ ┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐  │
│ │ Read Replica    │ │ Migration       │ │ Archival        │  │
│ │ Management      │ │ Framework       │ │ Strategy        │  │
│ │                 │ │                 │ │                 │  │
│ │ Load Balancing  │ │ Version Control │ │ Cold Storage    │  │
│ │ Lag Monitoring  │ │ Rollback        │ │ Retention       │  │
│ └─────────────────┘ └─────────────────┘ └─────────────────┘  │
└───────────────────────────────────────────────────────────────┘
                      │
┌─────────────────────▼─────────────────────────────────────────┐
│                 STORAGE LAYER                                 │
├───────────────────────────────────────────────────────────────┤
│  Primary DB     │  Read Replicas  │  Redis Cache  │  Archive  │
│  PostgreSQL     │  Multi-Region   │  Cluster      │  S3/GCS   │
│  MySQL          │  Load Balanced  │  Distributed  │  Local FS │
└───────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Database Connection Management (`data_layer_core.py`)

**Purpose**: Provides robust database connection pooling, health monitoring, and automatic failover.

**Key Features**:
- Async connection pooling for PostgreSQL and MySQL
- Circuit breaker pattern for fault tolerance
- Connection lifecycle management
- Health checks and metrics collection
- Automatic failover to backup databases

**Configuration Example**:
```python
primary_config = DatabaseConfig(
    host="primary-db.aictive.com",
    port=5432,
    database="aictive_production",
    username="aictive_user",
    password="secure_password",
    db_type=DatabaseType.POSTGRESQL,
    min_connections=5,
    max_connections=20,
    connection_timeout=30,
    query_timeout=60
)

await db_manager.add_database("primary", primary_config, failover_configs)
```

**Performance Metrics**:
- Connection pool utilization: < 80%
- Query execution time: P95 < 100ms
- Connection establishment: < 50ms
- Health check frequency: 60 seconds

### 2. Multi-Tier Caching Strategy (`redis_caching_strategy.py`)

**Purpose**: Implements intelligent caching with L1 (memory) and L2 (Redis) tiers for optimal performance.

**Cache Hierarchy**:
```
Application Request
        │
        ▼
   L1 Cache (Memory)
        │ miss
        ▼
   L2 Cache (Redis)
        │ miss
        ▼
    Database Query
```

**RentVine Data Caching**:
- Properties: 30-minute TTL
- Tenants: 15-minute TTL  
- Leases: 1-hour TTL
- Work Orders: 5-minute TTL
- Transactions: 2-hour TTL

**Cache Invalidation Strategies**:
- Tag-based invalidation for related data
- Event-driven invalidation on updates
- TTL-based expiration
- Manual invalidation for critical updates

**Performance Targets**:
- L1 Cache hit ratio: > 60%
- L2 Cache hit ratio: > 85%
- Combined hit ratio: > 95%
- Cache warming time: < 30 seconds

### 3. Database Migration Framework (`database_migration_system.py`)

**Purpose**: Provides version-controlled schema changes with rollback capabilities and validation.

**Migration Types**:
- Schema changes (tables, columns, indexes)
- Data transformations
- Constraint modifications
- View and function updates

**Migration Process**:
```
Migration File → Validation → Pre-checks → Execution → Post-checks → Rollback Capability
```

**Safety Features**:
- Pre-flight validation
- Destructive operation detection
- Batch processing for large data migrations
- Automatic rollback on failure
- Dependency management

**Example Migration**:
```python
MIGRATION_ID = "20241212_001_add_property_analytics"
UP_SQL = """
CREATE TABLE property_analytics (
    id SERIAL PRIMARY KEY,
    property_id INTEGER REFERENCES properties(id),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,2),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX idx_property_analytics_property_id ON property_analytics(property_id);
"""

DOWN_SQL = """
DROP TABLE IF EXISTS property_analytics;
"""
```

### 4. Read Replica Management (`read_replica_manager.py`)

**Purpose**: Implements intelligent read/write splitting with load balancing and lag monitoring.

**Query Routing Logic**:
```
Query Analysis → Query Type Detection → Replica Selection → Load Balancing → Execution
```

**Load Balancing Strategies**:
- Round Robin
- Weighted Round Robin
- Least Connections
- Least Response Time
- Geographic Distribution

**Monitoring Metrics**:
- Replication lag: < 30 seconds (warning), < 60 seconds (critical)
- Read replica availability: > 99.9%
- Query distribution: 70% reads, 30% writes
- Failover time: < 5 seconds

**Replica Configuration**:
```python
replica_config = ReplicaConfig(
    replica_id="read_replica_us_east",
    database_config=read_db_config,
    weight=1.0,
    tags=["analytics", "reporting"],
    max_lag_seconds=30.0,
    purpose=["read", "analytics"]
)
```

### 5. Data Archival Strategy (`data_archival_strategy.py`)

**Purpose**: Implements intelligent data lifecycle management with cold storage integration.

**Retention Policies**:
- Financial Data: 7 years (SOX compliance)
- Operational Data: 3 years 
- Analytics Data: 1 year
- Log Data: 90 days
- Cache Data: 30 days

**Archival Process**:
```
Data Identification → Compression → Storage Upload → Database Cleanup → Verification
```

**Storage Backends**:
- AWS S3 (with Glacier for long-term storage)
- Google Cloud Storage
- Local filesystem (for development)
- Azure Blob Storage (planned)

**Compliance Features**:
- Audit trails for all archival operations
- Integrity verification with checksums
- Encrypted storage
- Restoration capabilities
- Compliance reporting

## Performance Benchmarks

### Database Performance
- **Connection Pool**: 
  - Pool acquisition: < 10ms (P95)
  - Pool utilization: 60-80% optimal
  - Max connections: 100 per pool

- **Query Performance**:
  - Simple queries: < 50ms (P95)
  - Complex queries: < 500ms (P95)
  - Batch operations: < 2s per 1000 rows

### Caching Performance
- **L1 Cache**:
  - Hit ratio: 60-70%
  - Response time: < 1ms
  - Memory usage: < 100MB per instance

- **L2 Cache**:
  - Hit ratio: 85-95%
  - Response time: < 5ms
  - Network latency: < 2ms

### Read Replica Performance
- **Load Distribution**:
  - Read queries: 70-80% to replicas
  - Write queries: 100% to primary
  - Analytics queries: 90% to dedicated replicas

- **Replication Metrics**:
  - Lag monitoring: Every 30 seconds
  - Average lag: < 5 seconds
  - Failover time: < 10 seconds

## Scaling Strategies

### Horizontal Scaling

**Database Scaling**:
1. **Read Replicas**: Add replicas by region/purpose
2. **Sharding**: Partition by tenant or property
3. **Federation**: Separate by service boundaries

**Cache Scaling**:
1. **Redis Cluster**: Distributed caching
2. **Regional Caches**: Reduce latency
3. **Cache Hierarchies**: Multi-level caching

### Vertical Scaling

**Resource Optimization**:
- Connection pool tuning
- Query optimization
- Index optimization
- Memory allocation tuning

### Auto-Scaling Triggers

```yaml
scaling_triggers:
  database:
    cpu_utilization: > 70%
    connection_utilization: > 80%
    query_latency_p95: > 500ms
  
  cache:
    memory_utilization: > 80%
    hit_ratio: < 85%
    response_time_p95: > 10ms
  
  storage:
    disk_utilization: > 80%
    iops_utilization: > 70%
```

## Operational Runbooks

### Daily Operations

**Health Checks**:
```bash
# Database health
curl -X GET /api/v1/health/database

# Cache health
curl -X GET /api/v1/health/cache

# Replication status
curl -X GET /api/v1/health/replicas
```

**Monitoring Dashboards**:
- Database performance metrics
- Cache hit ratios and performance
- Replication lag monitoring
- Storage utilization trends

### Weekly Operations

**Performance Review**:
1. Analyze slow query logs
2. Review cache performance
3. Check replication health
4. Validate archival operations

**Capacity Planning**:
1. Review growth trends
2. Plan scaling activities
3. Update retention policies
4. Optimize resource allocation

### Monthly Operations

**Data Lifecycle Management**:
1. Review archival policies
2. Execute archival runs
3. Validate compliance requirements
4. Clean up expired data

**Security Audits**:
1. Review access logs
2. Validate encryption status
3. Check compliance reports
4. Update security policies

### Incident Response

**Database Issues**:
```bash
# Check primary database
kubectl exec -it primary-db -- pg_stat_activity

# Failover to replica
kubectl patch deployment primary-db --type='merge' -p='{"spec":{"replicas":0}}'
kubectl patch deployment failover-db --type='merge' -p='{"spec":{"replicas":1}}'

# Monitor replication lag
watch -n 5 'psql -h replica-db -c "SELECT extract(epoch from now() - pg_last_xact_replay_timestamp())"'
```

**Cache Issues**:
```bash
# Clear cache
redis-cli FLUSHALL

# Restart cache warming
curl -X POST /api/v1/cache/warm

# Monitor cache performance
redis-cli INFO stats
```

**Replication Issues**:
```bash
# Check replication status
curl -X GET /api/v1/replicas/status

# Force failover
curl -X POST /api/v1/replicas/failover

# Restart replication
kubectl restart deployment read-replica
```

## Zero-Downtime Deployment Strategy

### Database Migrations

**Blue-Green Migration**:
1. Apply schema changes to green environment
2. Run data migrations in batches
3. Validate data integrity
4. Switch traffic to green environment
5. Decommission blue environment

**Rolling Updates**:
1. Apply backwards-compatible changes
2. Deploy application updates
3. Apply forward-only changes
4. Validate system health

### Application Deployment

**Canary Deployments**:
```yaml
deployment_strategy:
  canary:
    steps:
      - weight: 10
        pause: 300s
      - weight: 50
        pause: 600s
      - weight: 100
```

**Circuit Breaker Configuration**:
```python
circuit_breaker_config = {
    "failure_threshold": 5,
    "recovery_timeout": 60,
    "success_threshold": 3
}
```

## Security Considerations

### Data Encryption
- **At Rest**: AES-256 encryption for all stored data
- **In Transit**: TLS 1.3 for all database connections
- **Key Management**: AWS KMS / HashiCorp Vault integration

### Access Control
- **Database**: Role-based access with minimal privileges
- **Cache**: Redis AUTH with rotating passwords
- **Storage**: IAM roles with temporary credentials

### Audit Logging
- All database operations logged
- Cache access patterns monitored
- Archive operations fully audited
- Compliance reports generated monthly

## Integration with RentVine API

### Data Synchronization
```python
# Automatic cache invalidation on RentVine updates
@cache_invalidate_on_update("properties")
async def update_property(property_id: str, updates: Dict):
    # Update via RentVine API
    result = await rentvine_client.update_property(property_id, updates)
    
    # Cache is automatically invalidated
    return result

# Intelligent caching for frequently accessed data
@cached_rentvine("properties", ttl=1800)
async def get_property(property_id: str):
    return await rentvine_client.get_property(property_id)
```

### Webhook Integration
```python
# Real-time cache invalidation via webhooks
async def handle_rentvine_webhook(webhook_data: Dict):
    entity_type = webhook_data.get("entity_type")
    entity_id = webhook_data.get("entity_id")
    action = webhook_data.get("action")
    
    if action in ["update", "delete"]:
        await cache_manager.invalidate_rentvine_data(entity_type, entity_id)
    
    # Warm cache for new entities
    if action == "create":
        await cache_manager.warm_rentvine_cache_for_entity(entity_type, entity_id)
```

## Monitoring and Alerting

### Key Metrics
```yaml
database_metrics:
  - connection_pool_utilization
  - query_response_time_p95
  - active_connections
  - lock_wait_time
  - transaction_duration

cache_metrics:
  - hit_ratio_l1
  - hit_ratio_l2
  - memory_usage
  - eviction_rate
  - response_time

replication_metrics:
  - lag_seconds
  - replica_availability
  - failover_count
  - query_distribution

archival_metrics:
  - archival_success_rate
  - storage_usage
  - restoration_time
  - compliance_status
```

### Alert Thresholds
```yaml
alerts:
  database:
    connection_pool_utilization: > 80%
    query_response_time_p95: > 500ms
    replica_lag: > 30s
  
  cache:
    hit_ratio: < 85%
    memory_usage: > 90%
    response_time_p95: > 10ms
  
  storage:
    disk_usage: > 80%
    archival_failures: > 5%
    restoration_time: > 60s
```

## Future Enhancements

### Planned Features
1. **Multi-Region Deployment**: Global data distribution
2. **Real-time Analytics**: Stream processing for operational insights
3. **Machine Learning Integration**: Predictive caching and optimization
4. **Event Sourcing**: Complete audit trail with event replay
5. **GraphQL Integration**: Unified data access layer

### Technology Roadmap
- **2024 Q1**: Multi-region read replicas
- **2024 Q2**: Advanced caching algorithms
- **2024 Q3**: ML-powered query optimization
- **2024 Q4**: Event sourcing implementation

## Conclusion

The Aictive Platform Data Layer provides a robust, scalable, and maintainable foundation for the property management system. With comprehensive monitoring, automatic scaling, and zero-downtime deployment capabilities, this architecture ensures reliable service delivery while maintaining optimal performance and compliance requirements.

The integration with RentVine APIs and webhook systems is seamless, providing real-time data synchronization and intelligent caching strategies that enhance user experience while reducing API load and costs.

For operational support and detailed implementation guidance, refer to the individual component documentation and the monitoring dashboards provided with the system.