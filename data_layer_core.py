"""
Comprehensive Database Connection Management and Optimization for Aictive Platform
Provides connection pooling, async management, query optimization, and health monitoring
"""

import asyncio
import logging
import time
from typing import Dict, List, Any, Optional, Tuple, Union, AsyncContextManager
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
from contextlib import asynccontextmanager

import asyncpg
import aiomysql
import aioredis
from tenacity import retry, stop_after_attempt, wait_exponential

from config import settings

logger = logging.getLogger(__name__)


class DatabaseType(Enum):
    """Supported database types"""
    POSTGRESQL = "postgresql"
    MYSQL = "mysql"
    REDIS = "redis"


class ConnectionStatus(Enum):
    """Connection pool status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    MAINTENANCE = "maintenance"


@dataclass
class DatabaseConfig:
    """Database connection configuration"""
    host: str
    port: int
    database: str
    username: str
    password: str
    db_type: DatabaseType
    min_connections: int = 5
    max_connections: int = 20
    connection_timeout: int = 30
    query_timeout: int = 60
    pool_recycle: int = 3600  # 1 hour
    ssl_mode: str = "prefer"
    charset: str = "utf8mb4"
    autocommit: bool = True
    enable_monitoring: bool = True


@dataclass
class QueryMetrics:
    """Query performance metrics"""
    query_hash: str
    execution_time: float
    rows_affected: int
    timestamp: datetime
    table_names: List[str] = field(default_factory=list)
    connection_id: Optional[str] = None
    was_cached: bool = False


@dataclass
class ConnectionPoolMetrics:
    """Connection pool performance metrics"""
    active_connections: int = 0
    idle_connections: int = 0
    total_connections: int = 0
    connections_created: int = 0
    connections_closed: int = 0
    connection_errors: int = 0
    query_count: int = 0
    avg_query_time: float = 0.0
    slow_queries: int = 0
    cache_hit_ratio: float = 0.0
    last_health_check: Optional[datetime] = None
    status: ConnectionStatus = ConnectionStatus.HEALTHY


class QueryOptimizer:
    """Query analysis and optimization"""
    
    def __init__(self):
        self.query_cache: Dict[str, Dict] = {}
        self.slow_query_threshold = 1.0  # seconds
        self.table_stats: Dict[str, Dict] = {}
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query for optimization opportunities"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        
        analysis = {
            "hash": query_hash,
            "type": self._get_query_type(query),
            "tables": self._extract_table_names(query),
            "has_where": "WHERE" in query.upper(),
            "has_index_hints": "USE INDEX" in query.upper() or "FORCE INDEX" in query.upper(),
            "has_joins": any(join in query.upper() for join in ["JOIN", "LEFT JOIN", "RIGHT JOIN", "INNER JOIN"]),
            "has_subquery": "(" in query and "SELECT" in query.upper(),
            "estimated_complexity": self._estimate_complexity(query)
        }
        
        # Add optimization suggestions
        analysis["suggestions"] = self._get_optimization_suggestions(query, analysis)
        
        return analysis
    
    def _get_query_type(self, query: str) -> str:
        """Determine query type"""
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return "SELECT"
        elif query_upper.startswith("INSERT"):
            return "INSERT"
        elif query_upper.startswith("UPDATE"):
            return "UPDATE"
        elif query_upper.startswith("DELETE"):
            return "DELETE"
        else:
            return "OTHER"
    
    def _extract_table_names(self, query: str) -> List[str]:
        """Extract table names from query"""
        # Simple table name extraction (could be enhanced with proper SQL parsing)
        tables = []
        words = query.replace(",", " ").split()
        
        for i, word in enumerate(words):
            if word.upper() in ["FROM", "JOIN", "UPDATE", "INTO"]:
                if i + 1 < len(words):
                    table = words[i + 1].strip("()`;").split(".")[- 1]
                    if table and table not in tables:
                        tables.append(table)
        
        return tables
    
    def _estimate_complexity(self, query: str) -> str:
        """Estimate query complexity"""
        score = 0
        query_upper = query.upper()
        
        # Basic scoring
        if "JOIN" in query_upper:
            score += 2
        if "SUBQUERY" in query_upper or "(" in query:
            score += 3
        if "GROUP BY" in query_upper:
            score += 1
        if "ORDER BY" in query_upper:
            score += 1
        if "HAVING" in query_upper:
            score += 2
        
        if score >= 6:
            return "HIGH"
        elif score >= 3:
            return "MEDIUM"
        else:
            return "LOW"
    
    def _get_optimization_suggestions(self, query: str, analysis: Dict) -> List[str]:
        """Generate optimization suggestions"""
        suggestions = []
        
        if not analysis["has_where"] and analysis["type"] == "SELECT":
            suggestions.append("Consider adding WHERE clause to limit results")
        
        if len(analysis["tables"]) > 3:
            suggestions.append("Query involves many tables - consider breaking into smaller queries")
        
        if analysis["estimated_complexity"] == "HIGH":
            suggestions.append("Complex query detected - consider query optimization")
        
        return suggestions


class DatabaseHealthMonitor:
    """Monitor database health and performance"""
    
    def __init__(self):
        self.health_checks: Dict[str, Dict] = {}
        self.alert_thresholds = {
            "connection_usage": 0.8,  # 80%
            "query_time": 5.0,  # 5 seconds
            "error_rate": 0.1,  # 10%
            "memory_usage": 0.9  # 90%
        }
    
    async def check_database_health(self, pool: Any, db_name: str) -> Dict[str, Any]:
        """Comprehensive database health check"""
        start_time = time.time()
        
        health_status = {
            "database": db_name,
            "timestamp": datetime.utcnow(),
            "status": "healthy",
            "checks": {},
            "metrics": {},
            "alerts": []
        }
        
        try:
            # Connection test
            async with pool.acquire() as conn:
                # Basic connectivity
                await conn.execute("SELECT 1")
                health_status["checks"]["connectivity"] = True
                
                # Response time
                query_start = time.time()
                await conn.execute("SELECT NOW()")
                response_time = time.time() - query_start
                health_status["metrics"]["response_time"] = response_time
                
                if response_time > self.alert_thresholds["query_time"]:
                    health_status["alerts"].append(f"High response time: {response_time:.3f}s")
                
                # Database-specific checks
                if hasattr(conn, 'get_server_version'):  # PostgreSQL
                    health_status["checks"]["version"] = await self._check_postgresql_health(conn)
                else:  # MySQL
                    health_status["checks"]["version"] = await self._check_mysql_health(conn)
        
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["checks"]["connectivity"] = False
            health_status["alerts"].append(f"Connection failed: {str(e)}")
            logger.error(f"Database health check failed for {db_name}: {str(e)}")
        
        # Check pool metrics
        pool_metrics = await self._get_pool_metrics(pool)
        health_status["metrics"].update(pool_metrics)
        
        # Evaluate overall health
        if health_status["alerts"]:
            health_status["status"] = "degraded" if health_status["checks"]["connectivity"] else "unhealthy"
        
        execution_time = time.time() - start_time
        health_status["metrics"]["health_check_time"] = execution_time
        
        # Store health check result
        self.health_checks[db_name] = health_status
        
        return health_status
    
    async def _check_postgresql_health(self, conn) -> Dict[str, Any]:
        """PostgreSQL-specific health checks"""
        checks = {}
        
        try:
            # Version info
            version_result = await conn.fetchrow("SELECT version()")
            checks["version"] = version_result["version"] if version_result else "Unknown"
            
            # Active connections
            active_conn_result = await conn.fetchrow(
                "SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active'"
            )
            checks["active_connections"] = active_conn_result["active_connections"] if active_conn_result else 0
            
            # Database size
            size_result = await conn.fetchrow(
                "SELECT pg_size_pretty(pg_database_size(current_database())) as size"
            )
            checks["database_size"] = size_result["size"] if size_result else "Unknown"
            
        except Exception as e:
            logger.warning(f"PostgreSQL health check error: {str(e)}")
            checks["error"] = str(e)
        
        return checks
    
    async def _check_mysql_health(self, conn) -> Dict[str, Any]:
        """MySQL-specific health checks"""
        checks = {}
        
        try:
            # Version info
            version_result = await conn.execute("SELECT VERSION() as version")
            checks["version"] = version_result if version_result else "Unknown"
            
            # Show status
            status_result = await conn.execute("SHOW STATUS LIKE 'Threads_connected'")
            checks["active_connections"] = status_result if status_result else 0
            
        except Exception as e:
            logger.warning(f"MySQL health check error: {str(e)}")
            checks["error"] = str(e)
        
        return checks
    
    async def _get_pool_metrics(self, pool: Any) -> Dict[str, Any]:
        """Extract pool metrics"""
        try:
            if hasattr(pool, '_holders'):  # asyncpg pool
                return {
                    "pool_size": pool._size,
                    "pool_max_size": pool._maxsize,
                    "pool_free_size": pool._pool.qsize() if hasattr(pool._pool, 'qsize') else 0
                }
            elif hasattr(pool, '_size'):  # aiomysql pool
                return {
                    "pool_size": pool.size,
                    "pool_max_size": pool.maxsize,
                    "pool_free_size": pool.freesize
                }
        except Exception as e:
            logger.warning(f"Could not get pool metrics: {str(e)}")
        
        return {"pool_metrics_error": "Unable to retrieve"}


class AsyncDatabaseManager:
    """Comprehensive async database manager"""
    
    def __init__(self):
        self.pools: Dict[str, Any] = {}
        self.configs: Dict[str, DatabaseConfig] = {}
        self.metrics: Dict[str, ConnectionPoolMetrics] = {}
        self.health_monitor = DatabaseHealthMonitor()
        self.query_optimizer = QueryOptimizer()
        self.failover_configs: Dict[str, List[DatabaseConfig]] = {}
        self._locks: Dict[str, asyncio.Lock] = {}
        
        # Start background monitoring
        asyncio.create_task(self._background_health_monitoring())
        asyncio.create_task(self._background_metrics_collection())
    
    async def add_database(
        self,
        name: str,
        config: DatabaseConfig,
        failover_configs: Optional[List[DatabaseConfig]] = None
    ) -> None:
        """Add database configuration and create connection pool"""
        self.configs[name] = config
        self.metrics[name] = ConnectionPoolMetrics()
        self._locks[name] = asyncio.Lock()
        
        if failover_configs:
            self.failover_configs[name] = failover_configs
        
        # Create initial connection pool
        await self._create_pool(name, config)
        
        logger.info(f"Added database '{name}' with {config.db_type.value} backend")
    
    async def _create_pool(self, name: str, config: DatabaseConfig) -> Any:
        """Create connection pool for specific database"""
        try:
            if config.db_type == DatabaseType.POSTGRESQL:
                pool = await asyncpg.create_pool(
                    host=config.host,
                    port=config.port,
                    database=config.database,
                    user=config.username,
                    password=config.password,
                    min_size=config.min_connections,
                    max_size=config.max_connections,
                    command_timeout=config.query_timeout,
                    server_settings={
                        'application_name': 'aictive_platform'
                    }
                )
            
            elif config.db_type == DatabaseType.MYSQL:
                pool = await aiomysql.create_pool(
                    host=config.host,
                    port=config.port,
                    db=config.database,
                    user=config.username,
                    password=config.password,
                    minsize=config.min_connections,
                    maxsize=config.max_connections,
                    charset=config.charset,
                    autocommit=config.autocommit
                )
            
            else:
                raise ValueError(f"Unsupported database type: {config.db_type}")
            
            self.pools[name] = pool
            self.metrics[name].status = ConnectionStatus.HEALTHY
            self.metrics[name].total_connections = config.max_connections
            
            logger.info(f"Created connection pool for '{name}' ({config.db_type.value})")
            return pool
            
        except Exception as e:
            logger.error(f"Failed to create pool for '{name}': {str(e)}")
            self.metrics[name].status = ConnectionStatus.UNHEALTHY
            self.metrics[name].connection_errors += 1
            raise
    
    @asynccontextmanager
    async def get_connection(self, db_name: str) -> AsyncContextManager:
        """Get database connection from pool with automatic failover"""
        if db_name not in self.pools:
            raise ValueError(f"Database '{db_name}' not configured")
        
        pool = self.pools[db_name]
        metrics = self.metrics[db_name]
        
        # Check pool health
        if metrics.status == ConnectionStatus.UNHEALTHY:
            # Attempt failover
            if db_name in self.failover_configs:
                await self._attempt_failover(db_name)
                pool = self.pools[db_name]
        
        try:
            async with pool.acquire() as connection:
                metrics.active_connections += 1
                connection_wrapper = DatabaseConnectionWrapper(
                    connection, 
                    db_name, 
                    self.query_optimizer,
                    metrics
                )
                yield connection_wrapper
                
        except Exception as e:
            metrics.connection_errors += 1
            logger.error(f"Connection error for '{db_name}': {str(e)}")
            raise
        finally:
            metrics.active_connections = max(0, metrics.active_connections - 1)
    
    async def _attempt_failover(self, db_name: str) -> None:
        """Attempt failover to backup database"""
        if db_name not in self.failover_configs:
            return
        
        async with self._locks[db_name]:
            logger.warning(f"Attempting failover for database '{db_name}'")
            
            for failover_config in self.failover_configs[db_name]:
                try:
                    # Close existing unhealthy pool
                    if db_name in self.pools:
                        await self.pools[db_name].close()
                    
                    # Create new pool with failover config
                    await self._create_pool(db_name, failover_config)
                    
                    # Test the connection
                    async with self.get_connection(db_name) as conn:
                        await conn.execute("SELECT 1")
                    
                    logger.info(f"Successfully failed over '{db_name}' to {failover_config.host}")
                    return
                    
                except Exception as e:
                    logger.error(f"Failover attempt failed for {failover_config.host}: {str(e)}")
                    continue
            
            logger.error(f"All failover attempts failed for '{db_name}'")
    
    async def execute_query(
        self,
        db_name: str,
        query: str,
        params: Optional[Tuple] = None,
        fetch_mode: str = "none"  # none, one, all
    ) -> Any:
        """Execute query with monitoring and optimization"""
        start_time = time.time()
        
        # Analyze query
        analysis = self.query_optimizer.analyze_query(query)
        
        async with self.get_connection(db_name) as conn:
            try:
                result = await conn.execute_with_monitoring(query, params, fetch_mode)
                
                # Record metrics
                execution_time = time.time() - start_time
                metrics = QueryMetrics(
                    query_hash=analysis["hash"],
                    execution_time=execution_time,
                    rows_affected=result.get("rows_affected", 0) if isinstance(result, dict) else 0,
                    timestamp=datetime.utcnow(),
                    table_names=analysis["tables"]
                )
                
                # Update pool metrics
                pool_metrics = self.metrics[db_name]
                pool_metrics.query_count += 1
                pool_metrics.avg_query_time = (
                    (pool_metrics.avg_query_time * (pool_metrics.query_count - 1) + execution_time) 
                    / pool_metrics.query_count
                )
                
                if execution_time > self.query_optimizer.slow_query_threshold:
                    pool_metrics.slow_queries += 1
                    logger.warning(
                        f"Slow query detected ({execution_time:.3f}s): {query[:100]}..."
                    )
                
                return result
                
            except Exception as e:
                self.metrics[db_name].connection_errors += 1
                logger.error(f"Query execution failed: {str(e)}")
                raise
    
    async def _background_health_monitoring(self) -> None:
        """Background task for continuous health monitoring"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                for db_name, pool in self.pools.items():
                    if self.configs[db_name].enable_monitoring:
                        health_status = await self.health_monitor.check_database_health(pool, db_name)
                        
                        # Update metrics based on health
                        if health_status["status"] == "unhealthy":
                            self.metrics[db_name].status = ConnectionStatus.UNHEALTHY
                        elif health_status["status"] == "degraded":
                            self.metrics[db_name].status = ConnectionStatus.DEGRADED
                        else:
                            self.metrics[db_name].status = ConnectionStatus.HEALTHY
                        
                        self.metrics[db_name].last_health_check = health_status["timestamp"]
                        
            except Exception as e:
                logger.error(f"Health monitoring error: {str(e)}")
    
    async def _background_metrics_collection(self) -> None:
        """Background task for metrics collection"""
        while True:
            try:
                await asyncio.sleep(30)  # Collect every 30 seconds
                
                for db_name in self.pools:
                    # Update connection counts and other metrics
                    # This would be expanded based on specific pool implementations
                    pass
                    
            except Exception as e:
                logger.error(f"Metrics collection error: {str(e)}")
    
    async def get_metrics(self, db_name: Optional[str] = None) -> Dict[str, Any]:
        """Get performance metrics"""
        if db_name:
            if db_name in self.metrics:
                return {
                    "database": db_name,
                    "metrics": self.metrics[db_name].__dict__,
                    "health": self.health_monitor.health_checks.get(db_name, {})
                }
            else:
                raise ValueError(f"Database '{db_name}' not found")
        
        # Return all metrics
        return {
            db_name: {
                "metrics": metrics.__dict__,
                "health": self.health_monitor.health_checks.get(db_name, {})
            }
            for db_name, metrics in self.metrics.items()
        }
    
    async def close_all(self) -> None:
        """Close all database connections"""
        for db_name, pool in self.pools.items():
            try:
                await pool.close()
                logger.info(f"Closed connection pool for '{db_name}'")
            except Exception as e:
                logger.error(f"Error closing pool for '{db_name}': {str(e)}")
        
        self.pools.clear()


class DatabaseConnectionWrapper:
    """Wrapper for database connections with monitoring"""
    
    def __init__(self, connection: Any, db_name: str, optimizer: QueryOptimizer, metrics: ConnectionPoolMetrics):
        self.connection = connection
        self.db_name = db_name
        self.optimizer = optimizer
        self.metrics = metrics
    
    async def execute(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute query without fetching results"""
        return await self.execute_with_monitoring(query, params, "none")
    
    async def fetchone(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute query and fetch one result"""
        return await self.execute_with_monitoring(query, params, "one")
    
    async def fetchall(self, query: str, params: Optional[Tuple] = None) -> Any:
        """Execute query and fetch all results"""
        return await self.execute_with_monitoring(query, params, "all")
    
    async def execute_with_monitoring(
        self, 
        query: str, 
        params: Optional[Tuple] = None, 
        fetch_mode: str = "none"
    ) -> Any:
        """Execute query with performance monitoring"""
        start_time = time.time()
        
        try:
            if fetch_mode == "one":
                if hasattr(self.connection, 'fetchrow'):  # asyncpg
                    result = await self.connection.fetchrow(query, *(params or ()))
                else:  # aiomysql
                    cursor = await self.connection.cursor()
                    await cursor.execute(query, params)
                    result = await cursor.fetchone()
                    await cursor.close()
            
            elif fetch_mode == "all":
                if hasattr(self.connection, 'fetch'):  # asyncpg
                    result = await self.connection.fetch(query, *(params or ()))
                else:  # aiomysql
                    cursor = await self.connection.cursor()
                    await cursor.execute(query, params)
                    result = await cursor.fetchall()
                    await cursor.close()
            
            else:  # none
                if hasattr(self.connection, 'execute'):  # asyncpg
                    result = await self.connection.execute(query, *(params or ()))
                else:  # aiomysql
                    cursor = await self.connection.cursor()
                    await cursor.execute(query, params)
                    result = {"rows_affected": cursor.rowcount}
                    await cursor.close()
            
            execution_time = time.time() - start_time
            
            # Log slow queries
            if execution_time > self.optimizer.slow_query_threshold:
                logger.warning(
                    f"Slow query on {self.db_name} ({execution_time:.3f}s): {query[:100]}..."
                )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(
                f"Query failed on {self.db_name} after {execution_time:.3f}s: {str(e)}"
            )
            raise


# Global database manager instance
db_manager = AsyncDatabaseManager()


# Convenience functions for common operations
async def setup_databases():
    """Setup standard database connections for Aictive platform"""
    # Primary PostgreSQL database
    primary_config = DatabaseConfig(
        host=getattr(settings, 'postgres_host', 'localhost'),
        port=getattr(settings, 'postgres_port', 5432),
        database=getattr(settings, 'postgres_db', 'aictive'),
        username=getattr(settings, 'postgres_user', 'aictive'),
        password=getattr(settings, 'postgres_password', 'password'),
        db_type=DatabaseType.POSTGRESQL,
        min_connections=5,
        max_connections=20
    )
    
    # Failover PostgreSQL (if configured)
    failover_configs = []
    if hasattr(settings, 'postgres_failover_host'):
        failover_config = DatabaseConfig(
            host=settings.postgres_failover_host,
            port=getattr(settings, 'postgres_failover_port', 5432),
            database=getattr(settings, 'postgres_failover_db', 'aictive'),
            username=getattr(settings, 'postgres_failover_user', 'aictive'),
            password=getattr(settings, 'postgres_failover_password', 'password'),
            db_type=DatabaseType.POSTGRESQL,
            min_connections=3,
            max_connections=10
        )
        failover_configs.append(failover_config)
    
    await db_manager.add_database("primary", primary_config, failover_configs)
    
    # Read replica (if configured)
    if hasattr(settings, 'postgres_read_host'):
        read_config = DatabaseConfig(
            host=settings.postgres_read_host,
            port=getattr(settings, 'postgres_read_port', 5432),
            database=getattr(settings, 'postgres_read_db', 'aictive'),
            username=getattr(settings, 'postgres_read_user', 'aictive'),
            password=getattr(settings, 'postgres_read_password', 'password'),
            db_type=DatabaseType.POSTGRESQL,
            min_connections=3,
            max_connections=15
        )
        
        await db_manager.add_database("read_replica", read_config)
    
    logger.info("Database connections initialized successfully")


async def get_db_connection(db_name: str = "primary"):
    """Get database connection context manager"""
    return db_manager.get_connection(db_name)


async def execute_query(query: str, params: Optional[Tuple] = None, db_name: str = "primary"):
    """Execute query on specified database"""
    return await db_manager.execute_query(db_name, query, params)


async def get_database_metrics():
    """Get all database performance metrics"""
    return await db_manager.get_metrics()