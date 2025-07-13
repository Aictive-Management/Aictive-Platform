"""
Aictive Platform V2 - Enhanced Architecture Integration
Combines AI Agents + Background Processing + Search
"""

import os
from typing import Dict, List, Optional
from datetime import datetime
import asyncio

# V2 Architecture Services
from supabase import create_client, Client
from inngest import Inngest
import meilisearch

# Our AI Components
from superclaude_integration import AictiveSuperClaudeOrchestrator
from swarm_hooks_integration import PropertyManagementSwarmV2


class AictiveV2Platform:
    """
    Enhanced platform with background processing and search
    """
    
    def __init__(self):
        # Initialize V2 services
        self.supabase = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_ANON_KEY")
        )
        self.inngest = Inngest(app_id="aictive-platform")
        self.search = meilisearch.Client(
            os.getenv("MEILISEARCH_HOST", "http://localhost:7700"),
            os.getenv("MEILISEARCH_KEY")
        )
        
        # Initialize AI components
        self.ai_swarm = PropertyManagementSwarmV2()
        self.orchestrator = AictiveSuperClaudeOrchestrator()
        
        # Register background functions
        self._register_background_jobs()
    
    def _register_background_jobs(self):
        """Register all background processing functions"""
        
        @self.inngest.create_function(
            fn_id="process-maintenance-request",
            trigger=self.inngest.trigger("maintenance/submitted")
        )
        async def process_maintenance(ctx):
            """Process maintenance request in background"""
            request_data = ctx.event.data
            
            # Step 1: AI Analysis (can take time)
            analysis = await self.ai_swarm.process_request({
                "type": "maintenance",
                **request_data
            })
            
            # Step 2: Store results
            await self.supabase.table('maintenance_requests').insert({
                "id": request_data["id"],
                "property_id": request_data["property_id"],
                "ai_analysis": analysis,
                "status": "analyzed",
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Step 3: Trigger next steps
            if analysis.get("urgency_score", 0) > 0.8:
                await ctx.send_event(
                    "maintenance/urgent",
                    data={"request_id": request_data["id"]}
                )
            
            return {"status": "completed", "analysis": analysis}
        
        @self.inngest.create_function(
            fn_id="process-application",
            trigger=self.inngest.trigger("application/submitted")
        )
        async def process_application(ctx):
            """Screen rental application in background"""
            app_data = ctx.event.data
            
            # AI screening
            screening = await self.orchestrator.process_with_superclaude(
                role="director_leasing",
                task_type="application_screening",
                data=app_data,
                use_mcp=["context7", "sequential"]
            )
            
            # Store results
            await self.supabase.table('applications').insert({
                "id": app_data["id"],
                "screening_results": screening,
                "score": screening.get("lead_score", 0),
                "status": "screened"
            }).execute()
            
            return screening
    
    async def submit_maintenance_request(self, request_data: Dict) -> Dict:
        """
        Submit maintenance request - returns immediately
        Processing happens in background
        """
        # Generate request ID
        request_id = f"REQ-{datetime.utcnow().timestamp()}"
        request_data["id"] = request_id
        
        # Queue for background processing
        await self.inngest.send(
            "maintenance/submitted",
            data=request_data
        )
        
        # Return immediately
        return {
            "request_id": request_id,
            "status": "queued",
            "message": "Your request is being processed. We'll notify you soon!"
        }
    
    async def search_knowledge_base(self, query: str, role: str = None) -> List[Dict]:
        """
        Search across all property management documents
        """
        # Search with role-specific filtering
        search_params = {
            "limit": 10,
            "attributesToHighlight": ["content"],
            "highlightPreTag": "<mark>",
            "highlightPostTag": "</mark>"
        }
        
        if role:
            search_params["filter"] = f"role = '{role}'"
        
        results = await self.search.index('property_knowledge').search(
            query,
            search_params
        )
        
        return results['hits']
    
    async def get_agent_dashboard(self, role: str) -> Dict:
        """
        Real-time dashboard for specific agent role
        """
        # Get recent activities
        activities = await self.supabase.table('agent_activities') \
            .select("*") \
            .eq('role', role) \
            .order('created_at', desc=True) \
            .limit(10) \
            .execute()
        
        # Get performance metrics
        metrics = await self.supabase.table('agent_metrics') \
            .select("*") \
            .eq('role', role) \
            .single() \
            .execute()
        
        return {
            "role": role,
            "recent_activities": activities.data,
            "metrics": metrics.data,
            "timestamp": datetime.utcnow().isoformat()
        }


# Example usage
async def example_v2_workflow():
    """Example of V2 architecture in action"""
    platform = AictiveV2Platform()
    
    # 1. Submit maintenance request (instant response)
    response = await platform.submit_maintenance_request({
        "property_id": "PROP-123",
        "unit_id": "UNIT-101",
        "description": "Water leak under kitchen sink",
        "tenant_id": "TENANT-001",
        "photos": ["leak1.jpg", "leak2.jpg"]
    })
    
    print(f"Request submitted: {response['request_id']}")
    # User can continue using the app while AI processes in background
    
    # 2. Search for similar issues
    similar = await platform.search_knowledge_base(
        "kitchen sink water leak",
        role="property_manager"
    )
    
    print(f"Found {len(similar)} similar cases")
    
    # 3. Check agent dashboard
    dashboard = await platform.get_agent_dashboard("property_manager")
    print(f"Property Manager processed {dashboard['metrics']['requests_today']} requests today")


if __name__ == "__main__":
    asyncio.run(example_v2_workflow())