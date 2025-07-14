#!/usr/bin/env python3
"""
Aictive Platform V2 - Main API Server
Combines 13 property management roles with AI-powered automation
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Initialize FastAPI
app = FastAPI(
    title="Aictive Platform V2",
    description="AI-powered property management with 13 specialized agents",
    version="2.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import our V2 components
from v2_architecture_integration import AictiveV2Platform
from correct_ai_implementation import AictiveAIService, WorkflowCoordinator, DecisionHooks

# Initialize platform
platform = AictiveV2Platform()
ai_service = AictiveAIService()
coordinator = WorkflowCoordinator()


# Request models
class MaintenanceRequest(BaseModel):
    property_id: str
    unit_id: str
    tenant_id: str
    description: str
    photos: Optional[List[str]] = []
    priority: Optional[str] = "normal"


class RentalApplication(BaseModel):
    applicant_name: str
    applicant_email: str
    phone: str
    property_interested: str
    move_in_date: str
    employment_info: Dict[str, Any]
    references: List[Dict[str, str]]


class AgentQuery(BaseModel):
    role: str
    question: str
    context: Optional[Dict[str, Any]] = {}


# Health check
@app.get("/")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "platform": "Aictive V2",
        "agents": 13,
        "timestamp": datetime.utcnow().isoformat()
    }


# Submit maintenance request
@app.post("/api/maintenance/submit")
async def submit_maintenance(request: MaintenanceRequest):
    """
    Submit a maintenance request for background processing
    Returns immediately while AI processes in background
    """
    try:
        result = await platform.submit_maintenance_request(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Submit rental application
@app.post("/api/applications/submit")
async def submit_application(application: RentalApplication):
    """
    Submit rental application for AI screening
    """
    try:
        # Queue for background processing
        await platform.inngest.send(
            "application/submitted",
            data=application.dict()
        )
        
        return {
            "status": "submitted",
            "message": "Application received and queued for screening",
            "application_id": f"APP-{datetime.utcnow().timestamp()}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Query knowledge base
@app.post("/api/knowledge/search")
async def search_knowledge(query: str, role: Optional[str] = None):
    """
    Search property management knowledge base
    """
    try:
        results = await platform.search_knowledge_base(query, role)
        return {
            "query": query,
            "role_filter": role,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Ask an agent
@app.post("/api/agents/ask")
async def ask_agent(query: AgentQuery):
    """
    Ask a specific agent a question using SuperClaude
    """
    try:
        response = await ai_service.process_request(
            role=query.role,
            task="answer_question",
            data={
                "question": query.question,
                "context": query.context
            }
        )
        
        return {
            "role": query.role,
            "question": query.question,
            "response": response
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get agent dashboard
@app.get("/api/agents/{role}/dashboard")
async def get_agent_dashboard(role: str):
    """
    Get real-time dashboard for specific agent role
    """
    try:
        dashboard = await platform.get_agent_dashboard(role)
        return dashboard
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# List all agents
@app.get("/api/agents")
async def list_agents():
    """
    List all 13 property management agents
    """
    agents = [
        {
            "role": "property_manager",
            "name": "Property Manager",
            "description": "Overall property operations",
            "superclaude_persona": "analyzer"
        },
        {
            "role": "director_leasing",
            "name": "Director of Leasing",
            "description": "Leasing operations and lead management",
            "superclaude_persona": "frontend"
        },
        {
            "role": "leasing_agent",
            "name": "Leasing Agent",
            "description": "Direct tenant interaction",
            "superclaude_persona": "designer"
        },
        {
            "role": "assistant_manager",
            "name": "Assistant Property Manager",
            "description": "Support daily operations",
            "superclaude_persona": "analyzer"
        },
        {
            "role": "regional_manager",
            "name": "Regional Manager",
            "description": "Oversee multiple properties",
            "superclaude_persona": "executive"
        },
        {
            "role": "bookkeeper",
            "name": "Bookkeeper",
            "description": "Financial records",
            "superclaude_persona": "backend"
        },
        {
            "role": "admin_assistant",
            "name": "Administrative Assistant",
            "description": "Administrative support",
            "superclaude_persona": "documentation"
        },
        {
            "role": "property_accountant",
            "name": "Property Accountant",
            "description": "Advanced financial management",
            "superclaude_persona": "analyst"
        },
        {
            "role": "marketing_manager",
            "name": "Marketing Manager",
            "description": "Property marketing",
            "superclaude_persona": "frontend"
        },
        {
            "role": "client_experience",
            "name": "Director of Client Experience",
            "description": "Resident satisfaction",
            "superclaude_persona": "designer"
        },
        {
            "role": "resident_services",
            "name": "Resident Services Manager",
            "description": "Handle resident needs",
            "superclaude_persona": "analyzer"
        },
        {
            "role": "staff_manager",
            "name": "Manager (Unspecified)",
            "description": "General management",
            "superclaude_persona": "executive"
        },
        {
            "role": "maintenance_coordinator",
            "name": "Maintenance Coordinator",
            "description": "Coordinate maintenance",
            "superclaude_persona": "backend"
        }
    ]
    
    return {
        "agents": agents,
        "total": len(agents)
    }


# Coordinate agent swarm
@app.post("/api/swarm/coordinate")
async def coordinate_swarm(
    task_type: str,
    coordinator_role: str,
    participating_roles: List[str],
    task_data: Dict[str, Any]
):
    """
    Coordinate multiple agents for complex tasks
    """
    try:
        result = await swarm.coordinate_agents(
            coordinator_role=coordinator_role,
            participating_roles=participating_roles,
            task_data={
                "type": task_type,
                **task_data
            }
        )
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Get system stats
@app.get("/api/stats")
async def get_stats():
    """
    Get platform statistics
    """
    try:
        # This would connect to Supabase in production
        return {
            "platform": "Aictive V2",
            "total_agents": 13,
            "requests_today": 42,
            "avg_response_time_ms": 1250,
            "active_swarms": 3,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          AICTIVE PLATFORM V2 - API SERVER                 ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check configuration
    required_vars = ["ANTHROPIC_API_KEY", "SUPABASE_URL", "SUPABASE_ANON_KEY"]
    missing = [v for v in required_vars if not os.getenv(v) or "your_" in os.getenv(v, "")]
    
    if missing:
        print(f"❌ Missing configuration: {', '.join(missing)}")
        print("Please update your .env file")
    else:
        print("✅ Configuration loaded")
        print("🚀 Starting API server on http://localhost:8000")
        print("\n📚 API Documentation: http://localhost:8000/docs")
        
        uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)