"""
Predictive Maintenance AI
Time series analysis and ML for equipment failure prediction and maintenance optimization
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
from collections import defaultdict
from sklearn.ensemble import RandomForestRegressor, GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.seasonal import seasonal_decompose
import prophet
import joblib

from rentvine_api_client import RentVineAPIClient
from webhook_workflow_engine import WebhookWorkflowEngine
from production_monitoring import MetricsCollector
from distributed_tracing import TracingManager

logger = logging.getLogger(__name__)


class MaintenanceCategory(Enum):
    """Categories of maintenance tasks"""
    HVAC = "hvac"
    PLUMBING = "plumbing"
    ELECTRICAL = "electrical"
    APPLIANCES = "appliances"
    STRUCTURAL = "structural"
    LANDSCAPING = "landscaping"
    SAFETY = "safety"
    GENERAL = "general"


class MaintenanceUrgency(Enum):
    """Urgency levels for maintenance"""
    EMERGENCY = "emergency"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    PREVENTIVE = "preventive"


@dataclass
class EquipmentProfile:
    """Profile for equipment/asset"""
    equipment_id: str
    equipment_type: str
    property_id: str
    install_date: datetime
    manufacturer: str
    model: str
    expected_lifespan_years: float
    maintenance_history: List[Dict[str, Any]] = field(default_factory=list)
    sensor_data: Dict[str, List[float]] = field(default_factory=dict)
    failure_risk_score: float = 0.0
    next_maintenance_date: Optional[datetime] = None


@dataclass
class MaintenancePrediction:
    """Prediction for maintenance needs"""
    equipment_id: str
    prediction_date: datetime
    failure_probability: float
    remaining_useful_life_days: int
    recommended_action: str
    urgency: MaintenanceUrgency
    estimated_cost: float
    confidence_score: float
    risk_factors: List[str]


@dataclass
class MaintenanceRecommendation:
    """AI-generated maintenance recommendation"""
    recommendation_id: str
    equipment_id: str
    property_id: str
    category: MaintenanceCategory
    urgency: MaintenanceUrgency
    description: str
    predicted_failure_date: Optional[datetime]
    estimated_cost: float
    roi_score: float
    work_order_template: Dict[str, Any]


class PredictiveMaintenanceAI:
    """AI system for predictive maintenance"""
    
    def __init__(
        self,
        rentvine_client: RentVineAPIClient,
        webhook_engine: WebhookWorkflowEngine
    ):
        self.rentvine_client = rentvine_client
        self.webhook_engine = webhook_engine
        self.metrics_collector = MetricsCollector()
        self.tracing = TracingManager()
        
        # ML models
        self.failure_predictor = GradientBoostingClassifier(n_estimators=100, random_state=42)
        self.rul_predictor = RandomForestRegressor(n_estimators=100, random_state=42)
        self.cost_estimator = RandomForestRegressor(n_estimators=50, random_state=42)
        self.time_series_analyzer = TimeSeriesAnalyzer()
        self.pattern_recognizer = PatternRecognizer()
        
        # Equipment profiles
        self.equipment_profiles: Dict[str, EquipmentProfile] = {}
        self.maintenance_history: List[Dict[str, Any]] = []
        self.predictions: List[MaintenancePrediction] = []
        
        # Configuration
        self.prediction_horizon_days = 90
        self.emergency_threshold = 0.8
        self.high_urgency_threshold = 0.6
        
    async def analyze_equipment(
        self,
        equipment_id: str,
        include_sensor_data: bool = True
    ) -> MaintenancePrediction:
        """Analyze equipment and predict maintenance needs"""
        
        trace_id = self.tracing.start_trace("equipment_analysis")
        
        try:
            # Get equipment profile
            profile = await self._get_or_create_profile(equipment_id)
            
            # Collect features
            features = await self._extract_equipment_features(profile, include_sensor_data)
            
            # Make predictions
            failure_prob = self._predict_failure_probability(features)
            rul_days = self._predict_remaining_useful_life(features)
            
            # Determine urgency and action
            urgency = self._determine_urgency(failure_prob, rul_days)
            action = self._recommend_action(failure_prob, rul_days, urgency)
            
            # Estimate cost
            estimated_cost = await self._estimate_maintenance_cost(
                profile, urgency, action
            )
            
            # Identify risk factors
            risk_factors = self._identify_risk_factors(profile, features)
            
            prediction = MaintenancePrediction(
                equipment_id=equipment_id,
                prediction_date=datetime.utcnow(),
                failure_probability=failure_prob,
                remaining_useful_life_days=rul_days,
                recommended_action=action,
                urgency=urgency,
                estimated_cost=estimated_cost,
                confidence_score=self._calculate_confidence(features),
                risk_factors=risk_factors
            )
            
            # Store prediction
            self.predictions.append(prediction)
            
            # Update profile
            profile.failure_risk_score = failure_prob
            if urgency in [MaintenanceUrgency.HIGH, MaintenanceUrgency.EMERGENCY]:
                profile.next_maintenance_date = datetime.utcnow() + timedelta(days=7)
            
            return prediction
            
        finally:
            self.tracing.end_trace(trace_id)
    
    async def analyze_property_portfolio(
        self,
        property_ids: List[str]
    ) -> Dict[str, Any]:
        """Analyze maintenance needs across property portfolio"""
        
        portfolio_analysis = {
            "timestamp": datetime.utcnow(),
            "properties_analyzed": len(property_ids),
            "total_equipment": 0,
            "high_risk_equipment": [],
            "maintenance_schedule": [],
            "budget_forecast": {},
            "recommendations": []
        }
        
        # Analyze each property
        for property_id in property_ids:
            property_equipment = await self._get_property_equipment(property_id)
            portfolio_analysis["total_equipment"] += len(property_equipment)
            
            # Analyze each equipment
            for equipment in property_equipment:
                prediction = await self.analyze_equipment(equipment["id"])
                
                if prediction.failure_probability > self.high_urgency_threshold:
                    portfolio_analysis["high_risk_equipment"].append({
                        "equipment_id": equipment["id"],
                        "property_id": property_id,
                        "risk_score": prediction.failure_probability,
                        "urgency": prediction.urgency.value
                    })
                
                # Add to maintenance schedule
                if prediction.urgency != MaintenanceUrgency.LOW:
                    portfolio_analysis["maintenance_schedule"].append({
                        "equipment_id": equipment["id"],
                        "property_id": property_id,
                        "scheduled_date": self._calculate_maintenance_date(prediction),
                        "estimated_cost": prediction.estimated_cost,
                        "urgency": prediction.urgency.value
                    })
        
        # Calculate budget forecast
        portfolio_analysis["budget_forecast"] = self._calculate_budget_forecast(
            portfolio_analysis["maintenance_schedule"]
        )
        
        # Generate recommendations
        portfolio_analysis["recommendations"] = await self._generate_portfolio_recommendations(
            portfolio_analysis
        )
        
        return portfolio_analysis
    
    async def predict_seasonal_maintenance(
        self,
        property_id: str,
        season: str
    ) -> List[MaintenanceRecommendation]:
        """Predict seasonal maintenance needs"""
        
        recommendations = []
        
        # Get property equipment
        equipment_list = await self._get_property_equipment(property_id)
        
        # Seasonal patterns
        seasonal_maintenance = {
            "spring": {
                MaintenanceCategory.HVAC: ["AC preparation", "filter replacement"],
                MaintenanceCategory.LANDSCAPING: ["lawn care", "irrigation check"],
                MaintenanceCategory.STRUCTURAL: ["roof inspection", "gutter cleaning"]
            },
            "summer": {
                MaintenanceCategory.HVAC: ["AC maintenance", "efficiency check"],
                MaintenanceCategory.PLUMBING: ["outdoor faucet check"],
                MaintenanceCategory.SAFETY: ["pool maintenance", "pest control"]
            },
            "fall": {
                MaintenanceCategory.HVAC: ["heating preparation", "furnace check"],
                MaintenanceCategory.LANDSCAPING: ["leaf removal", "winterization"],
                MaintenanceCategory.STRUCTURAL: ["weather sealing", "insulation check"]
            },
            "winter": {
                MaintenanceCategory.PLUMBING: ["pipe insulation", "freeze prevention"],
                MaintenanceCategory.HVAC: ["heating maintenance"],
                MaintenanceCategory.SAFETY: ["snow removal prep", "emergency supplies"]
            }
        }
        
        season_tasks = seasonal_maintenance.get(season.lower(), {})
        
        for category, tasks in season_tasks.items():
            # Find relevant equipment
            relevant_equipment = [
                e for e in equipment_list
                if self._get_equipment_category(e["type"]) == category
            ]
            
            for equipment in relevant_equipment:
                for task in tasks:
                    # Analyze need for this task
                    profile = await self._get_or_create_profile(equipment["id"])
                    need_score = await self._assess_seasonal_need(profile, task, season)
                    
                    if need_score > 0.5:
                        recommendation = MaintenanceRecommendation(
                            recommendation_id=f"seasonal_{equipment['id']}_{task}_{datetime.utcnow().timestamp()}",
                            equipment_id=equipment["id"],
                            property_id=property_id,
                            category=category,
                            urgency=MaintenanceUrgency.PREVENTIVE,
                            description=f"Seasonal {season} maintenance: {task}",
                            predicted_failure_date=None,
                            estimated_cost=await self._estimate_task_cost(task),
                            roi_score=need_score,
                            work_order_template=self._create_work_order_template(
                                equipment, task, category
                            )
                        )
                        recommendations.append(recommendation)
        
        return recommendations
    
    async def analyze_maintenance_patterns(
        self,
        time_window: timedelta = timedelta(days=365)
    ) -> Dict[str, Any]:
        """Analyze historical maintenance patterns"""
        
        # Filter recent maintenance history
        cutoff_date = datetime.utcnow() - time_window
        recent_maintenance = [
            m for m in self.maintenance_history
            if m.get("date", datetime.utcnow()) > cutoff_date
        ]
        
        if not recent_maintenance:
            return {"error": "Insufficient maintenance history"}
        
        # Convert to DataFrame for analysis
        df = pd.DataFrame(recent_maintenance)
        
        patterns = {
            "timestamp": datetime.utcnow(),
            "analysis_period": time_window.days,
            "total_maintenance_events": len(recent_maintenance),
            "patterns": {}
        }
        
        # Analyze by category
        if "category" in df.columns:
            category_analysis = df.groupby("category").agg({
                "cost": ["mean", "sum", "count"],
                "duration": "mean"
            })
            patterns["patterns"]["by_category"] = category_analysis.to_dict()
        
        # Time series analysis
        df["date"] = pd.to_datetime(df["date"])
        df.set_index("date", inplace=True)
        
        # Monthly frequency analysis
        monthly_counts = df.resample("M").size()
        patterns["patterns"]["monthly_frequency"] = {
            "mean": monthly_counts.mean(),
            "std": monthly_counts.std(),
            "trend": self._detect_trend(monthly_counts)
        }
        
        # Failure pattern recognition
        failure_patterns = await self.pattern_recognizer.analyze_failures(df)
        patterns["patterns"]["failure_patterns"] = failure_patterns
        
        # Cost trends
        if "cost" in df.columns:
            monthly_costs = df.resample("M")["cost"].sum()
            patterns["patterns"]["cost_trends"] = {
                "monthly_average": monthly_costs.mean(),
                "trend": self._detect_trend(monthly_costs),
                "forecast_next_month": self._forecast_next_value(monthly_costs)
            }
        
        return patterns
    
    async def create_smart_work_order(
        self,
        prediction: MaintenancePrediction
    ) -> Dict[str, Any]:
        """Create intelligent work order based on prediction"""
        
        # Get equipment profile
        profile = self.equipment_profiles.get(prediction.equipment_id)
        if not profile:
            raise ValueError(f"Equipment {prediction.equipment_id} not found")
        
        # Create work order
        work_order = {
            "property_id": profile.property_id,
            "equipment_id": prediction.equipment_id,
            "title": f"{prediction.urgency.value.title()} Maintenance: {profile.equipment_type}",
            "description": self._generate_work_order_description(prediction, profile),
            "priority": self._map_urgency_to_priority(prediction.urgency),
            "category": self._get_equipment_category(profile.equipment_type).value,
            "estimated_cost": prediction.estimated_cost,
            "ai_metadata": {
                "prediction_id": f"pred_{datetime.utcnow().timestamp()}",
                "failure_probability": prediction.failure_probability,
                "confidence_score": prediction.confidence_score,
                "risk_factors": prediction.risk_factors,
                "recommended_action": prediction.recommended_action
            },
            "scheduled_date": self._calculate_maintenance_date(prediction),
            "instructions": self._generate_maintenance_instructions(prediction, profile)
        }
        
        # Add parts and materials estimate
        parts_estimate = await self._estimate_parts_needed(profile, prediction)
        if parts_estimate:
            work_order["parts_needed"] = parts_estimate
        
        # Create via RentVine API
        created_order = await self.rentvine_client.create_work_order(work_order)
        
        # Track in system
        self.maintenance_history.append({
            "work_order_id": created_order["id"],
            "equipment_id": prediction.equipment_id,
            "prediction": prediction,
            "created_at": datetime.utcnow()
        })
        
        return created_order
    
    async def calculate_roi_analysis(
        self,
        property_id: str,
        analysis_period_years: int = 5
    ) -> Dict[str, Any]:
        """Calculate ROI for predictive vs reactive maintenance"""
        
        # Get property equipment
        equipment_list = await self._get_property_equipment(property_id)
        
        roi_analysis = {
            "property_id": property_id,
            "analysis_period_years": analysis_period_years,
            "timestamp": datetime.utcnow(),
            "predictive_maintenance": {
                "total_cost": 0,
                "prevented_failures": 0,
                "downtime_hours_saved": 0
            },
            "reactive_maintenance": {
                "total_cost": 0,
                "failure_count": 0,
                "downtime_hours": 0
            },
            "roi_metrics": {}
        }
        
        # Analyze each equipment
        for equipment in equipment_list:
            equipment_roi = await self._calculate_equipment_roi(
                equipment, analysis_period_years
            )
            
            # Aggregate costs
            roi_analysis["predictive_maintenance"]["total_cost"] += equipment_roi["predictive_cost"]
            roi_analysis["reactive_maintenance"]["total_cost"] += equipment_roi["reactive_cost"]
            
            # Count prevented failures
            roi_analysis["predictive_maintenance"]["prevented_failures"] += equipment_roi["prevented_failures"]
            roi_analysis["reactive_maintenance"]["failure_count"] += equipment_roi["expected_failures"]
            
            # Calculate downtime
            roi_analysis["predictive_maintenance"]["downtime_hours_saved"] += equipment_roi["downtime_saved"]
            roi_analysis["reactive_maintenance"]["downtime_hours"] += equipment_roi["reactive_downtime"]
        
        # Calculate ROI metrics
        total_savings = (
            roi_analysis["reactive_maintenance"]["total_cost"] -
            roi_analysis["predictive_maintenance"]["total_cost"]
        )
        
        roi_percentage = (
            (total_savings / roi_analysis["predictive_maintenance"]["total_cost"] * 100)
            if roi_analysis["predictive_maintenance"]["total_cost"] > 0 else 0
        )
        
        roi_analysis["roi_metrics"] = {
            "total_savings": total_savings,
            "roi_percentage": roi_percentage,
            "cost_reduction_percentage": (
                (total_savings / roi_analysis["reactive_maintenance"]["total_cost"] * 100)
                if roi_analysis["reactive_maintenance"]["total_cost"] > 0 else 0
            ),
            "downtime_reduction_hours": (
                roi_analysis["reactive_maintenance"]["downtime_hours"] -
                roi_analysis["predictive_maintenance"]["downtime_hours_saved"]
            ),
            "failure_prevention_rate": (
                roi_analysis["predictive_maintenance"]["prevented_failures"] /
                roi_analysis["reactive_maintenance"]["failure_count"]
                if roi_analysis["reactive_maintenance"]["failure_count"] > 0 else 0
            )
        }
        
        return roi_analysis
    
    async def generate_maintenance_dashboard(self) -> Dict[str, Any]:
        """Generate comprehensive maintenance dashboard data"""
        
        dashboard = {
            "timestamp": datetime.utcnow(),
            "overview": {
                "total_equipment": len(self.equipment_profiles),
                "high_risk_count": 0,
                "upcoming_maintenance": [],
                "recent_predictions": []
            },
            "metrics": {
                "average_failure_probability": 0,
                "prediction_accuracy": 0,
                "cost_savings_ytd": 0
            },
            "trends": {},
            "alerts": []
        }
        
        # Calculate high risk equipment
        for profile in self.equipment_profiles.values():
            if profile.failure_risk_score > self.high_urgency_threshold:
                dashboard["overview"]["high_risk_count"] += 1
        
        # Get recent predictions
        recent_predictions = sorted(
            self.predictions,
            key=lambda p: p.prediction_date,
            reverse=True
        )[:10]
        
        dashboard["overview"]["recent_predictions"] = [
            {
                "equipment_id": p.equipment_id,
                "failure_probability": p.failure_probability,
                "urgency": p.urgency.value,
                "estimated_cost": p.estimated_cost
            }
            for p in recent_predictions
        ]
        
        # Calculate metrics
        if self.predictions:
            dashboard["metrics"]["average_failure_probability"] = np.mean([
                p.failure_probability for p in self.predictions
            ])
        
        # Calculate prediction accuracy (if we have outcomes)
        accuracy = await self._calculate_prediction_accuracy()
        dashboard["metrics"]["prediction_accuracy"] = accuracy
        
        # Cost savings
        dashboard["metrics"]["cost_savings_ytd"] = await self._calculate_cost_savings_ytd()
        
        # Trends
        dashboard["trends"] = await self._generate_trend_analysis()
        
        # Generate alerts
        for profile in self.equipment_profiles.values():
            if profile.failure_risk_score > self.emergency_threshold:
                dashboard["alerts"].append({
                    "type": "emergency",
                    "equipment_id": profile.equipment_id,
                    "message": f"Emergency maintenance needed for {profile.equipment_type}",
                    "risk_score": profile.failure_risk_score
                })
        
        return dashboard
    
    async def _get_or_create_profile(self, equipment_id: str) -> EquipmentProfile:
        """Get or create equipment profile"""
        
        if equipment_id in self.equipment_profiles:
            return self.equipment_profiles[equipment_id]
        
        # Fetch from RentVine
        equipment_data = await self.rentvine_client.get_equipment(equipment_id)
        
        profile = EquipmentProfile(
            equipment_id=equipment_id,
            equipment_type=equipment_data.get("type", "unknown"),
            property_id=equipment_data.get("property_id"),
            install_date=datetime.fromisoformat(equipment_data.get("install_date", datetime.utcnow().isoformat())),
            manufacturer=equipment_data.get("manufacturer", "unknown"),
            model=equipment_data.get("model", "unknown"),
            expected_lifespan_years=self._get_expected_lifespan(equipment_data.get("type"))
        )
        
        # Load maintenance history
        history = await self.rentvine_client.get_maintenance_history(equipment_id)
        profile.maintenance_history = history
        
        self.equipment_profiles[equipment_id] = profile
        return profile
    
    async def _extract_equipment_features(
        self,
        profile: EquipmentProfile,
        include_sensor_data: bool
    ) -> np.ndarray:
        """Extract features for ML models"""
        
        features = []
        
        # Age features
        age_days = (datetime.utcnow() - profile.install_date).days
        age_years = age_days / 365
        features.extend([age_days, age_years])
        
        # Usage percentage of expected lifespan
        lifespan_usage = age_years / profile.expected_lifespan_years
        features.append(lifespan_usage)
        
        # Maintenance history features
        maintenance_count = len(profile.maintenance_history)
        days_since_last_maintenance = 365  # Default
        
        if profile.maintenance_history:
            last_maintenance = max(
                profile.maintenance_history,
                key=lambda m: m.get("date", datetime.min)
            )
            days_since_last_maintenance = (
                datetime.utcnow() - datetime.fromisoformat(last_maintenance["date"])
            ).days
        
        features.extend([maintenance_count, days_since_last_maintenance])
        
        # Failure history
        failure_count = sum(
            1 for m in profile.maintenance_history
            if m.get("type") == "failure"
        )
        features.append(failure_count)
        
        # Sensor data features (if available)
        if include_sensor_data and profile.sensor_data:
            for sensor_type, readings in profile.sensor_data.items():
                if readings:
                    features.extend([
                        np.mean(readings),
                        np.std(readings),
                        np.max(readings),
                        np.min(readings)
                    ])
        
        # Equipment type encoding (simplified)
        equipment_type_code = hash(profile.equipment_type) % 100
        features.append(equipment_type_code)
        
        return np.array(features)
    
    def _predict_failure_probability(self, features: np.ndarray) -> float:
        """Predict probability of failure"""
        
        try:
            # Reshape for single prediction
            features_2d = features.reshape(1, -1)
            
            # Get probability
            prob = self.failure_predictor.predict_proba(features_2d)[0][1]
            return float(prob)
        except:
            # Return default if model not trained
            return 0.5
    
    def _predict_remaining_useful_life(self, features: np.ndarray) -> int:
        """Predict remaining useful life in days"""
        
        try:
            # Reshape for single prediction
            features_2d = features.reshape(1, -1)
            
            # Get prediction
            rul_days = self.rul_predictor.predict(features_2d)[0]
            return max(0, int(rul_days))
        except:
            # Return default if model not trained
            return 180  # 6 months default
    
    def _determine_urgency(self, failure_prob: float, rul_days: int) -> MaintenanceUrgency:
        """Determine maintenance urgency"""
        
        if failure_prob > self.emergency_threshold or rul_days < 7:
            return MaintenanceUrgency.EMERGENCY
        elif failure_prob > self.high_urgency_threshold or rul_days < 30:
            return MaintenanceUrgency.HIGH
        elif failure_prob > 0.4 or rul_days < 90:
            return MaintenanceUrgency.MEDIUM
        elif failure_prob > 0.2:
            return MaintenanceUrgency.LOW
        else:
            return MaintenanceUrgency.PREVENTIVE
    
    def _recommend_action(
        self,
        failure_prob: float,
        rul_days: int,
        urgency: MaintenanceUrgency
    ) -> str:
        """Recommend maintenance action"""
        
        if urgency == MaintenanceUrgency.EMERGENCY:
            return "Immediate inspection and repair required"
        elif urgency == MaintenanceUrgency.HIGH:
            return "Schedule maintenance within 1 week"
        elif urgency == MaintenanceUrgency.MEDIUM:
            return "Schedule maintenance within 1 month"
        elif urgency == MaintenanceUrgency.LOW:
            return "Monitor and schedule routine maintenance"
        else:
            return "Continue preventive maintenance schedule"
    
    async def _estimate_maintenance_cost(
        self,
        profile: EquipmentProfile,
        urgency: MaintenanceUrgency,
        action: str
    ) -> float:
        """Estimate maintenance cost"""
        
        # Base cost by equipment type
        base_costs = {
            "hvac": 500,
            "plumbing": 300,
            "electrical": 400,
            "appliances": 250,
            "structural": 1000,
            "landscaping": 150,
            "general": 200
        }
        
        equipment_category = self._get_equipment_category(profile.equipment_type).value
        base_cost = base_costs.get(equipment_category, 300)
        
        # Urgency multiplier
        urgency_multipliers = {
            MaintenanceUrgency.EMERGENCY: 2.0,
            MaintenanceUrgency.HIGH: 1.5,
            MaintenanceUrgency.MEDIUM: 1.2,
            MaintenanceUrgency.LOW: 1.0,
            MaintenanceUrgency.PREVENTIVE: 0.8
        }
        
        cost = base_cost * urgency_multipliers.get(urgency, 1.0)
        
        # Age factor
        age_years = (datetime.utcnow() - profile.install_date).days / 365
        if age_years > profile.expected_lifespan_years * 0.8:
            cost *= 1.3  # Older equipment costs more
        
        return round(cost, 2)
    
    def _get_equipment_category(self, equipment_type: str) -> MaintenanceCategory:
        """Map equipment type to maintenance category"""
        
        type_lower = equipment_type.lower()
        
        if any(term in type_lower for term in ["hvac", "ac", "heating", "cooling", "furnace"]):
            return MaintenanceCategory.HVAC
        elif any(term in type_lower for term in ["plumb", "pipe", "water", "drain"]):
            return MaintenanceCategory.PLUMBING
        elif any(term in type_lower for term in ["electric", "wire", "circuit", "outlet"]):
            return MaintenanceCategory.ELECTRICAL
        elif any(term in type_lower for term in ["appliance", "refrigerator", "washer", "dryer", "dishwasher"]):
            return MaintenanceCategory.APPLIANCES
        elif any(term in type_lower for term in ["struct", "roof", "foundation", "wall"]):
            return MaintenanceCategory.STRUCTURAL
        elif any(term in type_lower for term in ["landscape", "lawn", "garden", "irrigation"]):
            return MaintenanceCategory.LANDSCAPING
        elif any(term in type_lower for term in ["safety", "security", "fire", "alarm"]):
            return MaintenanceCategory.SAFETY
        else:
            return MaintenanceCategory.GENERAL
    
    def _get_expected_lifespan(self, equipment_type: str) -> float:
        """Get expected lifespan in years for equipment type"""
        
        lifespans = {
            "hvac": 15,
            "water_heater": 10,
            "refrigerator": 13,
            "washer": 10,
            "dryer": 13,
            "dishwasher": 9,
            "roof": 20,
            "plumbing": 50,
            "electrical": 30
        }
        
        type_lower = equipment_type.lower()
        for key, years in lifespans.items():
            if key in type_lower:
                return years
                
        return 15  # Default 15 years


class TimeSeriesAnalyzer:
    """Analyzes time series data for maintenance prediction"""
    
    def __init__(self):
        self.models = {}
        
    def analyze_sensor_data(
        self,
        sensor_data: Dict[str, List[Tuple[datetime, float]]]
    ) -> Dict[str, Any]:
        """Analyze sensor time series data"""
        
        analysis = {}
        
        for sensor_type, readings in sensor_data.items():
            if len(readings) < 10:
                continue
                
            # Convert to pandas series
            dates, values = zip(*readings)
            ts = pd.Series(values, index=pd.DatetimeIndex(dates))
            
            # Basic statistics
            analysis[sensor_type] = {
                "mean": ts.mean(),
                "std": ts.std(),
                "trend": self._detect_trend(ts),
                "anomalies": self._detect_anomalies(ts),
                "forecast": self._forecast_series(ts, periods=7)
            }
            
        return analysis
    
    def _detect_trend(self, series: pd.Series) -> str:
        """Detect trend in time series"""
        
        if len(series) < 10:
            return "insufficient_data"
            
        # Simple linear regression trend
        x = np.arange(len(series))
        y = series.values
        
        slope = np.polyfit(x, y, 1)[0]
        
        if abs(slope) < 0.01:
            return "stable"
        elif slope > 0:
            return "increasing"
        else:
            return "decreasing"
    
    def _detect_anomalies(self, series: pd.Series) -> List[datetime]:
        """Detect anomalies in time series"""
        
        # Simple z-score method
        z_scores = np.abs((series - series.mean()) / series.std())
        anomaly_indices = series.index[z_scores > 3].tolist()
        
        return anomaly_indices
    
    def _forecast_series(self, series: pd.Series, periods: int) -> List[float]:
        """Forecast future values"""
        
        if len(series) < 20:
            # Too short for complex models, use simple average
            return [series.mean()] * periods
            
        try:
            # Use ARIMA for forecasting
            model = ARIMA(series, order=(1, 1, 1))
            model_fit = model.fit()
            forecast = model_fit.forecast(steps=periods)
            return forecast.tolist()
        except:
            # Fallback to simple method
            return [series.mean()] * periods


class PatternRecognizer:
    """Recognizes patterns in maintenance data"""
    
    def __init__(self):
        self.patterns = []
        
    async def analyze_failures(self, maintenance_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze failure patterns"""
        
        patterns = {
            "recurring_failures": [],
            "seasonal_patterns": {},
            "correlated_failures": []
        }
        
        # Find recurring failures
        if "equipment_id" in maintenance_df.columns and "type" in maintenance_df.columns:
            failure_df = maintenance_df[maintenance_df["type"] == "failure"]
            
            equipment_failures = failure_df.groupby("equipment_id").size()
            recurring = equipment_failures[equipment_failures > 2]
            
            patterns["recurring_failures"] = [
                {
                    "equipment_id": eq_id,
                    "failure_count": count,
                    "pattern": "frequent_failures"
                }
                for eq_id, count in recurring.items()
            ]
        
        # Detect seasonal patterns
        if not maintenance_df.empty:
            maintenance_df["month"] = maintenance_df.index.month
            monthly_counts = maintenance_df.groupby("month").size()
            
            # Identify peak months
            mean_count = monthly_counts.mean()
            peak_months = monthly_counts[monthly_counts > mean_count * 1.5]
            
            patterns["seasonal_patterns"] = {
                "peak_months": peak_months.index.tolist(),
                "pattern": "seasonal_increase"
            }
        
        return patterns