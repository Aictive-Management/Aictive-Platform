#!/usr/bin/env python3
"""
Setup Supabase Database Schema for Aictive Platform V2
Creates all required tables for the 13 property management roles
"""

import os
import sys
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Database schema for 13 roles
SCHEMA = """
-- Agent roles table
CREATE TABLE IF NOT EXISTS agent_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name TEXT UNIQUE NOT NULL,
    display_name TEXT NOT NULL,
    description TEXT,
    superclaude_persona TEXT,
    primary_commands TEXT[],
    mcp_servers TEXT[],
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Property management requests
CREATE TABLE IF NOT EXISTS requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_type TEXT NOT NULL,
    property_id TEXT,
    unit_id TEXT,
    tenant_id TEXT,
    description TEXT,
    urgency_level TEXT,
    status TEXT DEFAULT 'pending',
    assigned_role TEXT REFERENCES agent_roles(role_name),
    ai_analysis JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Agent activities log
CREATE TABLE IF NOT EXISTS agent_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT REFERENCES agent_roles(role_name),
    activity_type TEXT,
    request_id UUID REFERENCES requests(id),
    action_taken TEXT,
    result JSONB,
    duration_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Agent performance metrics
CREATE TABLE IF NOT EXISTS agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT REFERENCES agent_roles(role_name) UNIQUE,
    requests_today INTEGER DEFAULT 0,
    requests_week INTEGER DEFAULT 0,
    requests_month INTEGER DEFAULT 0,
    avg_response_time_ms INTEGER,
    success_rate DECIMAL(5,2),
    last_active TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Maintenance requests
CREATE TABLE IF NOT EXISTS maintenance_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id),
    issue_type TEXT,
    location TEXT,
    severity TEXT,
    parts_needed TEXT[],
    estimated_cost DECIMAL(10,2),
    work_order_id TEXT,
    vendor_assigned TEXT,
    scheduled_date DATE,
    completed_date DATE,
    photos TEXT[],
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Lease applications
CREATE TABLE IF NOT EXISTS applications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    request_id UUID REFERENCES requests(id),
    applicant_name TEXT,
    applicant_email TEXT,
    property_interested TEXT,
    lead_score DECIMAL(3,2),
    screening_results JSONB,
    background_check_status TEXT,
    credit_score INTEGER,
    income_verified BOOLEAN DEFAULT FALSE,
    references_checked BOOLEAN DEFAULT FALSE,
    decision TEXT,
    decision_date DATE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Document knowledge base
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role TEXT REFERENCES agent_roles(role_name),
    document_type TEXT,
    title TEXT,
    content TEXT,
    file_path TEXT,
    category TEXT,
    tags TEXT[],
    indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Swarm coordination
CREATE TABLE IF NOT EXISTS swarm_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    swarm_id TEXT,
    task_type TEXT,
    coordinator_role TEXT REFERENCES agent_roles(role_name),
    participating_roles TEXT[],
    status TEXT DEFAULT 'pending',
    context JSONB,
    decisions JSONB,
    hooks_triggered TEXT[],
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Hook executions
CREATE TABLE IF NOT EXISTS hook_executions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hook_type TEXT,
    trigger_event TEXT,
    swarm_task_id UUID REFERENCES swarm_tasks(id),
    input_data JSONB,
    output_data JSONB,
    execution_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc', NOW())
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_requests_status ON requests(status);
CREATE INDEX IF NOT EXISTS idx_requests_created ON requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_activities_role ON agent_activities(role);
CREATE INDEX IF NOT EXISTS idx_activities_created ON agent_activities(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_documents_role ON documents(role);
CREATE INDEX IF NOT EXISTS idx_documents_indexed ON documents(indexed);
CREATE INDEX IF NOT EXISTS idx_swarm_status ON swarm_tasks(status);
"""

# Initial data for 13 roles
ROLES_DATA = [
    {
        "role_name": "property_manager",
        "display_name": "Property Manager",
        "description": "Overall property operations and tenant relations",
        "superclaude_persona": "analyzer",
        "primary_commands": ["thinkdeep", "context", "organize"],
        "mcp_servers": ["calendar", "filesystem"]
    },
    {
        "role_name": "director_leasing",
        "display_name": "Director of Leasing",
        "description": "Leasing operations and lead management",
        "superclaude_persona": "frontend",
        "primary_commands": ["magic", "seq", "showme"],
        "mcp_servers": ["sequential", "obsidian"]
    },
    {
        "role_name": "leasing_agent",
        "display_name": "Leasing Agent",
        "description": "Direct tenant interaction and property showings",
        "superclaude_persona": "designer",
        "primary_commands": ["showme", "magic", "refine"],
        "mcp_servers": ["figma"]
    },
    {
        "role_name": "assistant_manager",
        "display_name": "Assistant Property Manager",
        "description": "Support property manager with daily operations",
        "superclaude_persona": "analyzer",
        "primary_commands": ["context", "organize", "timeline"],
        "mcp_servers": ["filesystem", "calendar"]
    },
    {
        "role_name": "regional_manager",
        "display_name": "Regional Manager",
        "description": "Oversee multiple properties in region",
        "superclaude_persona": "executive",
        "primary_commands": ["thinkdeep", "expand", "refine"],
        "mcp_servers": ["context7", "obsidian"]
    },
    {
        "role_name": "bookkeeper",
        "display_name": "Bookkeeper",
        "description": "Financial records and reporting",
        "superclaude_persona": "backend",
        "primary_commands": ["calc", "organize", "timeline"],
        "mcp_servers": ["filesystem"]
    },
    {
        "role_name": "admin_assistant",
        "display_name": "Administrative Assistant",
        "description": "Administrative support and documentation",
        "superclaude_persona": "documentation",
        "primary_commands": ["organize", "format", "refine"],
        "mcp_servers": ["filesystem", "obsidian"]
    },
    {
        "role_name": "property_accountant",
        "display_name": "Property Accountant",
        "description": "Advanced financial management and analysis",
        "superclaude_persona": "analyst",
        "primary_commands": ["calc", "thinkdeep", "expand"],
        "mcp_servers": ["sequential", "context7"]
    },
    {
        "role_name": "marketing_manager",
        "display_name": "Marketing Manager",
        "description": "Property marketing and advertising",
        "superclaude_persona": "frontend",
        "primary_commands": ["magic", "showme", "enhance"],
        "mcp_servers": ["figma", "obsidian"]
    },
    {
        "role_name": "client_experience",
        "display_name": "Director of Client Experience",
        "description": "Enhance resident satisfaction and retention",
        "superclaude_persona": "designer",
        "primary_commands": ["feel", "refine", "showme"],
        "mcp_servers": ["figma", "context7"]
    },
    {
        "role_name": "resident_services",
        "display_name": "Resident Services Manager",
        "description": "Handle resident needs and concerns",
        "superclaude_persona": "analyzer",
        "primary_commands": ["context", "feel", "timeline"],
        "mcp_servers": ["calendar", "filesystem"]
    },
    {
        "role_name": "staff_manager",
        "display_name": "Manager (Unspecified)",
        "description": "General management responsibilities",
        "superclaude_persona": "executive",
        "primary_commands": ["thinkdeep", "organize", "expand"],
        "mcp_servers": ["context7", "sequential"]
    },
    {
        "role_name": "maintenance_coordinator",
        "display_name": "Maintenance Coordinator",
        "description": "Coordinate maintenance requests and vendors",
        "superclaude_persona": "backend",
        "primary_commands": ["organize", "timeline", "context"],
        "mcp_servers": ["calendar", "filesystem"]
    }
]


def setup_database():
    """Set up the database schema and initial data"""
    
    # Check for required environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key or "your_" in supabase_url:
        print("❌ Error: Supabase credentials not configured!")
        print("Please add SUPABASE_URL and SUPABASE_ANON_KEY to your .env file")
        sys.exit(1)
    
    print("🔄 Connecting to Supabase...")
    
    try:
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("✅ Connected to Supabase")
        
        # Execute schema
        print("🔄 Creating database schema...")
        # Note: In production, use Supabase migrations
        # For now, we'll create tables via the Supabase dashboard
        print("⚠️  Please run the schema SQL in your Supabase SQL editor")
        
        # Insert initial role data
        print("🔄 Inserting agent roles...")
        
        for role in ROLES_DATA:
            try:
                supabase.table('agent_roles').upsert(role).execute()
                print(f"✅ Created role: {role['display_name']}")
            except Exception as e:
                print(f"⚠️  Role {role['role_name']} might already exist: {e}")
        
        # Create initial metrics entries
        print("🔄 Creating initial metrics...")
        
        for role in ROLES_DATA:
            try:
                supabase.table('agent_metrics').upsert({
                    "role": role["role_name"],
                    "requests_today": 0,
                    "requests_week": 0,
                    "requests_month": 0,
                    "success_rate": 100.0
                }).execute()
            except Exception as e:
                print(f"⚠️  Metrics for {role['role_name']} might already exist")
        
        print("\n✅ Database setup complete!")
        print("\n📋 Next steps:")
        print("1. Copy the schema from this file")
        print("2. Go to your Supabase dashboard")
        print("3. Navigate to SQL Editor")
        print("4. Paste and run the schema")
        print("5. Enable Row Level Security on all tables")
        
        # Save schema to file for easy access
        with open("database_schema.sql", "w") as f:
            f.write(SCHEMA)
        print("\n💾 Schema saved to database_schema.sql")
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║          AICTIVE PLATFORM V2 - DATABASE SETUP             ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    setup_database()