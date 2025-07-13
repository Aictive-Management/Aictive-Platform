"""
Database Migration Framework for Aictive Platform
Provides schema migration, version control, rollback capabilities,
data transformation pipelines, and migration validation
"""

import asyncio
import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import importlib.util
import traceback
import re

from data_layer_core import db_manager, get_db_connection, execute_query

logger = logging.getLogger(__name__)


class MigrationStatus(Enum):
    """Migration execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    SKIPPED = "skipped"


class MigrationType(Enum):
    """Types of migrations"""
    SCHEMA = "schema"
    DATA = "data"
    INDEX = "index"
    CONSTRAINT = "constraint"
    TRIGGER = "trigger"
    VIEW = "view"
    FUNCTION = "function"


class MigrationDirection(Enum):
    """Migration direction"""
    UP = "up"
    DOWN = "down"


@dataclass
class MigrationDependency:
    """Migration dependency specification"""
    migration_id: str
    required: bool = True
    reason: str = ""


@dataclass
class MigrationScript:
    """Migration script definition"""
    id: str
    name: str
    description: str
    migration_type: MigrationType
    up_sql: str
    down_sql: str
    dependencies: List[MigrationDependency] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_duration: Optional[int] = None  # seconds
    is_destructive: bool = False
    requires_downtime: bool = False
    batch_size: Optional[int] = None  # for large data migrations
    validation_queries: List[str] = field(default_factory=list)
    pre_checks: List[str] = field(default_factory=list)
    post_checks: List[str] = field(default_factory=list)


@dataclass
class MigrationExecution:
    """Migration execution record"""
    id: str
    migration_id: str
    status: MigrationStatus
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    error_message: Optional[str] = None
    rollback_reason: Optional[str] = None
    executed_by: str = "system"
    batch_number: Optional[int] = None
    rows_affected: int = 0
    checksum: Optional[str] = None


class MigrationValidator:
    """Validates migrations before and after execution"""
    
    def __init__(self):
        self.validation_rules = {
            "schema": self._validate_schema_migration,
            "data": self._validate_data_migration,
            "index": self._validate_index_migration
        }
    
    async def validate_migration(self, migration: MigrationScript) -> Tuple[bool, List[str]]:
        """Validate migration script"""
        issues = []
        
        # Basic validation
        if not migration.up_sql.strip():
            issues.append("Up migration SQL is empty")
        
        if not migration.down_sql.strip():
            issues.append("Down migration SQL is empty")
        
        # SQL syntax validation
        syntax_issues = await self._validate_sql_syntax(migration.up_sql)
        issues.extend(syntax_issues)
        
        # Type-specific validation
        if migration.migration_type.value in self.validation_rules:
            type_issues = await self.validation_rules[migration.migration_type.value](migration)
            issues.extend(type_issues)
        
        # Destructive operation checks
        if self._is_destructive_operation(migration.up_sql) and not migration.is_destructive:
            issues.append("Migration contains destructive operations but is not marked as destructive")
        
        return len(issues) == 0, issues
    
    async def _validate_sql_syntax(self, sql: str) -> List[str]:
        """Basic SQL syntax validation"""
        issues = []
        
        # Check for common issues
        if sql.strip().endswith(';') and sql.count(';') > 1:
            # Multiple statements - check if properly separated
            statements = [s.strip() for s in sql.split(';') if s.strip()]
            if len(statements) > 10:
                issues.append("Migration contains many statements - consider breaking into smaller migrations")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            (r'DROP\s+DATABASE', "Contains DROP DATABASE - extremely dangerous"),
            (r'TRUNCATE\s+TABLE', "Contains TRUNCATE TABLE - data loss operation"),
            (r'DELETE\s+FROM\s+\w+\s*$', "Contains DELETE without WHERE clause"),
            (r'UPDATE\s+\w+\s+SET.*(?!WHERE)', "Contains UPDATE without WHERE clause")
        ]
        
        for pattern, message in dangerous_patterns:
            if re.search(pattern, sql, re.IGNORECASE):
                issues.append(message)
        
        return issues
    
    def _is_destructive_operation(self, sql: str) -> bool:
        """Check if SQL contains destructive operations"""
        destructive_keywords = [
            'DROP TABLE', 'DROP COLUMN', 'DROP INDEX', 'DROP CONSTRAINT',
            'TRUNCATE', 'DELETE FROM', 'ALTER TABLE', 'DROP VIEW'
        ]
        
        sql_upper = sql.upper()
        return any(keyword in sql_upper for keyword in destructive_keywords)
    
    async def _validate_schema_migration(self, migration: MigrationScript) -> List[str]:
        """Validate schema migration"""
        issues = []
        
        # Check for proper table/column naming
        if 'CREATE TABLE' in migration.up_sql.upper():
            # Ensure proper naming conventions
            table_names = re.findall(r'CREATE\s+TABLE\s+(\w+)', migration.up_sql, re.IGNORECASE)
            for table_name in table_names:
                if not re.match(r'^[a-z][a-z0-9_]*$', table_name):
                    issues.append(f"Table name '{table_name}' doesn't follow naming conventions")
        
        return issues
    
    async def _validate_data_migration(self, migration: MigrationScript) -> List[str]:
        """Validate data migration"""
        issues = []
        
        # Check if batch size is specified for large data operations
        if any(keyword in migration.up_sql.upper() for keyword in ['INSERT', 'UPDATE', 'DELETE']):
            if migration.batch_size is None:
                issues.append("Data migration should specify batch_size for large operations")
        
        return issues
    
    async def _validate_index_migration(self, migration: MigrationScript) -> List[str]:
        """Validate index migration"""
        issues = []
        
        # Check for concurrent index creation
        if 'CREATE INDEX' in migration.up_sql.upper():
            if 'CONCURRENTLY' not in migration.up_sql.upper():
                issues.append("Consider using CONCURRENTLY for index creation to avoid blocking")
        
        return issues
    
    async def run_pre_checks(self, migration: MigrationScript, db_name: str = "primary") -> Tuple[bool, List[str]]:
        """Run pre-migration checks"""
        results = []
        
        for check_sql in migration.pre_checks:
            try:
                result = await execute_query(check_sql, db_name=db_name)
                results.append(f"Pre-check passed: {check_sql[:50]}...")
            except Exception as e:
                results.append(f"Pre-check failed: {check_sql[:50]}... - {str(e)}")
                return False, results
        
        return True, results
    
    async def run_post_checks(self, migration: MigrationScript, db_name: str = "primary") -> Tuple[bool, List[str]]:
        """Run post-migration validation"""
        results = []
        
        for check_sql in migration.post_checks:
            try:
                result = await execute_query(check_sql, db_name=db_name)
                results.append(f"Post-check passed: {check_sql[:50]}...")
            except Exception as e:
                results.append(f"Post-check failed: {check_sql[:50]}... - {str(e)}")
                return False, results
        
        return True, results


class MigrationRepository:
    """Manages migration scripts and execution history"""
    
    def __init__(self, migrations_path: str = "migrations"):
        self.migrations_path = Path(migrations_path)
        self.migrations: Dict[str, MigrationScript] = {}
        self.execution_history: List[MigrationExecution] = []
        self._ensure_migration_tables()
    
    async def _ensure_migration_tables(self):
        """Ensure migration tracking tables exist"""
        schema_sql = """
        CREATE TABLE IF NOT EXISTS migration_executions (
            id VARCHAR(255) PRIMARY KEY,
            migration_id VARCHAR(255) NOT NULL,
            status VARCHAR(50) NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP,
            duration_seconds DECIMAL(10,3),
            error_message TEXT,
            rollback_reason TEXT,
            executed_by VARCHAR(255) DEFAULT 'system',
            batch_number INTEGER,
            rows_affected INTEGER DEFAULT 0,
            checksum VARCHAR(64),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_migration_executions_migration_id 
        ON migration_executions(migration_id);
        
        CREATE INDEX IF NOT EXISTS idx_migration_executions_status 
        ON migration_executions(status);
        
        CREATE TABLE IF NOT EXISTS migration_locks (
            lock_name VARCHAR(255) PRIMARY KEY,
            locked_at TIMESTAMP NOT NULL,
            locked_by VARCHAR(255) NOT NULL,
            expires_at TIMESTAMP NOT NULL
        );
        """
        
        try:
            async with get_db_connection() as conn:
                # Split and execute each statement
                statements = [s.strip() for s in schema_sql.split(';') if s.strip()]
                for statement in statements:
                    await conn.execute(statement)
            
            logger.info("Migration tracking tables ensured")
        except Exception as e:
            logger.error(f"Failed to create migration tables: {str(e)}")
            raise
    
    def load_migrations_from_directory(self) -> int:
        """Load migration scripts from directory"""
        self.migrations.clear()
        
        if not self.migrations_path.exists():
            self.migrations_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created migrations directory: {self.migrations_path}")
            return 0
        
        loaded_count = 0
        for migration_file in self.migrations_path.glob("*.py"):
            try:
                migration = self._load_migration_from_file(migration_file)
                if migration:
                    self.migrations[migration.id] = migration
                    loaded_count += 1
            except Exception as e:
                logger.error(f"Failed to load migration {migration_file}: {str(e)}")
        
        logger.info(f"Loaded {loaded_count} migrations from {self.migrations_path}")
        return loaded_count
    
    def _load_migration_from_file(self, file_path: Path) -> Optional[MigrationScript]:
        """Load migration from Python file"""
        try:
            spec = importlib.util.spec_from_file_location("migration", file_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            
            # Migration file should define these attributes
            if not hasattr(module, 'MIGRATION_ID'):
                logger.warning(f"Migration file {file_path} missing MIGRATION_ID")
                return None
            
            migration = MigrationScript(
                id=module.MIGRATION_ID,
                name=getattr(module, 'MIGRATION_NAME', file_path.stem),
                description=getattr(module, 'DESCRIPTION', ''),
                migration_type=MigrationType(getattr(module, 'MIGRATION_TYPE', 'schema')),
                up_sql=getattr(module, 'UP_SQL', ''),
                down_sql=getattr(module, 'DOWN_SQL', ''),
                dependencies=[
                    MigrationDependency(**dep) if isinstance(dep, dict) else dep
                    for dep in getattr(module, 'DEPENDENCIES', [])
                ],
                tags=getattr(module, 'TAGS', []),
                estimated_duration=getattr(module, 'ESTIMATED_DURATION', None),
                is_destructive=getattr(module, 'IS_DESTRUCTIVE', False),
                requires_downtime=getattr(module, 'REQUIRES_DOWNTIME', False),
                batch_size=getattr(module, 'BATCH_SIZE', None),
                validation_queries=getattr(module, 'VALIDATION_QUERIES', []),
                pre_checks=getattr(module, 'PRE_CHECKS', []),
                post_checks=getattr(module, 'POST_CHECKS', [])
            )
            
            return migration
            
        except Exception as e:
            logger.error(f"Error loading migration from {file_path}: {str(e)}")
            return None
    
    async def get_execution_history(self, migration_id: str = None) -> List[MigrationExecution]:
        """Get migration execution history"""
        query = """
        SELECT id, migration_id, status, started_at, completed_at, 
               duration_seconds, error_message, rollback_reason, 
               executed_by, batch_number, rows_affected, checksum
        FROM migration_executions
        """
        params = None
        
        if migration_id:
            query += " WHERE migration_id = %s"
            params = (migration_id,)
        
        query += " ORDER BY started_at DESC"
        
        try:
            async with get_db_connection() as conn:
                results = await conn.fetchall(query, params)
                
                return [
                    MigrationExecution(
                        id=row['id'],
                        migration_id=row['migration_id'],
                        status=MigrationStatus(row['status']),
                        started_at=row['started_at'],
                        completed_at=row['completed_at'],
                        duration_seconds=float(row['duration_seconds']) if row['duration_seconds'] else None,
                        error_message=row['error_message'],
                        rollback_reason=row['rollback_reason'],
                        executed_by=row['executed_by'],
                        batch_number=row['batch_number'],
                        rows_affected=row['rows_affected'],
                        checksum=row['checksum']
                    )
                    for row in results
                ]
        except Exception as e:
            logger.error(f"Failed to get execution history: {str(e)}")
            return []
    
    async def record_execution(self, execution: MigrationExecution):
        """Record migration execution"""
        query = """
        INSERT INTO migration_executions 
        (id, migration_id, status, started_at, completed_at, duration_seconds,
         error_message, rollback_reason, executed_by, batch_number, 
         rows_affected, checksum)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
        status = VALUES(status),
        completed_at = VALUES(completed_at),
        duration_seconds = VALUES(duration_seconds),
        error_message = VALUES(error_message),
        rollback_reason = VALUES(rollback_reason),
        rows_affected = VALUES(rows_affected)
        """
        
        params = (
            execution.id,
            execution.migration_id,
            execution.status.value,
            execution.started_at,
            execution.completed_at,
            execution.duration_seconds,
            execution.error_message,
            execution.rollback_reason,
            execution.executed_by,
            execution.batch_number,
            execution.rows_affected,
            execution.checksum
        )
        
        try:
            async with get_db_connection() as conn:
                await conn.execute(query, params)
        except Exception as e:
            logger.error(f"Failed to record migration execution: {str(e)}")
            raise
    
    async def get_pending_migrations(self) -> List[MigrationScript]:
        """Get migrations that haven't been successfully executed"""
        executed_migrations = set()
        
        # Get successfully executed migrations
        history = await self.get_execution_history()
        for execution in history:
            if execution.status == MigrationStatus.COMPLETED:
                executed_migrations.add(execution.migration_id)
        
        # Return migrations not in executed set
        return [
            migration for migration_id, migration in self.migrations.items()
            if migration_id not in executed_migrations
        ]
    
    def get_migration_by_id(self, migration_id: str) -> Optional[MigrationScript]:
        """Get migration script by ID"""
        return self.migrations.get(migration_id)
    
    def get_all_migrations(self) -> List[MigrationScript]:
        """Get all loaded migration scripts"""
        return list(self.migrations.values())


class MigrationExecutor:
    """Executes migrations with rollback support"""
    
    def __init__(self, repository: MigrationRepository, validator: MigrationValidator):
        self.repository = repository
        self.validator = validator
        self.current_execution: Optional[MigrationExecution] = None
    
    async def execute_migration(
        self, 
        migration: MigrationScript, 
        direction: MigrationDirection = MigrationDirection.UP,
        db_name: str = "primary",
        dry_run: bool = False
    ) -> MigrationExecution:
        """Execute a single migration"""
        
        execution_id = f"{migration.id}_{direction.value}_{int(datetime.utcnow().timestamp())}"
        execution = MigrationExecution(
            id=execution_id,
            migration_id=migration.id,
            status=MigrationStatus.RUNNING,
            started_at=datetime.utcnow()
        )
        
        self.current_execution = execution
        
        try:
            # Record start of execution
            await self.repository.record_execution(execution)
            
            # Validate migration
            if direction == MigrationDirection.UP:
                is_valid, issues = await self.validator.validate_migration(migration)
                if not is_valid:
                    raise Exception(f"Migration validation failed: {', '.join(issues)}")
                
                # Run pre-checks
                pre_check_passed, pre_results = await self.validator.run_pre_checks(migration, db_name)
                if not pre_check_passed:
                    raise Exception(f"Pre-checks failed: {', '.join(pre_results)}")
            
            # Execute SQL
            sql = migration.up_sql if direction == MigrationDirection.UP else migration.down_sql
            
            if dry_run:
                logger.info(f"DRY RUN - Would execute migration {migration.id}")
                logger.info(f"SQL: {sql}")
                execution.status = MigrationStatus.COMPLETED
            else:
                rows_affected = await self._execute_sql(sql, migration, db_name)
                execution.rows_affected = rows_affected
                
                # Run post-checks for UP migrations
                if direction == MigrationDirection.UP:
                    post_check_passed, post_results = await self.validator.run_post_checks(migration, db_name)
                    if not post_check_passed:
                        raise Exception(f"Post-checks failed: {', '.join(post_results)}")
                
                execution.status = MigrationStatus.COMPLETED
            
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            # Calculate checksum
            execution.checksum = hashlib.sha256(sql.encode()).hexdigest()
            
            logger.info(
                f"Migration {migration.id} executed successfully in "
                f"{execution.duration_seconds:.2f} seconds"
            )
            
        except Exception as e:
            execution.status = MigrationStatus.FAILED
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            execution.duration_seconds = (
                execution.completed_at - execution.started_at
            ).total_seconds()
            
            logger.error(f"Migration {migration.id} failed: {str(e)}")
            logger.debug(traceback.format_exc())
        
        finally:
            # Record final execution state
            await self.repository.record_execution(execution)
            self.current_execution = None
        
        return execution
    
    async def _execute_sql(
        self, 
        sql: str, 
        migration: MigrationScript, 
        db_name: str
    ) -> int:
        """Execute SQL with proper transaction handling"""
        
        async with get_db_connection(db_name) as conn:
            # Handle batch processing for data migrations
            if migration.batch_size and migration.migration_type == MigrationType.DATA:
                return await self._execute_batched_sql(sql, migration.batch_size, conn)
            else:
                # Execute as single transaction
                try:
                    # Split multiple statements
                    statements = [s.strip() for s in sql.split(';') if s.strip()]
                    total_rows = 0
                    
                    for statement in statements:
                        result = await conn.execute(statement)
                        # Extract row count if available
                        if hasattr(result, 'rowcount'):
                            total_rows += result.rowcount
                        elif isinstance(result, str) and 'affected' in result.lower():
                            # Parse rowcount from result string if possible
                            import re
                            match = re.search(r'(\d+)', result)
                            if match:
                                total_rows += int(match.group(1))
                    
                    return total_rows
                    
                except Exception as e:
                    logger.error(f"SQL execution failed: {str(e)}")
                    raise
    
    async def _execute_batched_sql(
        self, 
        sql: str, 
        batch_size: int, 
        conn
    ) -> int:
        """Execute SQL in batches for large data operations"""
        
        # This is a simplified implementation
        # In practice, you'd need to modify the SQL to use LIMIT/OFFSET
        # or implement cursor-based pagination
        
        total_rows = 0
        batch_number = 0
        
        while True:
            # Modify SQL to add LIMIT clause
            batched_sql = f"{sql} LIMIT {batch_size} OFFSET {batch_number * batch_size}"
            
            try:
                result = await conn.execute(batched_sql)
                rows_affected = getattr(result, 'rowcount', 0)
                
                if rows_affected == 0:
                    break  # No more rows to process
                
                total_rows += rows_affected
                batch_number += 1
                
                # Update execution record with batch progress
                if self.current_execution:
                    self.current_execution.batch_number = batch_number
                    self.current_execution.rows_affected = total_rows
                    await self.repository.record_execution(self.current_execution)
                
                # Small delay between batches
                await asyncio.sleep(0.1)
                
            except Exception as e:
                logger.error(f"Batch {batch_number} failed: {str(e)}")
                raise
        
        return total_rows
    
    async def rollback_migration(
        self, 
        migration_id: str, 
        reason: str = "Manual rollback",
        db_name: str = "primary"
    ) -> MigrationExecution:
        """Rollback a migration"""
        
        migration = self.repository.get_migration_by_id(migration_id)
        if not migration:
            raise ValueError(f"Migration {migration_id} not found")
        
        if not migration.down_sql.strip():
            raise ValueError(f"Migration {migration_id} has no rollback SQL")
        
        # Execute down migration
        execution = await self.execute_migration(
            migration, 
            MigrationDirection.DOWN, 
            db_name
        )
        
        execution.rollback_reason = reason
        await self.repository.record_execution(execution)
        
        return execution


class MigrationManager:
    """Main migration management interface"""
    
    def __init__(self, migrations_path: str = "migrations"):
        self.repository = MigrationRepository(migrations_path)
        self.validator = MigrationValidator()
        self.executor = MigrationExecutor(self.repository, self.validator)
    
    async def initialize(self):
        """Initialize migration system"""
        await self.repository._ensure_migration_tables()
        self.repository.load_migrations_from_directory()
        logger.info("Migration system initialized")
    
    async def run_pending_migrations(
        self, 
        db_name: str = "primary",
        dry_run: bool = False,
        tags: Optional[List[str]] = None
    ) -> List[MigrationExecution]:
        """Run all pending migrations"""
        
        pending = await self.repository.get_pending_migrations()
        
        # Filter by tags if specified
        if tags:
            pending = [m for m in pending if any(tag in m.tags for tag in tags)]
        
        # Sort by dependencies (simplified - would need proper topological sort)
        pending.sort(key=lambda m: len(m.dependencies))
        
        executions = []
        
        for migration in pending:
            try:
                # Check dependencies
                await self._check_dependencies(migration)
                
                execution = await self.executor.execute_migration(
                    migration, 
                    MigrationDirection.UP, 
                    db_name, 
                    dry_run
                )
                executions.append(execution)
                
                if execution.status == MigrationStatus.FAILED:
                    logger.error(f"Migration {migration.id} failed, stopping migration run")
                    break
                    
            except Exception as e:
                logger.error(f"Failed to execute migration {migration.id}: {str(e)}")
                break
        
        return executions
    
    async def _check_dependencies(self, migration: MigrationScript):
        """Check if migration dependencies are satisfied"""
        history = await self.repository.get_execution_history()
        completed_migrations = {
            exec.migration_id for exec in history 
            if exec.status == MigrationStatus.COMPLETED
        }
        
        for dependency in migration.dependencies:
            if dependency.required and dependency.migration_id not in completed_migrations:
                raise Exception(
                    f"Required dependency {dependency.migration_id} not completed for "
                    f"migration {migration.id}: {dependency.reason}"
                )
    
    async def rollback_to_migration(
        self, 
        target_migration_id: str,
        db_name: str = "primary"
    ) -> List[MigrationExecution]:
        """Rollback to a specific migration"""
        
        history = await self.repository.get_execution_history()
        completed_migrations = [
            exec for exec in history 
            if exec.status == MigrationStatus.COMPLETED
        ]
        
        # Find migrations to rollback (after target)
        rollback_executions = []
        found_target = False
        
        for execution in reversed(completed_migrations):  # Most recent first
            if execution.migration_id == target_migration_id:
                found_target = True
                break
            
            # Rollback this migration
            try:
                rollback_execution = await self.executor.rollback_migration(
                    execution.migration_id,
                    f"Rollback to {target_migration_id}",
                    db_name
                )
                rollback_executions.append(rollback_execution)
                
            except Exception as e:
                logger.error(f"Failed to rollback migration {execution.migration_id}: {str(e)}")
                break
        
        if not found_target:
            raise ValueError(f"Target migration {target_migration_id} not found in completed migrations")
        
        return rollback_executions
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get overall migration system status"""
        all_migrations = self.repository.get_all_migrations()
        pending_migrations = await self.repository.get_pending_migrations()
        history = await self.repository.get_execution_history()
        
        # Statistics
        completed_count = len([h for h in history if h.status == MigrationStatus.COMPLETED])
        failed_count = len([h for h in history if h.status == MigrationStatus.FAILED])
        
        return {
            "total_migrations": len(all_migrations),
            "pending_migrations": len(pending_migrations),
            "completed_migrations": completed_count,
            "failed_migrations": failed_count,
            "last_execution": history[0] if history else None,
            "migrations": [
                {
                    "id": m.id,
                    "name": m.name,
                    "type": m.migration_type.value,
                    "is_destructive": m.is_destructive,
                    "requires_downtime": m.requires_downtime,
                    "status": "pending" if m in pending_migrations else "completed"
                }
                for m in all_migrations
            ]
        }
    
    def create_migration_template(self, migration_id: str, name: str, migration_type: str = "schema"):
        """Create a new migration file template"""
        template = f'''"""
Migration: {name}
ID: {migration_id}
Type: {migration_type}
"""

MIGRATION_ID = "{migration_id}"
MIGRATION_NAME = "{name}"
DESCRIPTION = ""
MIGRATION_TYPE = "{migration_type}"
IS_DESTRUCTIVE = False
REQUIRES_DOWNTIME = False
ESTIMATED_DURATION = None  # seconds
BATCH_SIZE = None  # for data migrations
TAGS = []
DEPENDENCIES = []

# Pre-migration checks
PRE_CHECKS = [
    # "SELECT COUNT(*) FROM some_table WHERE condition"
]

# Post-migration validation
POST_CHECKS = [
    # "SELECT COUNT(*) FROM new_table"
]

# Validation queries
VALIDATION_QUERIES = [
    # "SELECT 1"
]

UP_SQL = """
-- Your migration SQL here
"""

DOWN_SQL = """
-- Rollback SQL here
"""
'''
        
        file_path = self.repository.migrations_path / f"{migration_id}.py"
        file_path.write_text(template)
        
        logger.info(f"Created migration template: {file_path}")
        return file_path


# Global migration manager
migration_manager: Optional[MigrationManager] = None


async def initialize_migration_system(migrations_path: str = "migrations") -> MigrationManager:
    """Initialize the global migration system"""
    global migration_manager
    
    migration_manager = MigrationManager(migrations_path)
    await migration_manager.initialize()
    
    return migration_manager


async def run_migrations(dry_run: bool = False, tags: Optional[List[str]] = None):
    """Run pending migrations"""
    if not migration_manager:
        raise RuntimeError("Migration system not initialized")
    
    return await migration_manager.run_pending_migrations(dry_run=dry_run, tags=tags)


async def get_migration_status():
    """Get migration system status"""
    if not migration_manager:
        raise RuntimeError("Migration system not initialized")
    
    return await migration_manager.get_migration_status()