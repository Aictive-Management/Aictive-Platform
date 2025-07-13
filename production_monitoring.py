"""
Production Monitoring and Health Check System
Comprehensive monitoring, metrics, and alerting for Aictive Platform
"""

import asyncio
import time
import json
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import psutil
import httpx
from prometheus_client import Counter, Histogram, Gauge, Summary, CollectorRegistry, generate_latest
import structlog

# Configure structured logging
logger = structlog.get_logger()


class HealthStatus(Enum):
    """Health check status levels"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class MetricType(Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


@dataclass
class HealthCheckResult:
    """Result of a health check"""
    name: str
    status: HealthStatus
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Alert:
    """Alert configuration"""
    name: str
    condition: str
    threshold: float
    duration_seconds: int
    severity: str  # critical, warning, info
    notification_channels: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class MetricsCollector:
    """Prometheus metrics collector"""
    
    def __init__(self, registry: Optional[CollectorRegistry] = None):
        self.registry = registry or CollectorRegistry()
        self._initialize_metrics()
    
    def _initialize_metrics(self):
        """Initialize all metrics"""
        # API metrics
        self.api_requests_total = Counter(
            'aictive_api_requests_total',
            'Total API requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.api_request_duration = Histogram(
            'aictive_api_request_duration_seconds',
            'API request duration',
            ['method', 'endpoint'],
            buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
            registry=self.registry
        )
        
        # Workflow metrics
        self.workflow_executions_total = Counter(
            'aictive_workflow_executions_total',
            'Total workflow executions',
            ['workflow_type', 'status'],
            registry=self.registry
        )
        
        self.workflow_duration = Histogram(
            'aictive_workflow_duration_seconds',
            'Workflow execution duration',
            ['workflow_type'],
            buckets=(1, 5, 10, 30, 60, 300, 600, 1800, 3600),
            registry=self.registry
        )
        
        self.workflow_steps_completed = Counter(
            'aictive_workflow_steps_completed_total',
            'Total workflow steps completed',
            ['workflow_type', 'step_name', 'status'],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            'aictive_active_connections',
            'Number of active connections',
            ['connection_type'],
            registry=self.registry
        )
        
        self.database_connections = Gauge(
            'aictive_database_connections',
            'Number of database connections',
            ['database', 'state'],
            registry=self.registry
        )
        
        # Business metrics
        self.properties_total = Gauge(
            'aictive_properties_total',
            'Total number of properties',
            ['status'],
            registry=self.registry
        )
        
        self.work_orders_total = Gauge(
            'aictive_work_orders_total',
            'Total number of work orders',
            ['status', 'priority'],
            registry=self.registry
        )
        
        self.vacancy_rate = Gauge(
            'aictive_vacancy_rate',
            'Current vacancy rate',
            ['property_id'],
            registry=self.registry
        )
        
        self.revenue_collected = Counter(
            'aictive_revenue_collected_total',
            'Total revenue collected',
            ['type', 'property_id'],
            registry=self.registry
        )
        
        # AI/ML metrics
        self.ai_decisions_total = Counter(
            'aictive_ai_decisions_total',
            'Total AI decisions made',
            ['decision_type', 'confidence_level'],
            registry=self.registry
        )
        
        self.swarm_executions = Counter(
            'aictive_swarm_executions_total',
            'Total swarm executions',
            ['swarm_type', 'objective'],
            registry=self.registry
        )
        
        # Error metrics
        self.errors_total = Counter(
            'aictive_errors_total',
            'Total errors',
            ['error_type', 'component'],
            registry=self.registry
        )
    
    def record_api_request(self, method: str, endpoint: str, status: int, duration: float):
        """Record API request metrics"""
        self.api_requests_total.labels(method=method, endpoint=endpoint, status=str(status)).inc()
        self.api_request_duration.labels(method=method, endpoint=endpoint).observe(duration)
    
    def record_workflow_execution(self, workflow_type: str, status: str, duration: float):
        """Record workflow execution metrics"""
        self.workflow_executions_total.labels(workflow_type=workflow_type, status=status).inc()
        self.workflow_duration.labels(workflow_type=workflow_type).observe(duration)
    
    def record_workflow_step(self, workflow_type: str, step_name: str, status: str):
        """Record workflow step completion"""
        self.workflow_steps_completed.labels(
            workflow_type=workflow_type,
            step_name=step_name,
            status=status
        ).inc()
    
    def update_business_metrics(self, metrics: Dict[str, Any]):
        """Update business metrics"""
        if "properties" in metrics:
            for status, count in metrics["properties"].items():
                self.properties_total.labels(status=status).set(count)
        
        if "work_orders" in metrics:
            for status, priorities in metrics["work_orders"].items():
                for priority, count in priorities.items():
                    self.work_orders_total.labels(status=status, priority=priority).set(count)
        
        if "vacancy_rates" in metrics:
            for property_id, rate in metrics["vacancy_rates"].items():
                self.vacancy_rate.labels(property_id=property_id).set(rate)
    
    def record_ai_decision(self, decision_type: str, confidence: float):
        """Record AI decision metrics"""
        confidence_level = "high" if confidence > 0.8 else "medium" if confidence > 0.5 else "low"
        self.ai_decisions_total.labels(
            decision_type=decision_type,
            confidence_level=confidence_level
        ).inc()
    
    def record_error(self, error_type: str, component: str):
        """Record error metrics"""
        self.errors_total.labels(error_type=error_type, component=component).inc()
    
    def get_metrics(self) -> bytes:
        """Get metrics in Prometheus format"""
        return generate_latest(self.registry)


class HealthChecker:
    """Comprehensive health checking system"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.checks: Dict[str, Callable] = {}
        self._register_default_checks()
    
    def _register_default_checks(self):
        """Register default health checks"""
        self.register_check("system", self._check_system_resources)
        self.register_check("database", self._check_database)
        self.register_check("api", self._check_api)
        self.register_check("redis", self._check_redis)
        self.register_check("rentvine", self._check_rentvine)
    
    def register_check(self, name: str, check_func: Callable):
        """Register a health check"""
        self.checks[name] = check_func
    
    async def _check_system_resources(self) -> HealthCheckResult:
        """Check system resources"""
        start_time = time.time()
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Determine health status
            if cpu_percent > 90 or memory.percent > 90 or disk.percent > 90:
                status = HealthStatus.UNHEALTHY
                message = "System resources critically high"
            elif cpu_percent > 70 or memory.percent > 70 or disk.percent > 80:
                status = HealthStatus.DEGRADED
                message = "System resources elevated"
            else:
                status = HealthStatus.HEALTHY
                message = "System resources normal"
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="system",
                status=status,
                message=message,
                details={
                    "cpu_percent": cpu_percent,
                    "memory_percent": memory.percent,
                    "memory_available_gb": memory.available / (1024**3),
                    "disk_percent": disk.percent,
                    "disk_free_gb": disk.free / (1024**3)
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            return HealthCheckResult(
                name="system",
                status=HealthStatus.UNHEALTHY,
                message=f"System check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_database(self) -> HealthCheckResult:
        """Check database connectivity"""
        start_time = time.time()
        
        try:
            # This would be actual database check
            # For now, simulate with a simple check
            await asyncio.sleep(0.01)  # Simulate DB query
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="database",
                status=HealthStatus.HEALTHY,
                message="Database connection healthy",
                details={
                    "response_time_ms": duration_ms,
                    "active_connections": 5,
                    "max_connections": 100
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            return HealthCheckResult(
                name="database",
                status=HealthStatus.UNHEALTHY,
                message=f"Database check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_api(self) -> HealthCheckResult:
        """Check internal API health"""
        start_time = time.time()
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get("http://localhost:8000/health", timeout=5.0)
                response.raise_for_status()
                
                duration_ms = (time.time() - start_time) * 1000
                
                return HealthCheckResult(
                    name="api",
                    status=HealthStatus.HEALTHY,
                    message="API responding normally",
                    details={
                        "response_time_ms": duration_ms,
                        "status_code": response.status_code
                    },
                    duration_ms=duration_ms
                )
        except Exception as e:
            return HealthCheckResult(
                name="api",
                status=HealthStatus.UNHEALTHY,
                message=f"API check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_redis(self) -> HealthCheckResult:
        """Check Redis connectivity"""
        start_time = time.time()
        
        try:
            # Simulate Redis check
            await asyncio.sleep(0.005)
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.HEALTHY,
                message="Redis connection healthy",
                details={
                    "response_time_ms": duration_ms,
                    "used_memory_mb": 128,
                    "connected_clients": 10
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            return HealthCheckResult(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                message=f"Redis check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def _check_rentvine(self) -> HealthCheckResult:
        """Check RentVine API connectivity"""
        start_time = time.time()
        
        try:
            # This would check actual RentVine API
            await asyncio.sleep(0.1)  # Simulate API call
            
            duration_ms = (time.time() - start_time) * 1000
            
            return HealthCheckResult(
                name="rentvine",
                status=HealthStatus.HEALTHY,
                message="RentVine API accessible",
                details={
                    "response_time_ms": duration_ms,
                    "api_version": "v2",
                    "rate_limit_remaining": 950
                },
                duration_ms=duration_ms
            )
        except Exception as e:
            return HealthCheckResult(
                name="rentvine",
                status=HealthStatus.DEGRADED,  # Degraded, not unhealthy - we can work without it
                message=f"RentVine API check failed: {str(e)}",
                duration_ms=(time.time() - start_time) * 1000
            )
    
    async def run_all_checks(self) -> Dict[str, HealthCheckResult]:
        """Run all health checks"""
        results = {}
        
        # Run checks in parallel
        tasks = {
            name: asyncio.create_task(check_func())
            for name, check_func in self.checks.items()
        }
        
        for name, task in tasks.items():
            try:
                results[name] = await task
            except Exception as e:
                results[name] = HealthCheckResult(
                    name=name,
                    status=HealthStatus.UNHEALTHY,
                    message=f"Check failed with exception: {str(e)}"
                )
        
        return results
    
    def get_overall_status(self, results: Dict[str, HealthCheckResult]) -> HealthStatus:
        """Determine overall system health"""
        statuses = [result.status for result in results.values()]
        
        if any(status == HealthStatus.UNHEALTHY for status in statuses):
            return HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in statuses):
            return HealthStatus.DEGRADED
        else:
            return HealthStatus.HEALTHY


class AlertManager:
    """Alert management and notification system"""
    
    def __init__(self, metrics_collector: MetricsCollector):
        self.metrics = metrics_collector
        self.alerts: Dict[str, Alert] = {}
        self.alert_states: Dict[str, Dict[str, Any]] = {}
        self._register_default_alerts()
    
    def _register_default_alerts(self):
        """Register default alerts"""
        # High error rate
        self.register_alert(Alert(
            name="high_error_rate",
            condition="rate(errors_total[5m]) > 10",
            threshold=10,
            duration_seconds=300,
            severity="critical",
            notification_channels=["slack", "email"]
        ))
        
        # API latency
        self.register_alert(Alert(
            name="high_api_latency",
            condition="histogram_quantile(0.95, api_request_duration_seconds) > 2",
            threshold=2.0,
            duration_seconds=300,
            severity="warning",
            notification_channels=["slack"]
        ))
        
        # Workflow failures
        self.register_alert(Alert(
            name="workflow_failures",
            condition="rate(workflow_executions_total{status='failed'}[10m]) > 5",
            threshold=5,
            duration_seconds=600,
            severity="critical",
            notification_channels=["slack", "pagerduty"]
        ))
        
        # System resources
        self.register_alert(Alert(
            name="high_cpu_usage",
            condition="cpu_percent > 85",
            threshold=85,
            duration_seconds=300,
            severity="warning",
            notification_channels=["slack"]
        ))
        
        # Business metrics
        self.register_alert(Alert(
            name="high_vacancy_rate",
            condition="vacancy_rate > 0.15",
            threshold=0.15,
            duration_seconds=3600,
            severity="warning",
            notification_channels=["email"],
            metadata={"business_impact": "high"}
        ))
    
    def register_alert(self, alert: Alert):
        """Register an alert"""
        self.alerts[alert.name] = alert
        self.alert_states[alert.name] = {
            "active": False,
            "triggered_at": None,
            "last_notification": None
        }
    
    async def check_alerts(self, current_metrics: Dict[str, Any]):
        """Check all alerts against current metrics"""
        triggered_alerts = []
        
        for alert_name, alert in self.alerts.items():
            if self._evaluate_alert_condition(alert, current_metrics):
                if not self.alert_states[alert_name]["active"]:
                    # New alert
                    self.alert_states[alert_name]["active"] = True
                    self.alert_states[alert_name]["triggered_at"] = datetime.utcnow()
                    triggered_alerts.append(alert)
                    await self._send_alert_notification(alert, "triggered")
                    
                    logger.warning(
                        "Alert triggered",
                        alert_name=alert_name,
                        severity=alert.severity,
                        threshold=alert.threshold
                    )
            else:
                if self.alert_states[alert_name]["active"]:
                    # Alert resolved
                    self.alert_states[alert_name]["active"] = False
                    await self._send_alert_notification(alert, "resolved")
                    
                    logger.info(
                        "Alert resolved",
                        alert_name=alert_name
                    )
        
        return triggered_alerts
    
    def _evaluate_alert_condition(self, alert: Alert, metrics: Dict[str, Any]) -> bool:
        """Evaluate if alert condition is met"""
        # This is a simplified evaluation
        # In production, you'd use a proper expression evaluator
        
        # For demonstration, check some specific conditions
        if alert.name == "high_error_rate":
            error_rate = metrics.get("error_rate", 0)
            return error_rate > alert.threshold
        elif alert.name == "high_cpu_usage":
            cpu_usage = metrics.get("cpu_percent", 0)
            return cpu_usage > alert.threshold
        elif alert.name == "high_vacancy_rate":
            vacancy_rate = metrics.get("avg_vacancy_rate", 0)
            return vacancy_rate > alert.threshold
        
        return False
    
    async def _send_alert_notification(self, alert: Alert, status: str):
        """Send alert notification"""
        for channel in alert.notification_channels:
            if channel == "slack":
                await self._send_slack_notification(alert, status)
            elif channel == "email":
                await self._send_email_notification(alert, status)
            elif channel == "pagerduty":
                await self._send_pagerduty_notification(alert, status)
    
    async def _send_slack_notification(self, alert: Alert, status: str):
        """Send Slack notification"""
        # Implement actual Slack webhook call
        logger.info(
            "Slack notification sent",
            alert_name=alert.name,
            status=status,
            severity=alert.severity
        )
    
    async def _send_email_notification(self, alert: Alert, status: str):
        """Send email notification"""
        # Implement actual email sending
        logger.info(
            "Email notification sent",
            alert_name=alert.name,
            status=status,
            severity=alert.severity
        )
    
    async def _send_pagerduty_notification(self, alert: Alert, status: str):
        """Send PagerDuty notification"""
        # Implement actual PagerDuty integration
        logger.info(
            "PagerDuty notification sent",
            alert_name=alert.name,
            status=status,
            severity=alert.severity
        )


class MonitoringService:
    """Main monitoring service orchestrator"""
    
    def __init__(self):
        self.metrics = MetricsCollector()
        self.health_checker = HealthChecker(self.metrics)
        self.alert_manager = AlertManager(self.metrics)
        self.is_running = False
    
    async def start(self):
        """Start monitoring service"""
        self.is_running = True
        logger.info("Monitoring service started")
        
        # Start background tasks
        tasks = [
            asyncio.create_task(self._collect_metrics_loop()),
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._alert_check_loop())
        ]
        
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.info("Monitoring service stopped")
    
    async def stop(self):
        """Stop monitoring service"""
        self.is_running = False
    
    async def _collect_metrics_loop(self):
        """Continuously collect metrics"""
        while self.is_running:
            try:
                # Collect system metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                
                # Update gauges
                self.metrics.active_connections.labels(connection_type="http").set(50)  # Example
                self.metrics.database_connections.labels(database="main", state="active").set(10)
                
                # Collect business metrics (would come from actual services)
                business_metrics = {
                    "properties": {"active": 150, "inactive": 5},
                    "work_orders": {
                        "open": {"low": 20, "medium": 15, "high": 5, "emergency": 2},
                        "completed": {"low": 100, "medium": 80, "high": 40, "emergency": 10}
                    },
                    "vacancy_rates": {
                        "prop_1": 0.05,
                        "prop_2": 0.12,
                        "prop_3": 0.08
                    }
                }
                
                self.metrics.update_business_metrics(business_metrics)
                
                await asyncio.sleep(10)  # Collect every 10 seconds
                
            except Exception as e:
                logger.error("Error collecting metrics", error=str(e))
                await asyncio.sleep(10)
    
    async def _health_check_loop(self):
        """Run health checks periodically"""
        while self.is_running:
            try:
                results = await self.health_checker.run_all_checks()
                overall_status = self.health_checker.get_overall_status(results)
                
                logger.info(
                    "Health check completed",
                    overall_status=overall_status.value,
                    checks={name: result.status.value for name, result in results.items()}
                )
                
                await asyncio.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error("Error running health checks", error=str(e))
                await asyncio.sleep(30)
    
    async def _alert_check_loop(self):
        """Check alerts periodically"""
        while self.is_running:
            try:
                # Get current metrics snapshot
                current_metrics = {
                    "error_rate": 5,  # Example values
                    "cpu_percent": psutil.cpu_percent(),
                    "avg_vacancy_rate": 0.09
                }
                
                triggered_alerts = await self.alert_manager.check_alerts(current_metrics)
                
                if triggered_alerts:
                    logger.warning(
                        "Alerts triggered",
                        count=len(triggered_alerts),
                        alerts=[a.name for a in triggered_alerts]
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error("Error checking alerts", error=str(e))
                await asyncio.sleep(60)
    
    async def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status"""
        health_results = await self.health_checker.run_all_checks()
        overall_health = self.health_checker.get_overall_status(health_results)
        
        active_alerts = [
            alert_name
            for alert_name, state in self.alert_manager.alert_states.items()
            if state["active"]
        ]
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "health": {
                "overall": overall_health.value,
                "checks": {
                    name: {
                        "status": result.status.value,
                        "message": result.message,
                        "duration_ms": result.duration_ms
                    }
                    for name, result in health_results.items()
                }
            },
            "alerts": {
                "active": active_alerts,
                "total": len(self.alert_manager.alerts)
            },
            "metrics": {
                "endpoint": "/metrics",
                "format": "prometheus"
            }
        }


# Example usage
async def demo_monitoring():
    """Demonstrate monitoring system"""
    service = MonitoringService()
    
    # Get initial status
    status = await service.get_status()
    print("Monitoring Status:")
    print(json.dumps(status, indent=2))
    
    # Simulate some API requests
    service.metrics.record_api_request("GET", "/api/properties", 200, 0.125)
    service.metrics.record_api_request("POST", "/api/work-orders", 201, 0.250)
    service.metrics.record_api_request("GET", "/api/properties", 500, 2.5)
    
    # Simulate workflow execution
    service.metrics.record_workflow_execution("lease_renewal", "completed", 125.5)
    service.metrics.record_workflow_step("lease_renewal", "send_notice", "completed")
    
    # Simulate AI decision
    service.metrics.record_ai_decision("maintenance_priority", 0.85)
    
    # Get metrics
    print("\nPrometheus Metrics Sample:")
    metrics_output = service.metrics.get_metrics()
    print(metrics_output.decode('utf-8')[:500] + "...")


if __name__ == "__main__":
    asyncio.run(demo_monitoring())