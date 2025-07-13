"""
Enhanced Super Claude Orchestrator
Advanced swarm coordination with ML-powered optimization and dynamic scaling
"""

import asyncio
import json
import yaml
import numpy as np
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import random
import logging
from collections import defaultdict, deque
import threading
from concurrent.futures import ThreadPoolExecutor
import multiprocessing as mp

from super_claude_swarm_orchestrator import (
    SwarmObjective, SwarmTask, SwarmAgent, SuperClaudeSwarmOrchestrator
)
from distributed_tracing import TracingManager
from production_monitoring import MetricsCollector
from cache import CacheManager

logger = logging.getLogger(__name__)


class LoadBalancingStrategy(Enum):
    """Load balancing strategies for agent distribution"""
    ROUND_ROBIN = "round_robin"
    LEAST_LOADED = "least_loaded"
    CAPABILITY_BASED = "capability_based"
    PERFORMANCE_WEIGHTED = "performance_weighted"
    ADAPTIVE_ML = "adaptive_ml"


class ConsensusAlgorithm(Enum):
    """Consensus algorithms for swarm decision making"""
    MAJORITY_VOTE = "majority_vote"
    WEIGHTED_VOTE = "weighted_vote"
    BYZANTINE_FAULT_TOLERANT = "byzantine_fault_tolerant"
    RAFT = "raft"
    NEURAL_CONSENSUS = "neural_consensus"


@dataclass
class AgentPerformanceMetrics:
    """Detailed performance metrics for agents"""
    agent_id: str
    tasks_completed: int = 0
    success_rate: float = 1.0
    average_task_time: float = 0.0
    resource_utilization: float = 0.0
    collaboration_score: float = 1.0
    specialization_scores: Dict[str, float] = field(default_factory=dict)
    recent_performance: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def update_metrics(self, task_result: Dict[str, Any]):
        """Update metrics based on task result"""
        self.tasks_completed += 1
        success = task_result.get("success", True)
        duration = task_result.get("duration", 0)
        
        self.recent_performance.append({
            "success": success,
            "duration": duration,
            "timestamp": datetime.utcnow()
        })
        
        # Calculate moving average success rate
        recent_successes = sum(1 for p in self.recent_performance if p["success"])
        self.success_rate = recent_successes / len(self.recent_performance)
        
        # Update average task time
        durations = [p["duration"] for p in self.recent_performance if p["duration"] > 0]
        if durations:
            self.average_task_time = np.mean(durations)


@dataclass
class SwarmCommunicationProtocol:
    """Inter-agent communication protocol"""
    protocol_id: str
    message_type: str
    sender_id: str
    recipient_ids: List[str]
    payload: Dict[str, Any]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    requires_ack: bool = False
    priority: str = "normal"


class EnhancedSwarmCoordinator:
    """Enhanced coordinator with advanced algorithms"""
    
    def __init__(self, base_orchestrator: SuperClaudeSwarmOrchestrator):
        self.base_orchestrator = base_orchestrator
        self.agent_metrics: Dict[str, AgentPerformanceMetrics] = {}
        self.communication_bus: asyncio.Queue = asyncio.Queue()
        self.consensus_history: List[Dict[str, Any]] = []
        self.load_balancer = LoadBalancer()
        self.scaling_manager = DynamicScalingManager()
        self.optimization_engine = PerformanceOptimizer()
        
    async def distribute_task_with_load_balancing(
        self,
        task: SwarmTask,
        agents: List[SwarmAgent],
        strategy: LoadBalancingStrategy = LoadBalancingStrategy.ADAPTIVE_ML
    ) -> Dict[str, List[SwarmAgent]]:
        """Distribute tasks using advanced load balancing"""
        
        # Get agent performance metrics
        agent_states = await self._get_agent_states(agents)
        
        if strategy == LoadBalancingStrategy.ADAPTIVE_ML:
            # Use ML model to predict best agent assignment
            assignments = await self.optimization_engine.predict_optimal_assignment(
                task, agents, agent_states, self.agent_metrics
            )
        elif strategy == LoadBalancingStrategy.PERFORMANCE_WEIGHTED:
            # Weight by historical performance
            assignments = self._performance_weighted_assignment(task, agents)
        elif strategy == LoadBalancingStrategy.CAPABILITY_BASED:
            # Match capabilities to task requirements
            assignments = self._capability_based_assignment(task, agents)
        else:
            # Fallback to simple strategies
            assignments = self.load_balancer.assign(task, agents, strategy)
            
        return assignments
    
    async def coordinate_swarm_consensus(
        self,
        decision_context: Dict[str, Any],
        participating_agents: List[SwarmAgent],
        algorithm: ConsensusAlgorithm = ConsensusAlgorithm.NEURAL_CONSENSUS
    ) -> Dict[str, Any]:
        """Coordinate consensus among swarm agents"""
        
        consensus_id = f"consensus_{datetime.utcnow().timestamp()}"
        
        # Broadcast decision context to all agents
        await self._broadcast_message(
            SwarmCommunicationProtocol(
                protocol_id=consensus_id,
                message_type="consensus_request",
                sender_id="coordinator",
                recipient_ids=[a.agent_id for a in participating_agents],
                payload=decision_context,
                requires_ack=True,
                priority="high"
            )
        )
        
        # Collect votes/opinions
        votes = await self._collect_agent_votes(
            consensus_id, participating_agents, timeout=30
        )
        
        # Apply consensus algorithm
        if algorithm == ConsensusAlgorithm.NEURAL_CONSENSUS:
            result = await self._neural_consensus(votes, decision_context)
        elif algorithm == ConsensusAlgorithm.BYZANTINE_FAULT_TOLERANT:
            result = self._byzantine_consensus(votes)
        elif algorithm == ConsensusAlgorithm.RAFT:
            result = await self._raft_consensus(votes, participating_agents)
        else:
            result = self._simple_consensus(votes, algorithm)
            
        # Record consensus outcome
        self.consensus_history.append({
            "consensus_id": consensus_id,
            "algorithm": algorithm.value,
            "participants": len(participating_agents),
            "result": result,
            "timestamp": datetime.utcnow()
        })
        
        return result
    
    async def optimize_swarm_performance(self) -> Dict[str, Any]:
        """Real-time performance optimization"""
        
        optimization_results = {
            "timestamp": datetime.utcnow(),
            "optimizations_applied": []
        }
        
        # Analyze current performance
        performance_analysis = await self.optimization_engine.analyze_swarm_performance(
            self.agent_metrics, self.consensus_history
        )
        
        # Apply optimization strategies
        if performance_analysis["bottlenecks"]:
            # Address bottlenecks
            for bottleneck in performance_analysis["bottlenecks"]:
                optimization = await self._resolve_bottleneck(bottleneck)
                optimization_results["optimizations_applied"].append(optimization)
        
        if performance_analysis["underperforming_agents"]:
            # Rebalance or retrain underperforming agents
            for agent_id in performance_analysis["underperforming_agents"]:
                optimization = await self._optimize_agent(agent_id)
                optimization_results["optimizations_applied"].append(optimization)
        
        # Update load balancing strategy if needed
        if performance_analysis["recommended_strategy"]:
            self.load_balancer.update_strategy(
                performance_analysis["recommended_strategy"]
            )
            
        return optimization_results
    
    async def scale_swarm_dynamically(
        self,
        current_workload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Dynamically scale swarm based on workload"""
        
        scaling_decision = await self.scaling_manager.analyze_scaling_needs(
            current_workload,
            self.agent_metrics,
            self.base_orchestrator.available_agents
        )
        
        scaling_result = {
            "timestamp": datetime.utcnow(),
            "current_agents": len(self.base_orchestrator.available_agents),
            "scaling_action": scaling_decision["action"],
            "target_agents": scaling_decision["target_count"]
        }
        
        if scaling_decision["action"] == "scale_up":
            # Add more agents
            new_agents = await self._spawn_agents(
                scaling_decision["target_count"] - len(self.base_orchestrator.available_agents),
                scaling_decision["required_capabilities"]
            )
            scaling_result["agents_added"] = len(new_agents)
            
        elif scaling_decision["action"] == "scale_down":
            # Remove idle agents
            removed_agents = await self._retire_agents(
                len(self.base_orchestrator.available_agents) - scaling_decision["target_count"]
            )
            scaling_result["agents_removed"] = len(removed_agents)
            
        return scaling_result
    
    async def _broadcast_message(self, protocol: SwarmCommunicationProtocol):
        """Broadcast message to agents"""
        await self.communication_bus.put(protocol)
        
    async def _collect_agent_votes(
        self,
        consensus_id: str,
        agents: List[SwarmAgent],
        timeout: int
    ) -> List[Dict[str, Any]]:
        """Collect votes from agents for consensus"""
        votes = []
        
        try:
            async with asyncio.timeout(timeout):
                while len(votes) < len(agents):
                    message = await self.communication_bus.get()
                    if (message.message_type == "consensus_vote" and
                        message.payload.get("consensus_id") == consensus_id):
                        votes.append({
                            "agent_id": message.sender_id,
                            "vote": message.payload.get("vote"),
                            "confidence": message.payload.get("confidence", 1.0),
                            "reasoning": message.payload.get("reasoning", "")
                        })
        except asyncio.TimeoutError:
            logger.warning(f"Consensus timeout - received {len(votes)}/{len(agents)} votes")
            
        return votes
    
    async def _neural_consensus(
        self,
        votes: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Neural network-based consensus algorithm"""
        # Simplified neural consensus - in production would use trained model
        
        # Extract features from votes
        vote_values = [v["vote"] for v in votes]
        confidences = [v["confidence"] for v in votes]
        
        # Weight votes by confidence and agent performance
        weighted_votes = {}
        for vote in votes:
            agent_metrics = self.agent_metrics.get(vote["agent_id"])
            weight = vote["confidence"]
            if agent_metrics:
                weight *= agent_metrics.success_rate
                
            vote_value = vote["vote"]
            if vote_value not in weighted_votes:
                weighted_votes[vote_value] = 0
            weighted_votes[vote_value] += weight
            
        # Select highest weighted vote
        consensus_value = max(weighted_votes.items(), key=lambda x: x[1])[0]
        
        return {
            "consensus": consensus_value,
            "confidence": weighted_votes[consensus_value] / sum(weighted_votes.values()),
            "algorithm": "neural_consensus",
            "participation_rate": len(votes) / len(self.base_orchestrator.available_agents)
        }
    
    def _performance_weighted_assignment(
        self,
        task: SwarmTask,
        agents: List[SwarmAgent]
    ) -> Dict[str, List[SwarmAgent]]:
        """Assign agents based on performance history"""
        
        # Score agents for this task type
        agent_scores = []
        for agent in agents:
            metrics = self.agent_metrics.get(agent.agent_id)
            if metrics:
                # Consider specialization and general performance
                specialization = metrics.specialization_scores.get(
                    task.objective.value, 0.5
                )
                score = (
                    metrics.success_rate * 0.4 +
                    specialization * 0.4 +
                    (1 / (metrics.average_task_time + 1)) * 0.2
                )
            else:
                score = 0.5  # Default score for new agents
                
            agent_scores.append((agent, score))
            
        # Sort by score and assign top performers
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Determine number of agents needed based on complexity
        num_agents = min(
            max(1, int(task.complexity_score * 3)),
            len(agents)
        )
        
        return {
            "primary": [agent for agent, _ in agent_scores[:num_agents]],
            "backup": [agent for agent, _ in agent_scores[num_agents:num_agents+2]]
        }


class LoadBalancer:
    """Advanced load balancing for agent tasks"""
    
    def __init__(self):
        self.round_robin_index = 0
        self.agent_loads: Dict[str, float] = defaultdict(float)
        
    def assign(
        self,
        task: SwarmTask,
        agents: List[SwarmAgent],
        strategy: LoadBalancingStrategy
    ) -> Dict[str, List[SwarmAgent]]:
        """Assign agents based on strategy"""
        
        if strategy == LoadBalancingStrategy.ROUND_ROBIN:
            return self._round_robin_assign(task, agents)
        elif strategy == LoadBalancingStrategy.LEAST_LOADED:
            return self._least_loaded_assign(task, agents)
        else:
            # Default to round robin
            return self._round_robin_assign(task, agents)
            
    def _round_robin_assign(
        self,
        task: SwarmTask,
        agents: List[SwarmAgent]
    ) -> Dict[str, List[SwarmAgent]]:
        """Simple round-robin assignment"""
        
        num_agents = max(1, int(task.complexity_score * 2))
        assigned = []
        
        for _ in range(min(num_agents, len(agents))):
            assigned.append(agents[self.round_robin_index % len(agents)])
            self.round_robin_index += 1
            
        return {"primary": assigned, "backup": []}
    
    def _least_loaded_assign(
        self,
        task: SwarmTask,
        agents: List[SwarmAgent]
    ) -> Dict[str, List[SwarmAgent]]:
        """Assign to least loaded agents"""
        
        # Sort agents by current load
        sorted_agents = sorted(
            agents,
            key=lambda a: self.agent_loads.get(a.agent_id, 0)
        )
        
        num_agents = max(1, int(task.complexity_score * 2))
        assigned = sorted_agents[:min(num_agents, len(agents))]
        
        # Update loads
        for agent in assigned:
            self.agent_loads[agent.agent_id] += task.complexity_score
            
        return {"primary": assigned, "backup": []}


class DynamicScalingManager:
    """Manages dynamic scaling of swarm"""
    
    def __init__(self):
        self.scaling_history: List[Dict[str, Any]] = []
        self.min_agents = 3
        self.max_agents = 50
        self.scale_up_threshold = 0.8  # 80% utilization
        self.scale_down_threshold = 0.3  # 30% utilization
        
    async def analyze_scaling_needs(
        self,
        workload: Dict[str, Any],
        agent_metrics: Dict[str, AgentPerformanceMetrics],
        current_agents: List[SwarmAgent]
    ) -> Dict[str, Any]:
        """Analyze if scaling is needed"""
        
        # Calculate current utilization
        active_agents = sum(
            1 for agent in current_agents
            if agent.current_task is not None
        )
        utilization = active_agents / len(current_agents) if current_agents else 0
        
        # Calculate workload trends
        pending_tasks = workload.get("pending_tasks", 0)
        average_task_time = np.mean([
            m.average_task_time for m in agent_metrics.values()
        ]) if agent_metrics else 60  # Default 60 seconds
        
        # Predict future utilization
        predicted_time_to_complete = (pending_tasks * average_task_time) / len(current_agents)
        
        scaling_decision = {
            "action": "maintain",
            "target_count": len(current_agents),
            "current_utilization": utilization,
            "predicted_completion_time": predicted_time_to_complete
        }
        
        if utilization > self.scale_up_threshold or predicted_time_to_complete > 300:
            # Scale up
            scaling_decision["action"] = "scale_up"
            additional_agents = min(
                int((pending_tasks / 10) - len(current_agents)),
                self.max_agents - len(current_agents)
            )
            scaling_decision["target_count"] = len(current_agents) + additional_agents
            scaling_decision["required_capabilities"] = self._analyze_required_capabilities(
                workload
            )
            
        elif utilization < self.scale_down_threshold and len(current_agents) > self.min_agents:
            # Scale down
            scaling_decision["action"] = "scale_down"
            scaling_decision["target_count"] = max(
                self.min_agents,
                int(len(current_agents) * 0.7)
            )
            
        # Record decision
        self.scaling_history.append({
            "timestamp": datetime.utcnow(),
            "decision": scaling_decision,
            "workload": workload,
            "utilization": utilization
        })
        
        return scaling_decision
    
    def _analyze_required_capabilities(self, workload: Dict[str, Any]) -> List[str]:
        """Determine what capabilities are needed"""
        
        task_types = workload.get("task_types", {})
        required_capabilities = []
        
        # Map task types to capabilities
        capability_mapping = {
            "maintenance": ["technical_analysis", "scheduling"],
            "tenant_communication": ["natural_language", "empathy"],
            "financial": ["accounting", "reporting"],
            "emergency": ["crisis_management", "rapid_response"]
        }
        
        for task_type, count in task_types.items():
            if count > 0 and task_type in capability_mapping:
                required_capabilities.extend(capability_mapping[task_type])
                
        return list(set(required_capabilities))


class PerformanceOptimizer:
    """ML-powered performance optimization"""
    
    def __init__(self):
        self.optimization_history: List[Dict[str, Any]] = []
        self.performance_threshold = 0.7
        
    async def analyze_swarm_performance(
        self,
        agent_metrics: Dict[str, AgentPerformanceMetrics],
        consensus_history: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze overall swarm performance"""
        
        analysis = {
            "timestamp": datetime.utcnow(),
            "bottlenecks": [],
            "underperforming_agents": [],
            "recommended_strategy": None,
            "performance_score": 1.0
        }
        
        if not agent_metrics:
            return analysis
            
        # Calculate overall performance metrics
        success_rates = [m.success_rate for m in agent_metrics.values()]
        avg_success_rate = np.mean(success_rates)
        
        task_times = [m.average_task_time for m in agent_metrics.values()]
        avg_task_time = np.mean(task_times)
        
        # Identify underperforming agents
        for agent_id, metrics in agent_metrics.items():
            if metrics.success_rate < self.performance_threshold:
                analysis["underperforming_agents"].append(agent_id)
                
        # Identify bottlenecks
        if avg_task_time > 120:  # Tasks taking too long
            analysis["bottlenecks"].append({
                "type": "slow_processing",
                "severity": "high" if avg_task_time > 300 else "medium",
                "affected_agents": [
                    aid for aid, m in agent_metrics.items()
                    if m.average_task_time > avg_task_time * 1.5
                ]
            })
            
        # Analyze consensus efficiency
        if consensus_history:
            recent_consensus = consensus_history[-10:]
            avg_consensus_time = np.mean([
                c["timestamp"].timestamp() for c in recent_consensus
            ])
            if avg_consensus_time > 60:
                analysis["bottlenecks"].append({
                    "type": "slow_consensus",
                    "severity": "medium",
                    "recommendation": "switch_to_faster_algorithm"
                })
                
        # Calculate overall performance score
        analysis["performance_score"] = (
            avg_success_rate * 0.4 +
            min(1.0, 60 / avg_task_time) * 0.3 +
            (1 - len(analysis["underperforming_agents"]) / len(agent_metrics)) * 0.3
        )
        
        # Recommend optimization strategy
        if analysis["performance_score"] < 0.7:
            if len(analysis["underperforming_agents"]) > len(agent_metrics) * 0.3:
                analysis["recommended_strategy"] = LoadBalancingStrategy.PERFORMANCE_WEIGHTED
            else:
                analysis["recommended_strategy"] = LoadBalancingStrategy.ADAPTIVE_ML
                
        return analysis
    
    async def predict_optimal_assignment(
        self,
        task: SwarmTask,
        agents: List[SwarmAgent],
        agent_states: Dict[str, Any],
        agent_metrics: Dict[str, AgentPerformanceMetrics]
    ) -> Dict[str, List[SwarmAgent]]:
        """Use ML to predict optimal agent assignment"""
        
        # Simplified ML prediction - in production would use trained model
        
        # Feature extraction
        features = {
            "task_complexity": task.complexity_score,
            "task_type": task.objective.value,
            "task_priority": task.priority,
            "num_available_agents": len(agents),
            "avg_agent_performance": np.mean([
                agent_metrics.get(a.agent_id, AgentPerformanceMetrics(a.agent_id)).success_rate
                for a in agents
            ])
        }
        
        # Score each agent for this specific task
        agent_scores = []
        for agent in agents:
            metrics = agent_metrics.get(
                agent.agent_id,
                AgentPerformanceMetrics(agent.agent_id)
            )
            
            # Calculate compatibility score
            capability_match = sum(
                1 for cap in agent.capabilities
                if cap in str(task.description).lower()
            ) / len(agent.capabilities) if agent.capabilities else 0
            
            workload = 1.0 if agent.current_task else 0.0
            
            score = (
                metrics.success_rate * 0.3 +
                capability_match * 0.3 +
                (1 - workload) * 0.2 +
                metrics.collaboration_score * 0.2
            )
            
            agent_scores.append((agent, score))
            
        # Sort and select best agents
        agent_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Dynamic team size based on complexity
        team_size = max(1, min(
            int(task.complexity_score * 3),
            len(agents),
            5  # Max team size
        ))
        
        return {
            "primary": [agent for agent, _ in agent_scores[:team_size]],
            "backup": [agent for agent, _ in agent_scores[team_size:team_size+2]]
        }


class EnhancedSuperClaudeOrchestrator(SuperClaudeSwarmOrchestrator):
    """Enhanced orchestrator with all advanced features"""
    
    def __init__(self):
        super().__init__()
        self.enhanced_coordinator = EnhancedSwarmCoordinator(self)
        self.metrics_collector = MetricsCollector()
        self.tracing_manager = TracingManager()
        self.cache_manager = CacheManager()
        
    async def execute_with_optimization(
        self,
        task: SwarmTask,
        optimization_level: str = "high"
    ) -> Dict[str, Any]:
        """Execute task with full optimization stack"""
        
        trace_id = self.tracing_manager.start_trace("swarm_execution")
        
        try:
            # Check cache first
            cache_key = f"task_result_{task.task_id}"
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                return cached_result
                
            # Optimize swarm performance before execution
            if optimization_level == "high":
                await self.enhanced_coordinator.optimize_swarm_performance()
                
            # Distribute task with load balancing
            assignments = await self.enhanced_coordinator.distribute_task_with_load_balancing(
                task,
                self.available_agents,
                LoadBalancingStrategy.ADAPTIVE_ML
            )
            
            # Execute with monitoring
            result = await self._execute_with_monitoring(task, assignments)
            
            # Cache successful results
            if result.get("success"):
                await self.cache_manager.set(cache_key, result, ttl_seconds=3600)
                
            # Update metrics
            for agent_id in [a.agent_id for a in assignments["primary"]]:
                if agent_id in self.enhanced_coordinator.agent_metrics:
                    self.enhanced_coordinator.agent_metrics[agent_id].update_metrics(result)
                    
            return result
            
        finally:
            self.tracing_manager.end_trace(trace_id)
    
    async def _execute_with_monitoring(
        self,
        task: SwarmTask,
        assignments: Dict[str, List[SwarmAgent]]
    ) -> Dict[str, Any]:
        """Execute task with full monitoring"""
        
        start_time = datetime.utcnow()
        
        # Execute task using assigned agents
        primary_agents = assignments["primary"]
        
        # Create subtasks for each agent
        subtasks = []
        for agent in primary_agents:
            subtask = asyncio.create_task(
                agent.process_task(task, self.shared_memory)
            )
            subtasks.append(subtask)
            
        # Wait for completion with timeout
        try:
            results = await asyncio.gather(*subtasks, return_exceptions=True)
            
            # Aggregate results
            success = all(
                not isinstance(r, Exception) and r.get("success", False)
                for r in results
            )
            
            aggregated_result = {
                "success": success,
                "task_id": task.task_id,
                "duration": (datetime.utcnow() - start_time).total_seconds(),
                "agent_results": results,
                "assignments": {
                    "primary": [a.agent_id for a in primary_agents],
                    "backup": [a.agent_id for a in assignments.get("backup", [])]
                }
            }
            
            # Record metrics
            self.metrics_collector.record_metric(
                "swarm_task_execution",
                {
                    "task_id": task.task_id,
                    "success": success,
                    "duration": aggregated_result["duration"],
                    "num_agents": len(primary_agents)
                }
            )
            
            return aggregated_result
            
        except asyncio.TimeoutError:
            logger.error(f"Task {task.task_id} timed out")
            return {
                "success": False,
                "task_id": task.task_id,
                "error": "Task execution timed out",
                "duration": (datetime.utcnow() - start_time).total_seconds()
            }
    
    async def scale_swarm(self, workload_metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Scale swarm based on workload"""
        
        return await self.enhanced_coordinator.scale_swarm_dynamically(
            workload_metrics
        )
    
    async def get_swarm_consensus(
        self,
        decision_context: Dict[str, Any],
        consensus_type: ConsensusAlgorithm = ConsensusAlgorithm.NEURAL_CONSENSUS
    ) -> Dict[str, Any]:
        """Get consensus from swarm on a decision"""
        
        return await self.enhanced_coordinator.coordinate_swarm_consensus(
            decision_context,
            self.available_agents,
            consensus_type
        )
    
    async def get_performance_report(self) -> Dict[str, Any]:
        """Get comprehensive performance report"""
        
        agent_reports = {}
        for agent_id, metrics in self.enhanced_coordinator.agent_metrics.items():
            agent_reports[agent_id] = {
                "tasks_completed": metrics.tasks_completed,
                "success_rate": metrics.success_rate,
                "average_task_time": metrics.average_task_time,
                "specializations": metrics.specialization_scores
            }
            
        return {
            "timestamp": datetime.utcnow(),
            "total_agents": len(self.available_agents),
            "agent_performance": agent_reports,
            "consensus_history": len(self.enhanced_coordinator.consensus_history),
            "scaling_events": len(self.enhanced_coordinator.scaling_manager.scaling_history),
            "overall_performance": await self.enhanced_coordinator.optimization_engine.analyze_swarm_performance(
                self.enhanced_coordinator.agent_metrics,
                self.enhanced_coordinator.consensus_history
            )
        }