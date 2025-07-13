"""
Read Replica Management System for Aictive Platform
Implements read/write splitting, load balancing, replication lag monitoring,
automatic failover, and query routing optimization
"""

import asyncio
import logging
import time
import random
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

from data_layer_core import DatabaseConfig, DatabaseType, db_manager, get_db_connection

logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Types of database queries"""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    ANALYTICS = "analytics"


class ReplicaStatus(Enum):
    """Read replica status"""
    HEALTHY = "healthy"
    LAGGED = "lagged"
    UNHEALTHY = "unhealthy"
    OFFLINE = "offline"
    MAINTENANCE = "maintenance"


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for read replicas"""
    ROUND_ROBIN = "round_robin"
    WEIGHTED_ROUND_ROBIN = "weighted_round_robin"
    LEAST_CONNECTIONS = "least_connections"
    LEAST_RESPONSE_TIME = "least_response_time"
    RANDOM = "random"
    GEOGRAPHICAL = "geographical"


@dataclass
class ReplicaHealth:
    """Health metrics for a read replica"""
    replica_id: str
    status: ReplicaStatus
    lag_seconds: float
    active_connections: int
    avg_response_time: float
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    last_checked: datetime
    error_count: int = 0
    uptime_percentage: float = 100.0


@dataclass
class QueryRoutingRule:
    """Rules for routing queries to specific replicas"""
    pattern: str  # SQL pattern or regex
    replica_tags: List[str]  # Tags that replica must have
    priority: int = 0  # Higher priority rules are checked first
    description: str = ""
    enabled: bool = True


@dataclass
class ReplicaConfig:
    """Configuration for a read replica"""
    replica_id: str
    database_config: DatabaseConfig
    weight: float = 1.0  # For weighted load balancing
    tags: List[str] = field(default_factory=list)  # Analytics, reporting, etc.
    max_lag_seconds: float = 30.0
    max_connections: int = 100
    geographical_location: str = ""
    purpose: List[str] = field(default_factory=list)  # read, analytics, backup


@dataclass
class QueryMetrics:
    """Metrics for query execution"""
    query_id: str
    query_type: QueryType
    replica_id: str
    execution_time: float
    rows_returned: int
    timestamp: datetime
    success: bool
    error_message: Optional[str] = None


class ReplicationLagMonitor:
    """Monitors replication lag across read replicas"""
    
    def __init__(self):
        self.lag_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        self.lag_thresholds = {
            "warning": 10.0,  # seconds
            "critical": 30.0,  # seconds
            "failover": 60.0  # seconds
        }
    
    async def check_replication_lag(self, replica_id: str, db_name: str) -> float:
        """Check replication lag for a specific replica"""
        try:
            async with get_db_connection(db_name) as conn:
                # PostgreSQL lag check
                if hasattr(conn, 'fetchrow'):  # asyncpg
                    result = await conn.fetchrow("""
                        SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) as lag_seconds
                    """)
                    lag_seconds = float(result['lag_seconds']) if result and result['lag_seconds'] else 0.0
                
                # MySQL lag check
                else:  # aiomysql
                    result = await conn.fetchone("SHOW SLAVE STATUS")
                    if result:
                        lag_seconds = float(result.get('Seconds_Behind_Master', 0) or 0)
                    else:
                        lag_seconds = 0.0
                
                # Store lag history
                now = datetime.utcnow()
                self.lag_history[replica_id].append((now, lag_seconds))
                
                # Keep only last 100 measurements
                if len(self.lag_history[replica_id]) > 100:
                    self.lag_history[replica_id] = self.lag_history[replica_id][-100:]
                
                return lag_seconds
                
        except Exception as e:
            logger.error(f"Failed to check replication lag for {replica_id}: {str(e)}")
            return float('inf')  # Treat as severely lagged
    
    def get_lag_statistics(self, replica_id: str, window_minutes: int = 60) -> Dict[str, float]:
        """Get lag statistics for a replica over a time window"""
        if replica_id not in self.lag_history:
            return {"avg": 0.0, "max": 0.0, "min": 0.0, "current": 0.0}
        
        # Filter to time window
        cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
        recent_lags = [
            lag for timestamp, lag in self.lag_history[replica_id]
            if timestamp > cutoff_time
        ]
        
        if not recent_lags:
            return {"avg": 0.0, "max": 0.0, "min": 0.0, "current": 0.0}
        
        return {
            "avg": statistics.mean(recent_lags),
            "max": max(recent_lags),
            "min": min(recent_lags),
            "current": recent_lags[-1] if recent_lags else 0.0,
            "p95": statistics.quantiles(recent_lags, n=20)[18] if len(recent_lags) > 1 else recent_lags[0]
        }
    
    def is_replica_lagged(self, replica_id: str, threshold: str = "warning") -> bool:
        """Check if replica exceeds lag threshold"""
        if replica_id not in self.lag_history or not self.lag_history[replica_id]:
            return True  # Assume lagged if no data
        
        current_lag = self.lag_history[replica_id][-1][1]
        return current_lag > self.lag_thresholds[threshold]


class QueryAnalyzer:
    """Analyzes SQL queries to determine routing strategy"""
    
    def __init__(self):
        self.read_patterns = [
            r'^\s*SELECT\s+',
            r'^\s*SHOW\s+',
            r'^\s*DESCRIBE\s+',
            r'^\s*EXPLAIN\s+',
            r'^\s*WITH\s+.*\s+SELECT\s+'
        ]
        
        self.write_patterns = [
            r'^\s*INSERT\s+',
            r'^\s*UPDATE\s+',
            r'^\s*DELETE\s+',
            r'^\s*REPLACE\s+',
            r'^\s*CREATE\s+',
            r'^\s*ALTER\s+',
            r'^\s*DROP\s+',
            r'^\s*TRUNCATE\s+'
        ]
        
        self.admin_patterns = [
            r'^\s*GRANT\s+',
            r'^\s*REVOKE\s+',
            r'^\s*SET\s+',
            r'^\s*FLUSH\s+',
            r'^\s*ANALYZE\s+',
            r'^\s*OPTIMIZE\s+'
        ]
    
    def classify_query(self, sql: str) -> QueryType:
        """Classify query type based on SQL content"""
        sql_upper = sql.strip().upper()
        
        # Check write patterns first (most restrictive)
        for pattern in self.write_patterns:
            if self._matches_pattern(pattern, sql_upper):
                return QueryType.WRITE
        
        # Check admin patterns
        for pattern in self.admin_patterns:
            if self._matches_pattern(pattern, sql_upper):
                return QueryType.ADMIN
        
        # Check read patterns
        for pattern in self.read_patterns:
            if self._matches_pattern(pattern, sql_upper):
                # Further classify reads
                if any(keyword in sql_upper for keyword in ['GROUP BY', 'AGGREGATE', 'SUM(', 'COUNT(', 'AVG(']):
                    return QueryType.ANALYTICS
                return QueryType.READ
        
        # Default to write for unknown patterns (safety first)
        return QueryType.WRITE
    
    def _matches_pattern(self, pattern: str, sql: str) -> bool:
        """Check if SQL matches pattern"""
        import re
        return bool(re.match(pattern, sql, re.IGNORECASE))
    
    def extract_table_names(self, sql: str) -> List[str]:
        """Extract table names from SQL query"""
        # Simplified implementation - could use proper SQL parser
        import re
        
        # Remove comments and normalize whitespace
        sql = re.sub(r'--.*$', '', sql, flags=re.MULTILINE)
        sql = re.sub(r'/\*.*?\*/', '', sql, flags=re.DOTALL)
        sql = ' '.join(sql.split())
        
        tables = []
        
        # Extract tables from FROM clauses
        from_matches = re.finditer(r'\bFROM\s+([^\s,()]+)', sql, re.IGNORECASE)
        for match in from_matches:
            table = match.group(1).strip('`"[]')
            if '.' in table:
                table = table.split('.')[-1]  # Remove schema prefix
            tables.append(table)
        
        # Extract tables from JOIN clauses
        join_matches = re.finditer(r'\bJOIN\s+([^\s,()]+)', sql, re.IGNORECASE)
        for match in join_matches:
            table = match.group(1).strip('`"[]')
            if '.' in table:
                table = table.split('.')[-1]
            tables.append(table)
        
        return list(set(tables))  # Remove duplicates


class LoadBalancer:
    """Load balancer for read replicas"""
    
    def __init__(self, strategy: LoadBalancingStrategy = LoadBalancingStrategy.LEAST_RESPONSE_TIME):
        self.strategy = strategy
        self.round_robin_index = 0
        self.connection_counts: Dict[str, int] = defaultdict(int)
        self.response_times: Dict[str, List[float]] = defaultdict(list)
    
    def select_replica(
        self, 
        available_replicas: List[ReplicaConfig], 
        health_status: Dict[str, ReplicaHealth],
        query_type: QueryType = QueryType.READ
    ) -> Optional[ReplicaConfig]:
        """Select best replica based on load balancing strategy"""
        
        if not available_replicas:
            return None
        
        # Filter replicas by health and suitability
        suitable_replicas = []
        for replica in available_replicas:
            health = health_status.get(replica.replica_id)
            if health and health.status in [ReplicaStatus.HEALTHY, ReplicaStatus.LAGGED]:
                # Check if replica is suitable for query type
                if self._is_replica_suitable(replica, query_type):
                    suitable_replicas.append(replica)
        
        if not suitable_replicas:
            return None
        
        # Apply load balancing strategy
        if self.strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_select(suitable_replicas)
        
        elif self.strategy == LoadBalancingStrategy.WEIGHTED_ROUND_ROBIN:
            return self._weighted_round_robin_select(suitable_replicas)
        
        elif self.strategy == LoadBalancingStrategy.LEAST_CONNECTIONS:
            return self._least_connections_select(suitable_replicas)
        
        elif self.strategy == LoadBalancingStrategy.LEAST_RESPONSE_TIME:
            return self._least_response_time_select(suitable_replicas, health_status)
        
        elif self.strategy == LoadBalancingStrategy.RANDOM:
            return random.choice(suitable_replicas)
        
        else:
            # Default to round robin
            return self._round_robin_select(suitable_replicas)
    
    def _is_replica_suitable(self, replica: ReplicaConfig, query_type: QueryType) -> bool:
        """Check if replica is suitable for query type"""
        if query_type == QueryType.ANALYTICS:
            return "analytics" in replica.tags or "read" in replica.purpose
        elif query_type == QueryType.READ:
            return "read" in replica.purpose
        else:
            return True  # All replicas can handle other types
    
    def _round_robin_select(self, replicas: List[ReplicaConfig]) -> ReplicaConfig:
        """Round robin selection"""
        replica = replicas[self.round_robin_index % len(replicas)]
        self.round_robin_index += 1
        return replica
    
    def _weighted_round_robin_select(self, replicas: List[ReplicaConfig]) -> ReplicaConfig:
        """Weighted round robin based on replica weights"""
        total_weight = sum(r.weight for r in replicas)
        random_weight = random.uniform(0, total_weight)
        
        current_weight = 0
        for replica in replicas:
            current_weight += replica.weight
            if current_weight >= random_weight:
                return replica
        
        return replicas[-1]  # Fallback
    
    def _least_connections_select(self, replicas: List[ReplicaConfig]) -> ReplicaConfig:
        """Select replica with least active connections"""
        return min(replicas, key=lambda r: self.connection_counts[r.replica_id])
    
    def _least_response_time_select(
        self, 
        replicas: List[ReplicaConfig], 
        health_status: Dict[str, ReplicaHealth]
    ) -> ReplicaConfig:
        """Select replica with best response time"""
        return min(
            replicas, 
            key=lambda r: health_status.get(r.replica_id, ReplicaHealth(
                replica_id=r.replica_id,
                status=ReplicaStatus.UNHEALTHY,
                lag_seconds=float('inf'),
                active_connections=0,
                avg_response_time=float('inf'),
                cpu_usage=100.0,
                memory_usage=100.0,
                disk_usage=100.0,
                last_checked=datetime.utcnow()
            )).avg_response_time
        )
    
    def record_connection(self, replica_id: str, connected: bool):
        """Record connection event"""
        if connected:
            self.connection_counts[replica_id] += 1
        else:
            self.connection_counts[replica_id] = max(0, self.connection_counts[replica_id] - 1)
    
    def record_response_time(self, replica_id: str, response_time: float):
        """Record response time for replica"""
        self.response_times[replica_id].append(response_time)
        # Keep only last 100 measurements
        if len(self.response_times[replica_id]) > 100:
            self.response_times[replica_id] = self.response_times[replica_id][-100:]


class ReadReplicaManager:
    """Main read replica management system"""
    
    def __init__(self):
        self.replicas: Dict[str, ReplicaConfig] = {}
        self.health_status: Dict[str, ReplicaHealth] = {}
        self.lag_monitor = ReplicationLagMonitor()
        self.query_analyzer = QueryAnalyzer()
        self.load_balancer = LoadBalancer()
        self.routing_rules: List[QueryRoutingRule] = []
        self.query_metrics: List[QueryMetrics] = []
        self.failover_primary_id: Optional[str] = None
        
        # Start background monitoring
        self._monitoring_task = None
    
    async def initialize(self):
        """Initialize the read replica manager"""
        self._monitoring_task = asyncio.create_task(self._background_monitoring())
        logger.info("Read replica manager initialized")
    
    async def shutdown(self):
        """Shutdown the read replica manager"""
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("Read replica manager shutdown complete")
    
    def add_replica(self, replica_config: ReplicaConfig):
        """Add a read replica to the management system"""
        self.replicas[replica_config.replica_id] = replica_config
        
        # Initialize health status
        self.health_status[replica_config.replica_id] = ReplicaHealth(
            replica_id=replica_config.replica_id,
            status=ReplicaStatus.HEALTHY,
            lag_seconds=0.0,
            active_connections=0,
            avg_response_time=0.0,
            cpu_usage=0.0,
            memory_usage=0.0,
            disk_usage=0.0,
            last_checked=datetime.utcnow()
        )
        
        logger.info(f"Added read replica: {replica_config.replica_id}")
    
    def remove_replica(self, replica_id: str):
        """Remove a read replica from management"""
        if replica_id in self.replicas:
            del self.replicas[replica_id]
        if replica_id in self.health_status:
            del self.health_status[replica_id]
        logger.info(f"Removed read replica: {replica_id}")
    
    def add_routing_rule(self, rule: QueryRoutingRule):
        """Add a query routing rule"""
        self.routing_rules.append(rule)
        # Sort by priority (highest first)
        self.routing_rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"Added routing rule: {rule.description}")
    
    async def route_query(
        self, 
        sql: str, 
        params: Optional[Tuple] = None,
        prefer_replica_tags: Optional[List[str]] = None
    ) -> Tuple[str, Any]:
        """Route query to appropriate database (primary or replica)"""
        
        # Classify query
        query_type = self.query_analyzer.classify_query(sql)
        
        # Route writes and admin queries to primary
        if query_type in [QueryType.WRITE, QueryType.ADMIN]:
            return "primary", await self._execute_on_primary(sql, params)
        
        # Find suitable replicas for reads
        suitable_replicas = await self._find_suitable_replicas(sql, query_type, prefer_replica_tags)
        
        if not suitable_replicas:
            # Fallback to primary
            logger.warning("No suitable replicas available, routing to primary")
            return "primary", await self._execute_on_primary(sql, params)
        
        # Select best replica
        selected_replica = self.load_balancer.select_replica(
            suitable_replicas, 
            self.health_status, 
            query_type
        )
        
        if not selected_replica:
            return "primary", await self._execute_on_primary(sql, params)
        
        # Execute on selected replica
        try:
            start_time = time.time()
            result = await self._execute_on_replica(selected_replica.replica_id, sql, params)
            execution_time = time.time() - start_time
            
            # Record metrics
            self._record_query_metrics(
                query_type, selected_replica.replica_id, execution_time, True
            )
            
            return selected_replica.replica_id, result
            
        except Exception as e:
            logger.error(f"Query failed on replica {selected_replica.replica_id}: {str(e)}")
            
            # Record failure and try primary
            self._record_query_metrics(
                query_type, selected_replica.replica_id, 0, False, str(e)
            )
            
            return "primary", await self._execute_on_primary(sql, params)
    
    async def _find_suitable_replicas(
        self, 
        sql: str, 
        query_type: QueryType,
        prefer_replica_tags: Optional[List[str]] = None
    ) -> List[ReplicaConfig]:
        """Find replicas suitable for the query"""
        
        suitable_replicas = []
        
        # Check routing rules first
        for rule in self.routing_rules:
            if rule.enabled and self._query_matches_rule(sql, rule):
                # Find replicas with required tags
                for replica in self.replicas.values():
                    if any(tag in replica.tags for tag in rule.replica_tags):
                        health = self.health_status.get(replica.replica_id)
                        if health and health.status != ReplicaStatus.OFFLINE:
                            suitable_replicas.append(replica)
                
                if suitable_replicas:
                    return suitable_replicas
        
        # Default replica selection
        for replica in self.replicas.values():
            health = self.health_status.get(replica.replica_id)
            
            if not health or health.status == ReplicaStatus.OFFLINE:
                continue
            
            # Check lag
            if health.lag_seconds > replica.max_lag_seconds:
                continue
            
            # Check preferred tags
            if prefer_replica_tags:
                if not any(tag in replica.tags for tag in prefer_replica_tags):
                    continue
            
            # Check query type suitability
            if self.load_balancer._is_replica_suitable(replica, query_type):
                suitable_replicas.append(replica)
        
        return suitable_replicas
    
    def _query_matches_rule(self, sql: str, rule: QueryRoutingRule) -> bool:
        """Check if query matches routing rule"""
        import re
        try:
            return bool(re.search(rule.pattern, sql, re.IGNORECASE))
        except re.error:
            logger.warning(f"Invalid regex pattern in routing rule: {rule.pattern}")
            return False
    
    async def _execute_on_primary(self, sql: str, params: Optional[Tuple] = None) -> Any:
        """Execute query on primary database"""
        async with get_db_connection("primary") as conn:
            if params:
                return await conn.fetchall(sql, params)
            else:
                return await conn.fetchall(sql)
    
    async def _execute_on_replica(
        self, 
        replica_id: str, 
        sql: str, 
        params: Optional[Tuple] = None
    ) -> Any:
        """Execute query on specific replica"""
        self.load_balancer.record_connection(replica_id, True)
        try:
            async with get_db_connection(replica_id) as conn:
                if params:
                    return await conn.fetchall(sql, params)
                else:
                    return await conn.fetchall(sql)
        finally:
            self.load_balancer.record_connection(replica_id, False)
    
    def _record_query_metrics(
        self, 
        query_type: QueryType, 
        replica_id: str, 
        execution_time: float,
        success: bool,
        error_message: Optional[str] = None
    ):
        """Record query execution metrics"""
        
        metric = QueryMetrics(
            query_id=f"{int(time.time())}_{replica_id}",
            query_type=query_type,
            replica_id=replica_id,
            execution_time=execution_time,
            rows_returned=0,  # Would need to extract from result
            timestamp=datetime.utcnow(),
            success=success,
            error_message=error_message
        )
        
        self.query_metrics.append(metric)
        
        # Keep only last 1000 metrics
        if len(self.query_metrics) > 1000:
            self.query_metrics = self.query_metrics[-1000:]
        
        # Update load balancer metrics
        if success:
            self.load_balancer.record_response_time(replica_id, execution_time)
    
    async def _background_monitoring(self):
        """Background task for monitoring replica health"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                for replica_id, replica_config in self.replicas.items():
                    await self._check_replica_health(replica_id, replica_config)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background monitoring: {str(e)}")
    
    async def _check_replica_health(self, replica_id: str, replica_config: ReplicaConfig):
        """Check health of a specific replica"""
        try:
            start_time = time.time()
            
            # Check replication lag
            lag_seconds = await self.lag_monitor.check_replication_lag(replica_id, replica_id)
            
            # Simple connectivity and response time check
            async with get_db_connection(replica_id) as conn:
                await conn.execute("SELECT 1")
            
            response_time = time.time() - start_time
            
            # Determine status
            if lag_seconds == float('inf'):
                status = ReplicaStatus.OFFLINE
            elif lag_seconds > replica_config.max_lag_seconds:
                status = ReplicaStatus.LAGGED
            else:
                status = ReplicaStatus.HEALTHY
            
            # Update health status
            health = self.health_status[replica_id]
            health.status = status
            health.lag_seconds = lag_seconds
            health.avg_response_time = response_time
            health.last_checked = datetime.utcnow()
            health.error_count = 0  # Reset on successful check
            
        except Exception as e:
            logger.error(f"Health check failed for replica {replica_id}: {str(e)}")
            
            # Update error status
            health = self.health_status[replica_id]
            health.status = ReplicaStatus.UNHEALTHY
            health.error_count += 1
            health.last_checked = datetime.utcnow()
            
            # Mark as offline after multiple failures
            if health.error_count >= 3:
                health.status = ReplicaStatus.OFFLINE
    
    def get_replica_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all replicas"""
        status = {
            "replicas": {},
            "summary": {
                "total_replicas": len(self.replicas),
                "healthy_replicas": 0,
                "lagged_replicas": 0,
                "unhealthy_replicas": 0,
                "offline_replicas": 0
            },
            "load_balancing": {
                "strategy": self.load_balancer.strategy.value,
                "connection_counts": dict(self.load_balancer.connection_counts)
            },
            "recent_queries": len(self.query_metrics),
            "routing_rules": len(self.routing_rules)
        }
        
        for replica_id, replica_config in self.replicas.items():
            health = self.health_status.get(replica_id)
            lag_stats = self.lag_monitor.get_lag_statistics(replica_id)
            
            status["replicas"][replica_id] = {
                "config": {
                    "weight": replica_config.weight,
                    "tags": replica_config.tags,
                    "max_lag_seconds": replica_config.max_lag_seconds,
                    "purpose": replica_config.purpose
                },
                "health": {
                    "status": health.status.value if health else "unknown",
                    "lag_seconds": health.lag_seconds if health else 0,
                    "avg_response_time": health.avg_response_time if health else 0,
                    "error_count": health.error_count if health else 0,
                    "last_checked": health.last_checked.isoformat() if health else None
                },
                "lag_statistics": lag_stats
            }
            
            # Update summary counts
            if health:
                if health.status == ReplicaStatus.HEALTHY:
                    status["summary"]["healthy_replicas"] += 1
                elif health.status == ReplicaStatus.LAGGED:
                    status["summary"]["lagged_replicas"] += 1
                elif health.status == ReplicaStatus.UNHEALTHY:
                    status["summary"]["unhealthy_replicas"] += 1
                elif health.status == ReplicaStatus.OFFLINE:
                    status["summary"]["offline_replicas"] += 1
        
        return status
    
    def get_query_analytics(self, hours: int = 24) -> Dict[str, Any]:
        """Get query analytics for the specified time period"""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_metrics = [
            m for m in self.query_metrics 
            if m.timestamp > cutoff_time
        ]
        
        if not recent_metrics:
            return {"message": "No query data available"}
        
        # Analytics by replica
        replica_stats = defaultdict(lambda: {
            "query_count": 0,
            "avg_response_time": 0.0,
            "success_rate": 0.0,
            "query_types": defaultdict(int)
        })
        
        for metric in recent_metrics:
            stats = replica_stats[metric.replica_id]
            stats["query_count"] += 1
            stats["avg_response_time"] += metric.execution_time
            stats["query_types"][metric.query_type.value] += 1
            
            if metric.success:
                stats["success_rate"] += 1
        
        # Calculate averages
        for replica_id, stats in replica_stats.items():
            if stats["query_count"] > 0:
                stats["avg_response_time"] /= stats["query_count"]
                stats["success_rate"] = (stats["success_rate"] / stats["query_count"]) * 100
        
        return {
            "period_hours": hours,
            "total_queries": len(recent_metrics),
            "replica_analytics": dict(replica_stats),
            "query_type_distribution": {
                query_type.value: len([m for m in recent_metrics if m.query_type == query_type])
                for query_type in QueryType
            }
        }


# Global replica manager
replica_manager: Optional[ReadReplicaManager] = None


async def initialize_replica_manager() -> ReadReplicaManager:
    """Initialize the global read replica manager"""
    global replica_manager
    
    replica_manager = ReadReplicaManager()
    await replica_manager.initialize()
    
    return replica_manager


async def add_read_replica(
    replica_id: str,
    database_config: DatabaseConfig,
    weight: float = 1.0,
    tags: Optional[List[str]] = None,
    max_lag_seconds: float = 30.0
):
    """Add a read replica to the system"""
    if not replica_manager:
        raise RuntimeError("Replica manager not initialized")
    
    replica_config = ReplicaConfig(
        replica_id=replica_id,
        database_config=database_config,
        weight=weight,
        tags=tags or [],
        max_lag_seconds=max_lag_seconds,
        purpose=["read"]
    )
    
    replica_manager.add_replica(replica_config)


async def execute_read_query(sql: str, params: Optional[Tuple] = None, prefer_tags: Optional[List[str]] = None):
    """Execute a read query with automatic replica routing"""
    if not replica_manager:
        raise RuntimeError("Replica manager not initialized")
    
    return await replica_manager.route_query(sql, params, prefer_tags)


def get_replica_status():
    """Get status of all read replicas"""
    if not replica_manager:
        raise RuntimeError("Replica manager not initialized")
    
    return replica_manager.get_replica_status()