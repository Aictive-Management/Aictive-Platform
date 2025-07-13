"""
Data Layer Integration Example for Aictive Platform
Demonstrates how all data layer components work together with RentVine API
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Import all data layer components
from data_layer_core import (
    DatabaseConfig, DatabaseType, setup_databases, 
    get_db_connection, execute_query, get_database_metrics
)
from redis_caching_strategy import (
    StorageConfig, StorageProvider, initialize_cache_system, 
    cache_manager, cached_rentvine, cache_invalidate_on_update
)
from database_migration_system import (
    initialize_migration_system, run_migrations, get_migration_status
)
from read_replica_manager import (
    initialize_replica_manager, add_read_replica, 
    execute_read_query, get_replica_status
)
from data_archival_strategy import (
    initialize_archival_system, run_archival, get_archival_status
)

# Import existing components
from rentvine_api_client import RentVineAPIClient, RentVineConfig
from config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AictiveDataLayerManager:
    """Main data layer manager that orchestrates all components"""
    
    def __init__(self):
        self.initialized = False
        self.rentvine_client = None
        self.health_status = {}
    
    async def initialize_all_systems(self):
        """Initialize all data layer components"""
        logger.info("Initializing Aictive Data Layer...")
        
        try:
            # 1. Initialize core database connections
            await self._setup_databases()
            
            # 2. Initialize cache system
            await self._setup_caching()
            
            # 3. Initialize migration system
            await self._setup_migrations()
            
            # 4. Initialize read replica management
            await self._setup_read_replicas()
            
            # 5. Initialize archival system
            await self._setup_archival()
            
            # 6. Initialize RentVine integration
            await self._setup_rentvine_integration()
            
            self.initialized = True
            logger.info("All data layer systems initialized successfully!")
            
        except Exception as e:
            logger.error(f"Failed to initialize data layer: {str(e)}")
            raise
    
    async def _setup_databases(self):
        """Setup database connections"""
        logger.info("Setting up database connections...")
        
        # Setup primary and failover databases
        await setup_databases()
        
        # Verify connectivity
        async with get_db_connection() as conn:
            await conn.execute("SELECT 1")
        
        logger.info("Database connections established")
    
    async def _setup_caching(self):
        """Setup multi-tier caching"""
        logger.info("Setting up caching system...")
        
        redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/0')
        await initialize_cache_system(redis_url)
        
        # Warm cache with initial data
        if cache_manager:
            logger.info("Cache system ready for warming")
        
        logger.info("Caching system initialized")
    
    async def _setup_migrations(self):
        """Setup migration system"""
        logger.info("Setting up migration system...")
        
        await initialize_migration_system()
        
        # Check for pending migrations
        status = await get_migration_status()
        pending_count = status.get("pending_migrations", 0)
        
        if pending_count > 0:
            logger.warning(f"{pending_count} pending migrations found")
        else:
            logger.info("No pending migrations")
        
        logger.info("Migration system initialized")
    
    async def _setup_read_replicas(self):
        """Setup read replica management"""
        logger.info("Setting up read replica management...")
        
        await initialize_replica_manager()
        
        # Add read replicas if configured
        if hasattr(settings, 'postgres_read_host'):
            read_config = DatabaseConfig(
                host=settings.postgres_read_host,
                port=getattr(settings, 'postgres_read_port', 5432),
                database=getattr(settings, 'postgres_read_db', 'aictive'),
                username=getattr(settings, 'postgres_read_user', 'aictive'),
                password=getattr(settings, 'postgres_read_password', 'password'),
                db_type=DatabaseType.POSTGRESQL
            )
            
            await add_read_replica(
                replica_id="read_replica_primary",
                database_config=read_config,
                tags=["analytics", "reporting"]
            )
            
            logger.info("Read replica added")
        
        logger.info("Read replica management initialized")
    
    async def _setup_archival(self):
        """Setup data archival system"""
        logger.info("Setting up archival system...")
        
        # Configure storage (default to local filesystem for demo)
        storage_config = StorageConfig(
            provider=StorageProvider.LOCAL_FILESYSTEM,
            bucket_name=getattr(settings, 'archival_storage_path', './archives'),
            encryption=True
        )
        
        # Use S3 if configured
        if hasattr(settings, 'aws_s3_bucket'):
            storage_config = StorageConfig(
                provider=StorageProvider.AWS_S3,
                bucket_name=settings.aws_s3_bucket,
                region=getattr(settings, 'aws_region', 'us-east-1'),
                access_key=getattr(settings, 'aws_access_key', None),
                secret_key=getattr(settings, 'aws_secret_key', None),
                encryption=True
            )
        
        await initialize_archival_system(storage_config)
        
        logger.info("Archival system initialized")
    
    async def _setup_rentvine_integration(self):
        """Setup RentVine API integration"""
        logger.info("Setting up RentVine integration...")
        
        # Configure RentVine client
        rentvine_config = RentVineConfig(
            base_url=f"https://{settings.rentvine_subdomain}.rentvine.com/api/v2",
            api_key=settings.rentvine_access_key,
            api_secret=settings.rentvine_secret,
            tenant_id=getattr(settings, 'rentvine_tenant_id', 'default'),
            enable_caching=True
        )
        
        self.rentvine_client = RentVineAPIClient(rentvine_config)
        
        logger.info("RentVine integration ready")
    
    async def demonstrate_full_workflow(self):
        """Demonstrate the complete data layer workflow"""
        if not self.initialized:
            await self.initialize_all_systems()
        
        logger.info("=== Demonstrating Data Layer Workflow ===")
        
        # 1. Demonstrate caching with RentVine data
        await self._demo_caching_workflow()
        
        # 2. Demonstrate read/write splitting
        await self._demo_read_write_splitting()
        
        # 3. Demonstrate migration capabilities
        await self._demo_migration_workflow()
        
        # 4. Demonstrate archival workflow
        await self._demo_archival_workflow()
        
        # 5. Show comprehensive health status
        await self._demo_health_monitoring()
    
    async def _demo_caching_workflow(self):
        """Demonstrate intelligent caching"""
        logger.info("--- Caching Workflow Demo ---")
        
        if not cache_manager:
            logger.warning("Cache manager not available")
            return
        
        # Simulate RentVine data caching
        property_data = {
            "id": "prop_123",
            "name": "Sunset Apartments",
            "address": "123 Main St",
            "units": 24
        }
        
        # Cache property data
        await cache_manager.cache_rentvine_data("properties", "prop_123", property_data)
        logger.info("Cached property data")
        
        # Retrieve from cache (should be L1 hit)
        cached_data = await cache_manager.get_rentvine_data("properties", "prop_123")
        logger.info(f"Retrieved from cache: {cached_data['name']}")
        
        # Show cache statistics
        stats = cache_manager.get_comprehensive_stats()
        logger.info(f"Cache hit ratio: {stats['combined']['hit_ratio']:.2%}")
        
        # Demonstrate cache warming
        async def warm_properties():
            return {
                "prop_124": {"name": "Garden View", "units": 12},
                "prop_125": {"name": "City Center", "units": 36}
            }
        
        warmed_count = await cache_manager.warm_cache(
            warm_func=warm_properties,
            key_pattern="rentvine:properties",
            tags={"properties", "rentvine"},
            ttl=1800
        )
        logger.info(f"Warmed cache with {warmed_count} entries")
    
    async def _demo_read_write_splitting(self):
        """Demonstrate read/write query splitting"""
        logger.info("--- Read/Write Splitting Demo ---")
        
        # Write operation (goes to primary)
        insert_query = """
        INSERT INTO demo_table (name, value, created_at) 
        VALUES (%s, %s, %s)
        """
        
        try:
            # This would go to primary database
            await execute_query(
                insert_query, 
                ("Demo Entry", 42, datetime.utcnow())
            )
            logger.info("Write operation completed on primary database")
        except Exception as e:
            logger.info(f"Write operation simulation: {str(e)}")
        
        # Read operation (can go to replica)
        read_query = "SELECT COUNT(*) as total FROM demo_table WHERE created_at > %s"
        
        try:
            # This would be routed to read replica if available
            db_used, result = await execute_read_query(
                read_query, 
                (datetime.utcnow() - timedelta(days=1),)
            )
            logger.info(f"Read operation completed on: {db_used}")
        except Exception as e:
            logger.info(f"Read operation simulation: {str(e)}")
        
        # Show replica status
        status = get_replica_status()
        logger.info(f"Replica system status: {status['summary']}")
    
    async def _demo_migration_workflow(self):
        """Demonstrate migration capabilities"""
        logger.info("--- Migration Workflow Demo ---")
        
        # Show migration status
        status = await get_migration_status()
        logger.info(f"Migration status: {status['completed_migrations']} completed, "
                   f"{status['pending_migrations']} pending")
        
        # In a real scenario, you would run pending migrations
        # executions = await run_migrations(dry_run=True)
        # logger.info(f"Would execute {len(executions)} migrations")
        
        logger.info("Migration system ready for deployment")
    
    async def _demo_archival_workflow(self):
        """Demonstrate data archival"""
        logger.info("--- Archival Workflow Demo ---")
        
        # Show archival status
        status = await get_archival_status()
        logger.info(f"Archival system: {status['system_status']}")
        
        # Run archival simulation (dry run)
        try:
            executions = await run_archival(dry_run=True)
            total_rows = sum(e.rows_archived for e in executions)
            logger.info(f"Archival dry run: would archive {total_rows} rows")
        except Exception as e:
            logger.info(f"Archival simulation: {str(e)}")
    
    async def _demo_health_monitoring(self):
        """Show comprehensive health monitoring"""
        logger.info("--- Health Monitoring Demo ---")
        
        # Database metrics
        db_metrics = await get_database_metrics()
        logger.info("Database metrics collected")
        
        # Cache metrics
        if cache_manager:
            cache_stats = cache_manager.get_comprehensive_stats()
            logger.info(f"Cache performance: {cache_stats['combined']['hit_ratio']:.2%} hit ratio")
        
        # Replica status
        replica_status = get_replica_status()
        healthy_replicas = replica_status['summary']['healthy_replicas']
        total_replicas = replica_status['summary']['total_replicas']
        logger.info(f"Replica health: {healthy_replicas}/{total_replicas} healthy")
        
        # Archival status
        archival_status = await get_archival_status()
        success_rate = archival_status['execution_summary']['success_rate']
        logger.info(f"Archival success rate: {success_rate:.1f}%")
        
        self.health_status = {
            "database": "healthy",
            "cache": "healthy",
            "replicas": f"{healthy_replicas}/{total_replicas}",
            "archival": f"{success_rate:.1f}%",
            "overall": "operational"
        }
        
        logger.info(f"Overall system health: {self.health_status}")
    
    async def shutdown_all_systems(self):
        """Gracefully shutdown all systems"""
        logger.info("Shutting down data layer systems...")
        
        try:
            # Shutdown cache system
            if cache_manager:
                from redis_caching_strategy import shutdown_cache_system
                await shutdown_cache_system()
            
            # Shutdown replica manager
            from read_replica_manager import replica_manager
            if replica_manager:
                await replica_manager.shutdown()
            
            # Shutdown archival system
            from data_archival_strategy import archival_manager
            if archival_manager:
                await archival_manager.shutdown()
            
            # Close database connections
            from data_layer_core import db_manager
            await db_manager.close_all()
            
            logger.info("All systems shutdown gracefully")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")


# Example usage functions with decorators
class RentVineIntegrationExample:
    """Example of how to integrate with RentVine using the data layer"""
    
    def __init__(self, data_manager: AictiveDataLayerManager):
        self.data_manager = data_manager
    
    @cached_rentvine("properties", ttl=1800)
    async def get_property_with_caching(self, property_id: str):
        """Get property with automatic caching"""
        if self.data_manager.rentvine_client:
            async with self.data_manager.rentvine_client as client:
                response = await client.get_property(property_id)
                return response.data if response.success else None
        return {"id": property_id, "name": "Demo Property", "cached": True}
    
    @cache_invalidate_on_update("properties")
    async def update_property_with_cache_invalidation(self, property_id: str, updates: Dict):
        """Update property with automatic cache invalidation"""
        if self.data_manager.rentvine_client:
            async with self.data_manager.rentvine_client as client:
                response = await client.update_property(property_id, updates)
                return response
        return {"success": True, "cached_invalidated": True}
    
    async def get_analytics_data(self, start_date: datetime, end_date: datetime):
        """Get analytics data using read replica"""
        analytics_query = """
        SELECT 
            DATE(created_at) as date,
            COUNT(*) as transaction_count,
            SUM(amount) as total_amount
        FROM transactions 
        WHERE created_at BETWEEN %s AND %s
        GROUP BY DATE(created_at)
        ORDER BY date
        """
        
        try:
            # This query will be routed to analytics replica
            db_used, results = await execute_read_query(
                analytics_query, 
                (start_date, end_date),
                prefer_tags=["analytics"]
            )
            
            logger.info(f"Analytics query executed on: {db_used}")
            return results
            
        except Exception as e:
            logger.error(f"Analytics query failed: {str(e)}")
            return []
    
    async def process_webhook_update(self, webhook_data: Dict):
        """Process RentVine webhook update with cache invalidation"""
        entity_type = webhook_data.get("entity_type")
        entity_id = webhook_data.get("entity_id")
        action = webhook_data.get("action")
        
        logger.info(f"Processing webhook: {action} {entity_type} {entity_id}")
        
        if cache_manager and action in ["update", "delete"]:
            # Invalidate cache for updated entity
            await cache_manager.invalidate_rentvine_data(entity_type, entity_id)
            
            # Invalidate related caches
            if entity_type == "properties":
                await cache_manager.invalidate_by_tags({"properties", "rentvine"})
        
        # Store webhook event for audit
        webhook_query = """
        INSERT INTO webhook_events (entity_type, entity_id, action, payload, processed_at)
        VALUES (%s, %s, %s, %s, %s)
        """
        
        try:
            await execute_query(
                webhook_query,
                (entity_type, entity_id, action, str(webhook_data), datetime.utcnow())
            )
        except Exception as e:
            logger.error(f"Failed to store webhook event: {str(e)}")


async def main():
    """Main demonstration function"""
    logger.info("Starting Aictive Data Layer Integration Demo")
    
    # Initialize the data layer manager
    data_manager = AictiveDataLayerManager()
    
    try:
        # Initialize all systems
        await data_manager.initialize_all_systems()
        
        # Run the complete workflow demonstration
        await data_manager.demonstrate_full_workflow()
        
        # Demonstrate RentVine integration
        rentvine_integration = RentVineIntegrationExample(data_manager)
        
        # Example property operations
        property_data = await rentvine_integration.get_property_with_caching("prop_123")
        logger.info(f"Retrieved property: {property_data}")
        
        # Example analytics query
        analytics_data = await rentvine_integration.get_analytics_data(
            datetime.utcnow() - timedelta(days=30),
            datetime.utcnow()
        )
        logger.info(f"Analytics data points: {len(analytics_data)}")
        
        # Example webhook processing
        webhook_data = {
            "entity_type": "properties",
            "entity_id": "prop_123",
            "action": "update",
            "changes": {"name": "Updated Property Name"}
        }
        await rentvine_integration.process_webhook_update(webhook_data)
        
        logger.info("Demo completed successfully!")
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        raise
    
    finally:
        # Clean shutdown
        await data_manager.shutdown_all_systems()


if __name__ == "__main__":
    asyncio.run(main())