"""
Hybrid AI Services for Aictive Platform v2
Implements multimodal AI processing for property management
"""

import os
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime
import base64
from PIL import Image
import io

# Core AI service imports
from openai import AsyncOpenAI
from claude_service import ClaudeService  # Your existing Claude service
import aiohttp


class MultimodalAIService:
    """Hybrid AI service combining local and cloud processing"""
    
    def __init__(self):
        self.openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.claude_service = ClaudeService()
        self.config = self._load_config()
        
    def _load_config(self) -> Dict:
        """Load AI service configuration"""
        return {
            "vision": {
                "damage_threshold": 0.7,
                "quality_min_score": 0.8,
                "max_image_size": 4096
            },
            "text": {
                "response_temperature": 0.7,
                "max_tokens": 1000,
                "confidence_threshold": 0.85
            },
            "costs": {
                "vision_per_image": 0.15,
                "text_per_1k_tokens": 0.03
            }
        }
    
    async def process_maintenance_request(self, request_data: Dict) -> Dict:
        """
        Process multimodal maintenance request
        Combines text, images, and potentially audio
        """
        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "request_id": request_data.get("id"),
            "analysis": {}
        }
        
        # Process text description
        if "description" in request_data:
            text_analysis = await self._analyze_maintenance_text(
                request_data["description"]
            )
            results["analysis"]["text"] = text_analysis
            
        # Process images if provided
        if "images" in request_data:
            image_analysis = await self._analyze_property_images(
                request_data["images"]
            )
            results["analysis"]["images"] = image_analysis
            
        # Calculate urgency score
        results["urgency_score"] = self._calculate_urgency(results["analysis"])
        
        # Generate recommended actions
        results["recommended_actions"] = await self._generate_recommendations(
            results["analysis"]
        )
        
        return results
    
    async def _analyze_maintenance_text(self, description: str) -> Dict:
        """Analyze maintenance request text for urgency and category"""
        prompt = f"""
        Analyze this maintenance request and provide:
        1. Category (plumbing, electrical, HVAC, structural, other)
        2. Urgency (emergency, high, medium, low)
        3. Key issues identified
        4. Estimated time to repair
        
        Request: {description}
        
        Return as JSON.
        """
        
        response = await self.claude_service.generate(prompt)
        return json.loads(response)
    
    async def _analyze_property_images(self, images: List[str]) -> List[Dict]:
        """Analyze property images for damage assessment"""
        analyses = []
        
        for image_path in images:
            # Prepare image for API
            base64_image = self._encode_image(image_path)
            
            response = await self.openai_client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": """Analyze this property image and identify:
                            1. Any visible damage or maintenance issues
                            2. Severity of each issue (1-10 scale)
                            3. Affected area/component
                            4. Recommended repair type
                            Return as structured JSON."""
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}"
                            }
                        }
                    ]
                }],
                max_tokens=500
            )
            
            analysis = json.loads(response.choices[0].message.content)
            analysis["image_path"] = image_path
            analyses.append(analysis)
            
        return analyses
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image to base64 for API transmission"""
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    
    def _calculate_urgency(self, analysis: Dict) -> float:
        """Calculate overall urgency score from multimodal analysis"""
        urgency_score = 0.0
        weights = {"text": 0.4, "images": 0.6}
        
        # Text-based urgency
        if "text" in analysis:
            text_urgency_map = {
                "emergency": 1.0,
                "high": 0.75,
                "medium": 0.5,
                "low": 0.25
            }
            text_urgency = analysis["text"].get("urgency", "medium")
            urgency_score += weights["text"] * text_urgency_map.get(text_urgency, 0.5)
        
        # Image-based urgency
        if "images" in analysis:
            max_severity = max(
                issue.get("severity", 0) / 10.0
                for img in analysis["images"]
                for issue in img.get("issues", [])
            ) if analysis["images"] else 0
            urgency_score += weights["images"] * max_severity
            
        return min(urgency_score, 1.0)
    
    async def _generate_recommendations(self, analysis: Dict) -> Dict:
        """Generate actionable recommendations based on analysis"""
        prompt = f"""
        Based on this maintenance analysis, provide recommendations:
        
        Analysis: {json.dumps(analysis, indent=2)}
        
        Include:
        1. Immediate actions required
        2. Vendor type needed
        3. Estimated cost range
        4. Parts/materials likely needed
        5. Tenant communication template
        
        Format as actionable JSON.
        """
        
        response = await self.claude_service.generate(prompt)
        return json.loads(response)


class PropertyDamageAI:
    """Specialized AI for property damage assessment"""
    
    def __init__(self, ai_service: MultimodalAIService):
        self.ai_service = ai_service
        
    async def compare_move_conditions(
        self,
        move_in_photos: List[str],
        move_out_photos: List[str]
    ) -> Dict:
        """
        Compare move-in and move-out photos for damage assessment
        Used for security deposit decisions
        """
        comparison_results = {
            "comparison_date": datetime.utcnow().isoformat(),
            "damages_found": [],
            "normal_wear_tear": [],
            "improvements": [],
            "deposit_recommendations": {}
        }
        
        # Analyze each set of photos
        move_in_analysis = await self.ai_service._analyze_property_images(move_in_photos)
        move_out_analysis = await self.ai_service._analyze_property_images(move_out_photos)
        
        # Compare conditions
        for room in self._match_rooms(move_in_analysis, move_out_analysis):
            room_comparison = self._compare_room_condition(
                room["move_in"],
                room["move_out"]
            )
            
            if room_comparison["has_damage"]:
                comparison_results["damages_found"].extend(room_comparison["damages"])
            if room_comparison["has_wear"]:
                comparison_results["normal_wear_tear"].extend(room_comparison["wear"])
                
        # Calculate deposit recommendations
        comparison_results["deposit_recommendations"] = self._calculate_deposit_deductions(
            comparison_results["damages_found"]
        )
        
        return comparison_results
    
    def _match_rooms(self, move_in: List[Dict], move_out: List[Dict]) -> List[Dict]:
        """Match rooms between move-in and move-out photos"""
        # Implementation to match corresponding rooms
        # This would use image similarity or metadata
        matched_rooms = []
        # ... matching logic ...
        return matched_rooms
    
    def _compare_room_condition(self, move_in: Dict, move_out: Dict) -> Dict:
        """Compare specific room conditions"""
        comparison = {
            "has_damage": False,
            "has_wear": False,
            "damages": [],
            "wear": []
        }
        
        # Compare identified issues
        # ... comparison logic ...
        
        return comparison
    
    def _calculate_deposit_deductions(self, damages: List[Dict]) -> Dict:
        """Calculate security deposit deductions based on damages"""
        deductions = {
            "total": 0,
            "items": [],
            "justification": []
        }
        
        for damage in damages:
            # Use historical data and cost estimates
            cost_estimate = self._estimate_repair_cost(damage)
            deductions["items"].append({
                "damage": damage["description"],
                "cost": cost_estimate,
                "category": damage["category"]
            })
            deductions["total"] += cost_estimate
            
        return deductions
    
    def _estimate_repair_cost(self, damage: Dict) -> float:
        """Estimate repair cost based on damage type and severity"""
        # This would use historical data from your system
        base_costs = {
            "paint": 150,
            "carpet": 300,
            "drywall": 200,
            "appliance": 250,
            "plumbing": 175,
            "electrical": 225
        }
        
        category = damage.get("category", "other")
        severity = damage.get("severity", 5) / 10.0
        
        base_cost = base_costs.get(category, 100)
        return base_cost * severity


class LeadScoringAI:
    """AI for scoring and prioritizing rental inquiries"""
    
    def __init__(self, ai_service: MultimodalAIService):
        self.ai_service = ai_service
        
    async def score_lead(self, inquiry_data: Dict) -> Dict:
        """
        Score rental inquiry based on multiple factors
        Uses your Resident Scoring Matrix
        """
        scoring_result = {
            "lead_id": inquiry_data.get("id"),
            "score": 0,
            "factors": {},
            "recommendation": "",
            "priority": "medium"
        }
        
        # Analyze inquiry text for indicators
        if "message" in inquiry_data:
            text_indicators = await self._analyze_inquiry_text(inquiry_data["message"])
            scoring_result["factors"]["text_analysis"] = text_indicators
            
        # Score based on provided information completeness
        info_score = self._score_information_completeness(inquiry_data)
        scoring_result["factors"]["completeness"] = info_score
        
        # Calculate timing score
        timing_score = self._score_timing(inquiry_data)
        scoring_result["factors"]["timing"] = timing_score
        
        # Calculate overall score
        scoring_result["score"] = self._calculate_overall_score(scoring_result["factors"])
        
        # Set priority and recommendation
        if scoring_result["score"] > 0.8:
            scoring_result["priority"] = "high"
            scoring_result["recommendation"] = "Contact immediately - high conversion probability"
        elif scoring_result["score"] > 0.6:
            scoring_result["priority"] = "medium"
            scoring_result["recommendation"] = "Follow up within 2 hours"
        else:
            scoring_result["priority"] = "low"
            scoring_result["recommendation"] = "Standard response timeline"
            
        return scoring_result
    
    async def _analyze_inquiry_text(self, message: str) -> Dict:
        """Analyze inquiry text for quality indicators"""
        prompt = f"""
        Analyze this rental inquiry for quality indicators:
        
        Message: {message}
        
        Score (0-1) for:
        1. Seriousness/intent
        2. Financial stability indicators
        3. Urgency
        4. Clarity of needs
        5. Red flags or concerns
        
        Return as JSON with scores and reasoning.
        """
        
        response = await self.ai_service.claude_service.generate(prompt)
        return json.loads(response)
    
    def _score_information_completeness(self, inquiry_data: Dict) -> float:
        """Score based on how complete the provided information is"""
        required_fields = [
            "name", "email", "phone", "move_date",
            "desired_bedrooms", "budget", "occupants"
        ]
        
        provided_fields = sum(1 for field in required_fields if field in inquiry_data)
        return provided_fields / len(required_fields)
    
    def _score_timing(self, inquiry_data: Dict) -> float:
        """Score based on move-in timing"""
        if "move_date" not in inquiry_data:
            return 0.5
            
        move_date = datetime.fromisoformat(inquiry_data["move_date"])
        days_until_move = (move_date - datetime.utcnow()).days
        
        if 14 <= days_until_move <= 45:
            return 1.0  # Ideal timing
        elif 7 <= days_until_move < 14:
            return 0.8  # Urgent but doable
        elif 45 < days_until_move <= 90:
            return 0.6  # Future planning
        else:
            return 0.3  # Too soon or too far
    
    def _calculate_overall_score(self, factors: Dict) -> float:
        """Calculate weighted overall score"""
        weights = {
            "text_analysis": 0.4,
            "completeness": 0.3,
            "timing": 0.3
        }
        
        total_score = 0
        for factor, value in factors.items():
            if factor in weights:
                if isinstance(value, dict) and "overall" in value:
                    score = value["overall"]
                else:
                    score = value
                total_score += weights[factor] * score
                
        return min(total_score, 1.0)


# Usage example
async def example_usage():
    """Example of using the hybrid AI service"""
    ai_service = MultimodalAIService()
    
    # Process a maintenance request
    maintenance_request = {
        "id": "REQ-2024-001",
        "description": "Water leak under kitchen sink, getting worse",
        "images": ["/path/to/kitchen_leak_1.jpg", "/path/to/kitchen_leak_2.jpg"]
    }
    
    result = await ai_service.process_maintenance_request(maintenance_request)
    print(f"Urgency Score: {result['urgency_score']}")
    print(f"Recommendations: {result['recommended_actions']}")
    
    # Score a rental lead
    lead_scorer = LeadScoringAI(ai_service)
    inquiry = {
        "id": "LEAD-2024-001",
        "name": "John Smith",
        "email": "john@email.com",
        "message": "Looking for a 2BR apartment, moving next month. Stable job, excellent credit.",
        "move_date": "2024-02-15",
        "budget": "$2000"
    }
    
    lead_score = await lead_scorer.score_lead(inquiry)
    print(f"Lead Score: {lead_score['score']}")
    print(f"Priority: {lead_score['priority']}")


if __name__ == "__main__":
    asyncio.run(example_usage())