"""
AI Workflow Optimizer
Machine learning-powered workflow optimization with predictive analytics
"""

import asyncio
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import defaultdict, Counter
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import joblib
import hashlib

from webhook_workflow_engine import WebhookWorkflowEngine, WorkflowPriority
from rentvine_webhook_handler import WebhookEventType
from cache import CacheManager
from distributed_tracing import TracingManager
from production_monitoring import MetricsCollector

logger = logging.getLogger(__name__)


class OptimizationStrategy(Enum):
    """Workflow optimization strategies"""
    PATH_OPTIMIZATION = "path_optimization"
    RESOURCE_ALLOCATION = "resource_allocation"
    PARALLEL_EXECUTION = "parallel_execution"
    PREDICTIVE_ROUTING = "predictive_routing"
    COST_OPTIMIZATION = "cost_optimization"


@dataclass
class WorkflowPattern:
    """Identified workflow pattern"""
    pattern_id: str
    pattern_type: str
    frequency: int
    average_duration: float
    success_rate: float
    common_paths: List[List[str]]
    bottlenecks: List[str]
    optimization_opportunities: List[Dict[str, Any]]


@dataclass
class WorkflowPrediction:
    """ML prediction for workflow execution"""
    workflow_id: str
    predicted_duration: float
    predicted_success_rate: float
    recommended_path: List[str]
    confidence_score: float
    risk_factors: List[str]


@dataclass
class ABTestConfiguration:
    """A/B test configuration for workflows"""
    test_id: str
    variant_a: Dict[str, Any]
    variant_b: Dict[str, Any]
    start_date: datetime
    end_date: Optional[datetime]
    traffic_split: float = 0.5
    success_metric: str = "completion_rate"
    minimum_sample_size: int = 100


class WorkflowOptimizer:
    """Main optimizer class with ML capabilities"""
    
    def __init__(
        self,
        webhook_engine: WebhookWorkflowEngine,
        cache_manager: CacheManager
    ):
        self.webhook_engine = webhook_engine
        self.cache = cache_manager
        self.metrics_collector = MetricsCollector()
        self.tracing = TracingManager()
        
        # ML models
        self.duration_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.success_predictor = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.path_optimizer = WorkflowPathOptimizer()
        self.pattern_analyzer = PatternAnalyzer()
        
        # A/B testing
        self.ab_tests: Dict[str, ABTestConfiguration] = {}
        self.ab_results: Dict[str, Dict[str, Any]] = defaultdict(dict)
        
        # Performance tracking
        self.workflow_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []
        
    async def predict_workflow_performance(
        self,
        workflow_type: str,
        workflow_data: Dict[str, Any]
    ) -> WorkflowPrediction:
        """Predict workflow performance using ML models"""
        
        # Extract features
        features = self._extract_workflow_features(workflow_type, workflow_data)
        
        # Check cache
        cache_key = f"prediction_{hashlib.md5(json.dumps(features, sort_keys=True).encode()).hexdigest()}"
        cached_prediction = await self.cache.get(cache_key)
        if cached_prediction:
            return WorkflowPrediction(**cached_prediction)
        
        # Make predictions
        try:
            # Prepare feature vector
            feature_vector = self._prepare_feature_vector(features)
            
            # Predict duration
            predicted_duration = self.duration_predictor.predict([feature_vector])[0]
            
            # Predict success rate
            success_probability = self.success_predictor.predict_proba([feature_vector])[0][1]
            
            # Get optimal path
            recommended_path = await self.path_optimizer.find_optimal_path(
                workflow_type, features
            )
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(features, success_probability)
            
            prediction = WorkflowPrediction(
                workflow_id=f"{workflow_type}_{datetime.utcnow().timestamp()}",
                predicted_duration=predicted_duration,
                predicted_success_rate=success_probability,
                recommended_path=recommended_path,
                confidence_score=self._calculate_confidence(features),
                risk_factors=risk_factors
            )
            
            # Cache prediction
            await self.cache.set(cache_key, prediction.__dict__, ttl_seconds=3600)
            
            return prediction
            
        except Exception as e:
            logger.error(f"Prediction failed: {e}")
            # Return default prediction
            return WorkflowPrediction(
                workflow_id=f"{workflow_type}_{datetime.utcnow().timestamp()}",
                predicted_duration=300.0,  # Default 5 minutes
                predicted_success_rate=0.8,
                recommended_path=["start", "process", "complete"],
                confidence_score=0.5,
                risk_factors=["prediction_unavailable"]
            )
    
    async def optimize_workflow_path(
        self,
        workflow_id: str,
        current_path: List[str],
        optimization_strategy: OptimizationStrategy = OptimizationStrategy.PATH_OPTIMIZATION
    ) -> Dict[str, Any]:
        """Dynamically optimize workflow execution path"""
        
        trace_id = self.tracing.start_trace("workflow_optimization")
        
        try:
            optimization_result = {
                "workflow_id": workflow_id,
                "original_path": current_path,
                "optimization_strategy": optimization_strategy.value,
                "timestamp": datetime.utcnow()
            }
            
            if optimization_strategy == OptimizationStrategy.PATH_OPTIMIZATION:
                # Find shortest/most efficient path
                optimized_path = await self.path_optimizer.optimize_path(
                    current_path, self.workflow_history
                )
                optimization_result["optimized_path"] = optimized_path
                optimization_result["estimated_improvement"] = self._estimate_improvement(
                    current_path, optimized_path
                )
                
            elif optimization_strategy == OptimizationStrategy.PARALLEL_EXECUTION:
                # Identify parallelizable steps
                parallel_groups = self._identify_parallel_steps(current_path)
                optimization_result["parallel_groups"] = parallel_groups
                optimization_result["estimated_speedup"] = len(parallel_groups) / len(current_path)
                
            elif optimization_strategy == OptimizationStrategy.PREDICTIVE_ROUTING:
                # Use ML to predict best next steps
                next_steps = await self._predict_next_steps(workflow_id, current_path)
                optimization_result["predicted_next_steps"] = next_steps
                optimization_result["confidence"] = 0.85  # Placeholder
                
            elif optimization_strategy == OptimizationStrategy.COST_OPTIMIZATION:
                # Optimize for cost efficiency
                cost_optimized_path = await self._optimize_for_cost(current_path)
                optimization_result["cost_optimized_path"] = cost_optimized_path
                optimization_result["estimated_cost_reduction"] = 0.2  # 20% reduction
                
            # Record optimization
            self.optimization_history.append(optimization_result)
            
            # Update metrics
            self.metrics_collector.record_metric(
                "workflow_optimization",
                {
                    "workflow_id": workflow_id,
                    "strategy": optimization_strategy.value,
                    "improvement": optimization_result.get("estimated_improvement", 0)
                }
            )
            
            return optimization_result
            
        finally:
            self.tracing.end_trace(trace_id)
    
    async def analyze_workflow_patterns(
        self,
        time_window: timedelta = timedelta(days=30)
    ) -> List[WorkflowPattern]:
        """Analyze historical patterns to identify optimization opportunities"""
        
        # Filter recent workflow history
        cutoff_date = datetime.utcnow() - time_window
        recent_workflows = [
            w for w in self.workflow_history
            if w.get("timestamp", datetime.utcnow()) > cutoff_date
        ]
        
        if not recent_workflows:
            return []
        
        # Analyze patterns
        patterns = await self.pattern_analyzer.analyze(recent_workflows)
        
        # Identify optimization opportunities for each pattern
        for pattern in patterns:
            pattern.optimization_opportunities = self._identify_optimizations(pattern)
            
        return patterns
    
    async def create_ab_test(
        self,
        test_name: str,
        workflow_type: str,
        variant_a_config: Dict[str, Any],
        variant_b_config: Dict[str, Any],
        duration_days: int = 14
    ) -> ABTestConfiguration:
        """Create A/B test for workflow variations"""
        
        test_config = ABTestConfiguration(
            test_id=f"ab_test_{test_name}_{datetime.utcnow().timestamp()}",
            variant_a=variant_a_config,
            variant_b=variant_b_config,
            start_date=datetime.utcnow(),
            end_date=datetime.utcnow() + timedelta(days=duration_days)
        )
        
        self.ab_tests[test_config.test_id] = test_config
        
        logger.info(f"Created A/B test: {test_config.test_id}")
        
        return test_config
    
    async def execute_with_ab_test(
        self,
        workflow_id: str,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute workflow with A/B testing if applicable"""
        
        # Check for active A/B tests
        active_test = self._get_active_test(workflow_data.get("type"))
        
        if not active_test:
            # Normal execution
            return await self.webhook_engine.process_workflow(workflow_data)
        
        # Determine variant
        variant = self._select_variant(active_test)
        
        # Execute with variant configuration
        if variant == "A":
            config = active_test.variant_a
        else:
            config = active_test.variant_b
            
        # Apply variant configuration
        modified_data = {**workflow_data, **config}
        
        # Execute workflow
        start_time = datetime.utcnow()
        result = await self.webhook_engine.process_workflow(modified_data)
        duration = (datetime.utcnow() - start_time).total_seconds()
        
        # Record A/B test result
        test_result = {
            "workflow_id": workflow_id,
            "variant": variant,
            "success": result.get("success", False),
            "duration": duration,
            "timestamp": datetime.utcnow()
        }
        
        if active_test.test_id not in self.ab_results:
            self.ab_results[active_test.test_id] = {
                "A": [],
                "B": []
            }
            
        self.ab_results[active_test.test_id][variant].append(test_result)
        
        # Check if test should conclude
        await self._check_test_completion(active_test)
        
        return result
    
    async def get_workflow_kpis(self) -> Dict[str, Any]:
        """Calculate and return workflow KPIs"""
        
        if not self.workflow_history:
            return {
                "total_workflows": 0,
                "average_duration": 0,
                "success_rate": 0,
                "optimization_impact": 0
            }
        
        # Calculate KPIs
        total_workflows = len(self.workflow_history)
        successful_workflows = sum(
            1 for w in self.workflow_history
            if w.get("success", False)
        )
        
        durations = [
            w.get("duration", 0) for w in self.workflow_history
            if w.get("duration") is not None
        ]
        
        # Calculate optimization impact
        optimized_workflows = [
            w for w in self.workflow_history
            if w.get("optimized", False)
        ]
        
        optimization_impact = 0
        if optimized_workflows:
            avg_optimized_duration = np.mean([
                w.get("duration", 0) for w in optimized_workflows
            ])
            avg_normal_duration = np.mean([
                w.get("duration", 0) for w in self.workflow_history
                if not w.get("optimized", False)
            ])
            
            if avg_normal_duration > 0:
                optimization_impact = (
                    (avg_normal_duration - avg_optimized_duration) / avg_normal_duration
                )
        
        kpis = {
            "total_workflows": total_workflows,
            "average_duration": np.mean(durations) if durations else 0,
            "success_rate": successful_workflows / total_workflows if total_workflows > 0 else 0,
            "optimization_impact": optimization_impact,
            "workflows_by_type": Counter(
                w.get("type", "unknown") for w in self.workflow_history
            ),
            "average_duration_by_type": self._calculate_avg_duration_by_type(),
            "peak_hours": self._identify_peak_hours(),
            "bottleneck_steps": self._identify_bottlenecks()
        }
        
        return kpis
    
    async def train_models(self, training_data: Optional[List[Dict[str, Any]]] = None):
        """Train or retrain ML models with workflow data"""
        
        if training_data is None:
            training_data = self.workflow_history
            
        if len(training_data) < 100:
            logger.warning("Insufficient training data for model training")
            return
        
        # Prepare training data
        X = []
        y_duration = []
        y_success = []
        
        for workflow in training_data:
            features = self._extract_workflow_features(
                workflow.get("type", "unknown"),
                workflow
            )
            feature_vector = self._prepare_feature_vector(features)
            
            X.append(feature_vector)
            y_duration.append(workflow.get("duration", 300))
            y_success.append(1 if workflow.get("success", False) else 0)
        
        X = np.array(X)
        y_duration = np.array(y_duration)
        y_success = np.array(y_success)
        
        # Train models
        self.duration_predictor.fit(X, y_duration)
        self.success_predictor.fit(X, y_success)
        
        # Save models
        joblib.dump(self.duration_predictor, "models/duration_predictor.pkl")
        joblib.dump(self.success_predictor, "models/success_predictor.pkl")
        
        logger.info("ML models trained successfully")
    
    def _extract_workflow_features(
        self,
        workflow_type: str,
        workflow_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract features for ML models"""
        
        features = {
            "workflow_type": workflow_type,
            "priority": workflow_data.get("priority", "normal"),
            "data_size": len(json.dumps(workflow_data)),
            "hour_of_day": datetime.utcnow().hour,
            "day_of_week": datetime.utcnow().weekday(),
            "has_attachments": "attachments" in workflow_data,
            "step_count": len(workflow_data.get("steps", [])),
            "complexity_score": self._calculate_complexity(workflow_data)
        }
        
        # Add historical features if available
        historical_stats = self._get_historical_stats(workflow_type)
        features.update(historical_stats)
        
        return features
    
    def _prepare_feature_vector(self, features: Dict[str, Any]) -> List[float]:
        """Convert features to numerical vector"""
        
        # Define feature order
        feature_order = [
            "priority_score",
            "data_size",
            "hour_of_day",
            "day_of_week",
            "has_attachments",
            "step_count",
            "complexity_score",
            "historical_success_rate",
            "historical_avg_duration"
        ]
        
        # Convert categorical features
        priority_map = {"low": 0, "normal": 1, "high": 2, "emergency": 3}
        
        vector = []
        for feature in feature_order:
            if feature == "priority_score":
                vector.append(priority_map.get(features.get("priority", "normal"), 1))
            elif feature == "has_attachments":
                vector.append(1.0 if features.get(feature, False) else 0.0)
            else:
                vector.append(float(features.get(feature, 0)))
                
        return vector
    
    def _identify_risk_factors(
        self,
        features: Dict[str, Any],
        success_probability: float
    ) -> List[str]:
        """Identify potential risk factors"""
        
        risk_factors = []
        
        if success_probability < 0.7:
            risk_factors.append("low_success_probability")
            
        if features.get("complexity_score", 0) > 0.8:
            risk_factors.append("high_complexity")
            
        if features.get("historical_success_rate", 1.0) < 0.8:
            risk_factors.append("poor_historical_performance")
            
        if features.get("step_count", 0) > 10:
            risk_factors.append("many_steps")
            
        return risk_factors
    
    def _calculate_complexity(self, workflow_data: Dict[str, Any]) -> float:
        """Calculate workflow complexity score"""
        
        complexity = 0.0
        
        # Factor in number of steps
        step_count = len(workflow_data.get("steps", []))
        complexity += min(step_count / 20, 0.5)  # Max 0.5 for steps
        
        # Factor in conditional logic
        conditions = str(workflow_data).count("if") + str(workflow_data).count("condition")
        complexity += min(conditions / 10, 0.3)  # Max 0.3 for conditions
        
        # Factor in integrations
        integrations = workflow_data.get("integrations", [])
        complexity += min(len(integrations) / 5, 0.2)  # Max 0.2 for integrations
        
        return min(complexity, 1.0)


class WorkflowPathOptimizer:
    """Specialized optimizer for workflow paths"""
    
    def __init__(self):
        self.path_cache: Dict[str, List[str]] = {}
        self.transition_matrix: Dict[str, Dict[str, float]] = defaultdict(dict)
        
    async def find_optimal_path(
        self,
        workflow_type: str,
        features: Dict[str, Any]
    ) -> List[str]:
        """Find optimal execution path"""
        
        # Check cache
        cache_key = f"{workflow_type}_{hashlib.md5(json.dumps(features, sort_keys=True).encode()).hexdigest()}"
        if cache_key in self.path_cache:
            return self.path_cache[cache_key]
        
        # Build path based on workflow type
        base_path = self._get_base_path(workflow_type)
        
        # Optimize based on features
        if features.get("priority") == "emergency":
            # Skip non-essential steps
            base_path = [step for step in base_path if "optional" not in step]
            
        if features.get("has_attachments"):
            # Add attachment processing
            base_path.insert(1, "process_attachments")
            
        # Cache result
        self.path_cache[cache_key] = base_path
        
        return base_path
    
    async def optimize_path(
        self,
        current_path: List[str],
        historical_data: List[Dict[str, Any]]
    ) -> List[str]:
        """Optimize existing path based on historical data"""
        
        # Build transition probabilities
        self._build_transition_matrix(historical_data)
        
        # Find optimal path using dynamic programming
        optimized_path = self._find_shortest_path(
            current_path[0] if current_path else "start",
            current_path[-1] if current_path else "complete"
        )
        
        return optimized_path or current_path
    
    def _get_base_path(self, workflow_type: str) -> List[str]:
        """Get base path for workflow type"""
        
        base_paths = {
            "maintenance": ["start", "assess", "schedule", "assign", "execute", "verify", "complete"],
            "tenant_request": ["start", "receive", "categorize", "process", "respond", "complete"],
            "payment": ["start", "validate", "process", "record", "notify", "complete"],
            "inspection": ["start", "schedule", "conduct", "document", "followup", "complete"]
        }
        
        return base_paths.get(workflow_type, ["start", "process", "complete"])
    
    def _build_transition_matrix(self, historical_data: List[Dict[str, Any]]):
        """Build transition probability matrix"""
        
        for workflow in historical_data:
            path = workflow.get("path", [])
            duration = workflow.get("duration", 300)
            success = workflow.get("success", True)
            
            # Weight by success and inverse duration
            weight = (1.0 if success else 0.5) / (duration / 300)
            
            for i in range(len(path) - 1):
                from_step = path[i]
                to_step = path[i + 1]
                
                if to_step not in self.transition_matrix[from_step]:
                    self.transition_matrix[from_step][to_step] = 0
                    
                self.transition_matrix[from_step][to_step] += weight
    
    def _find_shortest_path(self, start: str, end: str) -> Optional[List[str]]:
        """Find shortest path using Dijkstra's algorithm"""
        
        # Simplified implementation
        if not self.transition_matrix:
            return None
            
        # Build graph
        graph = {}
        for from_step, transitions in self.transition_matrix.items():
            graph[from_step] = {
                to_step: 1 / weight if weight > 0 else float('inf')
                for to_step, weight in transitions.items()
            }
            
        # Find path (simplified - would use proper Dijkstra in production)
        path = [start]
        current = start
        
        while current != end and current in graph:
            next_steps = graph.get(current, {})
            if not next_steps:
                break
                
            # Choose step with highest weight (lowest cost)
            next_step = min(next_steps.items(), key=lambda x: x[1])[0]
            path.append(next_step)
            current = next_step
            
            if len(path) > 20:  # Prevent infinite loops
                break
                
        return path if path[-1] == end else None


class PatternAnalyzer:
    """Analyze workflow patterns for insights"""
    
    def __init__(self):
        self.clustering_model = KMeans(n_clusters=5, random_state=42)
        self.scaler = StandardScaler()
        
    async def analyze(self, workflows: List[Dict[str, Any]]) -> List[WorkflowPattern]:
        """Analyze workflows to identify patterns"""
        
        if len(workflows) < 10:
            return []
        
        # Extract features for clustering
        features = []
        for workflow in workflows:
            feature_vector = [
                workflow.get("duration", 300),
                len(workflow.get("path", [])),
                1 if workflow.get("success", False) else 0,
                workflow.get("retry_count", 0)
            ]
            features.append(feature_vector)
            
        # Scale features
        features_scaled = self.scaler.fit_transform(features)
        
        # Cluster workflows
        clusters = self.clustering_model.fit_predict(features_scaled)
        
        # Analyze each cluster
        patterns = []
        for cluster_id in range(self.clustering_model.n_clusters):
            cluster_workflows = [
                w for i, w in enumerate(workflows)
                if clusters[i] == cluster_id
            ]
            
            if not cluster_workflows:
                continue
                
            pattern = self._analyze_cluster(cluster_id, cluster_workflows)
            patterns.append(pattern)
            
        return patterns
    
    def _analyze_cluster(
        self,
        cluster_id: int,
        workflows: List[Dict[str, Any]]
    ) -> WorkflowPattern:
        """Analyze a cluster of workflows"""
        
        # Calculate statistics
        durations = [w.get("duration", 300) for w in workflows]
        success_count = sum(1 for w in workflows if w.get("success", False))
        
        # Find common paths
        paths = [tuple(w.get("path", [])) for w in workflows]
        path_counter = Counter(paths)
        common_paths = [
            list(path) for path, count in path_counter.most_common(3)
        ]
        
        # Identify bottlenecks
        step_durations = defaultdict(list)
        for workflow in workflows:
            steps = workflow.get("step_durations", {})
            for step, duration in steps.items():
                step_durations[step].append(duration)
                
        bottlenecks = []
        for step, durations in step_durations.items():
            if np.mean(durations) > np.percentile(list(step_durations.values()), 75):
                bottlenecks.append(step)
        
        return WorkflowPattern(
            pattern_id=f"pattern_{cluster_id}",
            pattern_type=self._classify_pattern(workflows),
            frequency=len(workflows),
            average_duration=np.mean(durations),
            success_rate=success_count / len(workflows) if workflows else 0,
            common_paths=common_paths,
            bottlenecks=bottlenecks,
            optimization_opportunities=[]
        )
    
    def _classify_pattern(self, workflows: List[Dict[str, Any]]) -> str:
        """Classify the type of pattern"""
        
        # Simple classification based on characteristics
        avg_duration = np.mean([w.get("duration", 300) for w in workflows])
        avg_steps = np.mean([len(w.get("path", [])) for w in workflows])
        
        if avg_duration < 60:
            return "quick_workflow"
        elif avg_duration > 600:
            return "long_running"
        elif avg_steps > 10:
            return "complex_workflow"
        else:
            return "standard_workflow"