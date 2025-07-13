-- Aictive Platform V2 Database Schema
-- For Supabase PostgreSQL

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

-- Enable Row Level Security
ALTER TABLE agent_roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_activities ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE maintenance_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE applications ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE swarm_tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE hook_executions ENABLE ROW LEVEL SECURITY;

-- Create basic RLS policies (customize based on your auth setup)
-- Example: Allow authenticated users to read agent roles
CREATE POLICY "Allow authenticated read agent_roles" ON agent_roles
    FOR SELECT USING (auth.role() = 'authenticated');

-- Example: Allow service role full access
CREATE POLICY "Service role full access" ON requests
    FOR ALL USING (auth.role() = 'service_role');

-- Add more specific RLS policies based on your requirements