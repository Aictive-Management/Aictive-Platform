"""
Intelligent Caching with Machine Learning
ML-powered cache prediction and optimization for the Aictive platform
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
from collections import defaultdict, deque
import hashlib
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import redis.asyncio as redis
import joblib

from cache import CacheManager
from redis_caching_strategy import RedisCachingStrategy
from production_monitoring import MetricsCollector
from distributed_tracing import TracingManager

logger = logging.getLogger(__name__)


class CachingStrategy(Enum):
    """Advanced caching strategies"""
    PREDICTIVE = "predictive"
    ADAPTIVE = "adaptive"
    USER_BEHAVIOR = "user_behavior"
    TIME_SERIES = "time_series"
    COLLABORATIVE = "collaborative"


@dataclass
class CachePattern:
    """Identified cache access pattern"""
    pattern_id: str
    pattern_type: str
    access_frequency: float
    time_distribution: Dict[int, float]  # Hour -> frequency
    user_segments: List[str]
    predictability_score: float
    recommended_ttl: int


@dataclass
class CachePrediction:
    """ML prediction for cache behavior"""
    key_pattern: str
    probability_of_access: float
    predicted_access_time: datetime
    optimal_ttl: int
    confidence_score: float
    preload_recommendation: bool


@dataclass
class UserBehaviorProfile:
    """User behavior profile for caching"""
    user_id: str
    access_patterns: Dict[str, List[datetime]]
    frequently_accessed: List[str]
    access_times: List[int]  # Hours of day
    average_session_duration: float
    predictability_score: float


class IntelligentCacheML:
    """ML-powered intelligent caching system"""
    
    def __init__(
        self,
        base_cache: CacheManager,
        redis_strategy: RedisCachingStrategy,
        redis_url: str = "redis://localhost:6379"
    ):
        self.base_cache = base_cache
        self.redis_strategy = redis_strategy
        self.redis_client = None
        self.redis_url = redis_url
        
        # ML models
        self.access_predictor = RandomForestClassifier(n_estimators=100, random_state=42)
        self.anomaly_detector = IsolationForest(contamination=0.1, random_state=42)
        self.pattern_analyzer = CachePatternAnalyzer()
        self.behavior_analyzer = UserBehaviorAnalyzer()
        
        # Metrics and monitoring
        self.metrics_collector = MetricsCollector()
        self.tracing = TracingManager()
        
        # Cache statistics
        self.access_history: deque = deque(maxlen=10000)
        self.hit_ratio_history: deque = deque(maxlen=1000)
        self.user_profiles: Dict[str, UserBehaviorProfile] = {}
        self.cache_patterns: List[CachePattern] = []
        
        # Dynamic configuration
        self.dynamic_ttls: Dict[str, int] = {}
        self.preload_queue: asyncio.Queue = asyncio.Queue()
        
    async def initialize(self):
        """Initialize Redis connection and start background tasks"""
        self.redis_client = await redis.from_url(self.redis_url)
        
        # Start background tasks
        asyncio.create_task(self._cache_warming_loop())
        asyncio.create_task(self._pattern_analysis_loop())
        asyncio.create_task(self._anomaly_detection_loop())
        
    async def get_with_ml(
        self,
        key: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[Any]:
        """Get value with ML-powered optimization"""
        
        trace_id = self.tracing.start_trace("ml_cache_get")
        
        try:
            # Record access
            access_record = {
                "key": key,
                "user_id": user_id,
                "timestamp": datetime.utcnow(),
                "context": context or {}
            }
            self.access_history.append(access_record)
            
            # Try to get from cache
            value = await self.base_cache.get(key)
            
            if value is not None:
                # Cache hit
                self._record_hit(key, user_id)
                
                # Update user behavior if applicable
                if user_id:
                    await self._update_user_behavior(user_id, key, hit=True)
                    
                return value
            else:
                # Cache miss
                self._record_miss(key, user_id)
                
                # Predict if this key should be preloaded
                if await self._should_preload(key, user_id, context):
                    await self.preload_queue.put({
                        "key": key,
                        "user_id": user_id,
                        "context": context
                    })
                    
                return None
                
        finally:
            self.tracing.end_trace(trace_id)
    
    async def set_with_ml(
        self,
        key: str,
        value: Any,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Set value with ML-optimized TTL"""
        
        # Predict optimal TTL
        optimal_ttl = await self._predict_optimal_ttl(key, user_id, context)
        
        # Store in cache with predicted TTL
        await self.base_cache.set(key, value, ttl_seconds=optimal_ttl)
        
        # Update dynamic TTL mapping
        self.dynamic_ttls[self._get_key_pattern(key)] = optimal_ttl
        
        # Store in Redis if it's a frequently accessed key
        if await self._is_frequently_accessed(key):
            await self.redis_strategy.set_cache(key, value, ttl=optimal_ttl)
    
    async def predict_cache_needs(
        self,
        time_window: timedelta = timedelta(hours=1)
    ) -> List[CachePrediction]:
        """Predict upcoming cache needs"""
        
        predictions = []
        
        # Analyze patterns for each user
        for user_id, profile in self.user_profiles.items():
            user_predictions = await self._predict_user_cache_needs(
                profile, time_window
            )
            predictions.extend(user_predictions)
        
        # Analyze global patterns
        global_predictions = await self._predict_global_cache_needs(time_window)
        predictions.extend(global_predictions)
        
        # Sort by probability and filter
        predictions.sort(key=lambda p: p.probability_of_access, reverse=True)
        
        return predictions[:100]  # Top 100 predictions
    
    async def warm_cache_predictively(self):
        """Warm cache based on ML predictions"""
        
        predictions = await self.predict_cache_needs()
        
        warmed_keys = 0
        for prediction in predictions:
            if prediction.preload_recommendation and prediction.probability_of_access > 0.7:
                # Simulate cache warming (in production, would fetch actual data)
                await self.base_cache.set(
                    prediction.key_pattern,
                    f"preloaded_data_{prediction.key_pattern}",
                    ttl_seconds=prediction.optimal_ttl
                )
                warmed_keys += 1
                
        logger.info(f"Warmed {warmed_keys} cache entries based on predictions")
        
        return warmed_keys
    
    async def analyze_cache_patterns(self) -> List[CachePattern]:
        """Analyze cache access patterns"""
        
        if len(self.access_history) < 100:
            return []
        
        # Convert access history to dataframe for analysis
        df = pd.DataFrame(list(self.access_history))
        
        # Analyze patterns
        patterns = await self.pattern_analyzer.analyze(df)
        
        # Update stored patterns
        self.cache_patterns = patterns
        
        return patterns
    
    async def optimize_cache_size(self) -> Dict[str, Any]:
        """Dynamically adjust cache size based on ML analysis"""
        
        # Analyze current cache performance
        current_hit_ratio = self._calculate_hit_ratio()
        memory_usage = await self._get_memory_usage()
        
        # Predict optimal cache size
        features = [
            current_hit_ratio,
            memory_usage,
            len(self.access_history),
            len(self.user_profiles),
            datetime.utcnow().hour
        ]
        
        # Simple optimization logic (in production would use trained model)
        optimization = {
            "current_size": memory_usage,
            "current_hit_ratio": current_hit_ratio,
            "recommended_action": "maintain"
        }
        
        if current_hit_ratio < 0.7 and memory_usage < 0.8:
            # Increase cache size
            optimization["recommended_action"] = "increase"
            optimization["recommended_size"] = memory_usage * 1.2
        elif current_hit_ratio > 0.9 and memory_usage > 0.5:
            # Decrease cache size to save memory
            optimization["recommended_action"] = "decrease"
            optimization["recommended_size"] = memory_usage * 0.8
            
        return optimization
    
    async def detect_anomalies(self) -> List[Dict[str, Any]]:
        """Detect anomalies in cache access patterns"""
        
        if len(self.access_history) < 100:
            return []
        
        # Prepare features for anomaly detection
        features = []
        for access in list(self.access_history)[-100:]:
            feature = [
                len(access["key"]),
                access["timestamp"].hour,
                access["timestamp"].weekday(),
                1 if access.get("user_id") else 0
            ]
            features.append(feature)
        
        # Detect anomalies
        anomalies = self.anomaly_detector.fit_predict(features)
        
        # Extract anomalous accesses
        anomalous_accesses = []
        for i, is_anomaly in enumerate(anomalies):
            if is_anomaly == -1:
                access = list(self.access_history)[-100 + i]
                anomalous_accesses.append({
                    "access": access,
                    "anomaly_score": self.anomaly_detector.score_samples([features[i]])[0],
                    "detected_at": datetime.utcnow()
                })
                
        return anomalous_accesses
    
    async def get_cache_insights(self) -> Dict[str, Any]:
        """Get comprehensive cache insights and recommendations"""
        
        insights = {
            "timestamp": datetime.utcnow(),
            "performance": {
                "hit_ratio": self._calculate_hit_ratio(),
                "average_ttl": np.mean(list(self.dynamic_ttls.values())) if self.dynamic_ttls else 300,
                "total_accesses": len(self.access_history),
                "unique_keys": len(set(a["key"] for a in self.access_history))
            },
            "patterns": {
                "identified_patterns": len(self.cache_patterns),
                "top_patterns": [
                    {
                        "pattern": p.pattern_type,
                        "frequency": p.access_frequency,
                        "predictability": p.predictability_score
                    }
                    for p in self.cache_patterns[:5]
                ]
            },
            "user_behavior": {
                "total_users": len(self.user_profiles),
                "predictable_users": sum(
                    1 for p in self.user_profiles.values()
                    if p.predictability_score > 0.7
                ),
                "average_session_duration": np.mean([
                    p.average_session_duration for p in self.user_profiles.values()
                ]) if self.user_profiles else 0
            },
            "optimization": await self.optimize_cache_size(),
            "anomalies": len(await self.detect_anomalies()),
            "recommendations": self._generate_recommendations()
        }
        
        return insights
    
    async def _cache_warming_loop(self):
        """Background task for predictive cache warming"""
        while True:
            try:
                await asyncio.sleep(300)  # Every 5 minutes
                await self.warm_cache_predictively()
            except Exception as e:
                logger.error(f"Cache warming error: {e}")
    
    async def _pattern_analysis_loop(self):
        """Background task for pattern analysis"""
        while True:
            try:
                await asyncio.sleep(600)  # Every 10 minutes
                await self.analyze_cache_patterns()
            except Exception as e:
                logger.error(f"Pattern analysis error: {e}")
    
    async def _anomaly_detection_loop(self):
        """Background task for anomaly detection"""
        while True:
            try:
                await asyncio.sleep(60)  # Every minute
                anomalies = await self.detect_anomalies()
                if anomalies:
                    logger.warning(f"Detected {len(anomalies)} cache anomalies")
                    # Could trigger alerts here
            except Exception as e:
                logger.error(f"Anomaly detection error: {e}")
    
    async def _predict_optimal_ttl(
        self,
        key: str,
        user_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> int:
        """Predict optimal TTL for a cache entry"""
        
        # Get key pattern
        pattern = self._get_key_pattern(key)
        
        # Check if we have historical data
        if pattern in self.dynamic_ttls:
            base_ttl = self.dynamic_ttls[pattern]
        else:
            base_ttl = 300  # Default 5 minutes
            
        # Adjust based on user behavior
        if user_id and user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            if key in profile.frequently_accessed:
                # Extend TTL for frequently accessed items
                base_ttl = int(base_ttl * 1.5)
                
        # Adjust based on time of day
        current_hour = datetime.utcnow().hour
        if 9 <= current_hour <= 17:  # Business hours
            base_ttl = int(base_ttl * 1.2)
            
        # Cap TTL
        return min(base_ttl, 3600)  # Max 1 hour
    
    async def _should_preload(
        self,
        key: str,
        user_id: Optional[str],
        context: Optional[Dict[str, Any]]
    ) -> bool:
        """Determine if a key should be preloaded"""
        
        # Check user behavior
        if user_id and user_id in self.user_profiles:
            profile = self.user_profiles[user_id]
            if key in profile.frequently_accessed:
                return True
                
        # Check access frequency
        pattern = self._get_key_pattern(key)
        pattern_accesses = sum(
            1 for a in self.access_history
            if self._get_key_pattern(a["key"]) == pattern
        )
        
        return pattern_accesses > 10
    
    async def _update_user_behavior(
        self,
        user_id: str,
        key: str,
        hit: bool
    ):
        """Update user behavior profile"""
        
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserBehaviorProfile(
                user_id=user_id,
                access_patterns={},
                frequently_accessed=[],
                access_times=[],
                average_session_duration=0.0,
                predictability_score=0.5
            )
            
        profile = self.user_profiles[user_id]
        
        # Update access patterns
        if key not in profile.access_patterns:
            profile.access_patterns[key] = []
        profile.access_patterns[key].append(datetime.utcnow())
        
        # Update frequently accessed
        key_accesses = len(profile.access_patterns[key])
        if key_accesses > 5 and key not in profile.frequently_accessed:
            profile.frequently_accessed.append(key)
            
        # Update access times
        profile.access_times.append(datetime.utcnow().hour)
        
        # Calculate predictability (simplified)
        if len(profile.access_times) > 10:
            hour_counts = pd.Series(profile.access_times).value_counts()
            profile.predictability_score = hour_counts.max() / len(profile.access_times)
    
    def _record_hit(self, key: str, user_id: Optional[str]):
        """Record cache hit"""
        self.hit_ratio_history.append(1)
        self.metrics_collector.record_metric(
            "cache_hit",
            {"key_pattern": self._get_key_pattern(key), "user_id": user_id}
        )
    
    def _record_miss(self, key: str, user_id: Optional[str]):
        """Record cache miss"""
        self.hit_ratio_history.append(0)
        self.metrics_collector.record_metric(
            "cache_miss",
            {"key_pattern": self._get_key_pattern(key), "user_id": user_id}
        )
    
    def _calculate_hit_ratio(self) -> float:
        """Calculate current hit ratio"""
        if not self.hit_ratio_history:
            return 0.0
        return sum(self.hit_ratio_history) / len(self.hit_ratio_history)
    
    async def _get_memory_usage(self) -> float:
        """Get current memory usage (0-1)"""
        # Simplified - in production would check actual memory
        return len(self.access_history) / 10000
    
    def _get_key_pattern(self, key: str) -> str:
        """Extract pattern from key"""
        # Simple pattern extraction - could be more sophisticated
        parts = key.split("_")
        if len(parts) > 2:
            return f"{parts[0]}_{parts[1]}_*"
        return key
    
    async def _is_frequently_accessed(self, key: str) -> bool:
        """Check if key is frequently accessed"""
        pattern = self._get_key_pattern(key)
        pattern_count = sum(
            1 for a in self.access_history
            if self._get_key_pattern(a["key"]) == pattern
        )
        return pattern_count > 5
    
    async def _predict_user_cache_needs(
        self,
        profile: UserBehaviorProfile,
        time_window: timedelta
    ) -> List[CachePrediction]:
        """Predict cache needs for a specific user"""
        
        predictions = []
        
        # Analyze access patterns
        for key, access_times in profile.access_patterns.items():
            if len(access_times) < 3:
                continue
                
            # Calculate access frequency
            recent_accesses = [
                t for t in access_times
                if t > datetime.utcnow() - timedelta(days=7)
            ]
            
            if not recent_accesses:
                continue
                
            # Predict next access time (simplified)
            avg_interval = np.mean([
                (recent_accesses[i+1] - recent_accesses[i]).total_seconds()
                for i in range(len(recent_accesses)-1)
            ])
            
            last_access = max(recent_accesses)
            predicted_next = last_access + timedelta(seconds=avg_interval)
            
            if predicted_next < datetime.utcnow() + time_window:
                predictions.append(CachePrediction(
                    key_pattern=key,
                    probability_of_access=min(0.9, len(recent_accesses) / 10),
                    predicted_access_time=predicted_next,
                    optimal_ttl=int(avg_interval * 1.5),
                    confidence_score=profile.predictability_score,
                    preload_recommendation=True
                ))
                
        return predictions
    
    async def _predict_global_cache_needs(
        self,
        time_window: timedelta
    ) -> List[CachePrediction]:
        """Predict global cache needs"""
        
        predictions = []
        
        # Analyze patterns
        for pattern in self.cache_patterns:
            if pattern.predictability_score > 0.6:
                # Predict based on time distribution
                current_hour = datetime.utcnow().hour
                next_hour = (current_hour + 1) % 24
                
                if pattern.time_distribution.get(next_hour, 0) > 0.1:
                    predictions.append(CachePrediction(
                        key_pattern=pattern.pattern_id,
                        probability_of_access=pattern.time_distribution[next_hour],
                        predicted_access_time=datetime.utcnow() + timedelta(hours=1),
                        optimal_ttl=pattern.recommended_ttl,
                        confidence_score=pattern.predictability_score,
                        preload_recommendation=pattern.access_frequency > 10
                    ))
                    
        return predictions
    
    def _generate_recommendations(self) -> List[str]:
        """Generate cache optimization recommendations"""
        
        recommendations = []
        
        hit_ratio = self._calculate_hit_ratio()
        if hit_ratio < 0.7:
            recommendations.append("Consider increasing cache size or TTL values")
            
        if len(self.cache_patterns) > 10:
            recommendations.append("Implement pattern-based caching strategies")
            
        predictable_users = sum(
            1 for p in self.user_profiles.values()
            if p.predictability_score > 0.7
        )
        if predictable_users > len(self.user_profiles) * 0.5:
            recommendations.append("Enable user-specific cache warming")
            
        if self.dynamic_ttls:
            avg_ttl = np.mean(list(self.dynamic_ttls.values()))
            if avg_ttl < 60:
                recommendations.append("TTLs are very short - consider extending for stable data")
            elif avg_ttl > 1800:
                recommendations.append("TTLs are long - ensure data freshness requirements are met")
                
        return recommendations


class CachePatternAnalyzer:
    """Analyzes cache access patterns"""
    
    def __init__(self):
        self.scaler = StandardScaler()
        
    async def analyze(self, access_df: pd.DataFrame) -> List[CachePattern]:
        """Analyze access patterns from dataframe"""
        
        patterns = []
        
        # Extract key patterns
        access_df['key_pattern'] = access_df['key'].apply(self._extract_pattern)
        
        # Group by pattern
        for pattern, group in access_df.groupby('key_pattern'):
            if len(group) < 10:
                continue
                
            # Calculate time distribution
            group['hour'] = pd.to_datetime(group['timestamp']).dt.hour
            time_dist = group['hour'].value_counts(normalize=True).to_dict()
            
            # Calculate access frequency
            total_duration = (group['timestamp'].max() - group['timestamp'].min()).total_seconds()
            frequency = len(group) / (total_duration / 3600) if total_duration > 0 else 0
            
            # Identify user segments
            user_segments = []
            if 'user_id' in group.columns:
                top_users = group['user_id'].value_counts().head(5)
                user_segments = top_users.index.tolist()
                
            # Calculate predictability
            predictability = self._calculate_predictability(group)
            
            # Recommend TTL based on access pattern
            recommended_ttl = self._recommend_ttl(frequency, predictability)
            
            patterns.append(CachePattern(
                pattern_id=pattern,
                pattern_type=self._classify_pattern_type(frequency, time_dist),
                access_frequency=frequency,
                time_distribution=time_dist,
                user_segments=user_segments,
                predictability_score=predictability,
                recommended_ttl=recommended_ttl
            ))
            
        return patterns
    
    def _extract_pattern(self, key: str) -> str:
        """Extract pattern from cache key"""
        parts = key.split("_")
        if len(parts) > 2:
            return f"{parts[0]}_{parts[1]}_*"
        return key
    
    def _calculate_predictability(self, group: pd.DataFrame) -> float:
        """Calculate how predictable the access pattern is"""
        
        # Check time-based predictability
        if 'hour' not in group.columns:
            group['hour'] = pd.to_datetime(group['timestamp']).dt.hour
            
        hour_std = group['hour'].std()
        time_predictability = 1 / (1 + hour_std / 12)  # Normalize by max std
        
        # Check interval predictability
        timestamps = pd.to_datetime(group['timestamp']).sort_values()
        if len(timestamps) > 1:
            intervals = timestamps.diff().dropna().dt.total_seconds()
            interval_cv = intervals.std() / intervals.mean() if intervals.mean() > 0 else 1
            interval_predictability = 1 / (1 + interval_cv)
        else:
            interval_predictability = 0
            
        return (time_predictability + interval_predictability) / 2
    
    def _recommend_ttl(self, frequency: float, predictability: float) -> int:
        """Recommend TTL based on access pattern"""
        
        # Base TTL on frequency (accesses per hour)
        if frequency > 10:
            base_ttl = 300  # 5 minutes for very frequent
        elif frequency > 1:
            base_ttl = 900  # 15 minutes for frequent
        else:
            base_ttl = 3600  # 1 hour for infrequent
            
        # Adjust based on predictability
        if predictability > 0.8:
            # Highly predictable - can use longer TTL
            return int(base_ttl * 1.5)
        elif predictability < 0.3:
            # Unpredictable - use shorter TTL
            return int(base_ttl * 0.5)
        else:
            return base_ttl
    
    def _classify_pattern_type(
        self,
        frequency: float,
        time_distribution: Dict[int, float]
    ) -> str:
        """Classify the type of access pattern"""
        
        # Check for business hours pattern
        business_hours = range(9, 18)
        business_hour_access = sum(
            time_distribution.get(h, 0) for h in business_hours
        )
        
        if business_hour_access > 0.7:
            return "business_hours"
        elif max(time_distribution.values()) > 0.3:
            return "peak_hour"
        elif frequency > 5:
            return "constant_high"
        elif frequency < 0.5:
            return "sporadic"
        else:
            return "regular"


class UserBehaviorAnalyzer:
    """Analyzes user behavior for cache optimization"""
    
    def __init__(self):
        self.session_threshold = timedelta(minutes=30)
        
    def analyze_user_sessions(
        self,
        user_accesses: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze user session patterns"""
        
        if not user_accesses:
            return {}
            
        # Sort by timestamp
        sorted_accesses = sorted(user_accesses, key=lambda x: x['timestamp'])
        
        # Identify sessions
        sessions = []
        current_session = [sorted_accesses[0]]
        
        for i in range(1, len(sorted_accesses)):
            time_diff = sorted_accesses[i]['timestamp'] - sorted_accesses[i-1]['timestamp']
            
            if time_diff <= self.session_threshold:
                current_session.append(sorted_accesses[i])
            else:
                sessions.append(current_session)
                current_session = [sorted_accesses[i]]
                
        sessions.append(current_session)
        
        # Analyze sessions
        session_durations = [
            (s[-1]['timestamp'] - s[0]['timestamp']).total_seconds()
            for s in sessions if len(s) > 1
        ]
        
        return {
            "total_sessions": len(sessions),
            "average_session_duration": np.mean(session_durations) if session_durations else 0,
            "average_session_size": np.mean([len(s) for s in sessions]),
            "common_session_patterns": self._find_common_patterns(sessions)
        }
    
    def _find_common_patterns(
        self,
        sessions: List[List[Dict[str, Any]]]
    ) -> List[List[str]]:
        """Find common access patterns in sessions"""
        
        # Extract key sequences
        sequences = []
        for session in sessions:
            if len(session) > 2:
                sequence = [access['key'] for access in session]
                sequences.append(sequence)
                
        # Find common subsequences (simplified)
        if not sequences:
            return []
            
        # Count 2-grams
        bigrams = defaultdict(int)
        for sequence in sequences:
            for i in range(len(sequence) - 1):
                bigram = (sequence[i], sequence[i+1])
                bigrams[bigram] += 1
                
        # Return most common patterns
        common_bigrams = sorted(bigrams.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [list(bigram) for bigram, count in common_bigrams if count > 2]