-- Supabase Schema for Aictive Platform SOP Orchestration
-- This creates all necessary tables for workflow management

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- SOPs Table - Stores all standard operating procedures
CREATE TABLE sops (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    department VARCHAR(100) NOT NULL,
    category VARCHAR(100) NOT NULL,
    version INTEGER DEFAULT 1,
    is_active BOOLEAN DEFAULT true,
    
    -- Workflow definition
    steps JSONB NOT NULL, -- Array of step objects
    required_roles TEXT[], -- Roles that can execute this SOP
    escalation_path TEXT[], -- Role IDs for escalation
    
    -- Timing
    time_limit_hours INTEGER,
    priority VARCHAR(50) DEFAULT 'medium',
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_by UUID,
    
    CONSTRAINT valid_priority CHECK (priority IN ('low', 'medium', 'high', 'emergency'))
);

-- SOP Steps Structure (stored in JSONB):
-- {
--   "step_id": "step_001",
--   "name": "Acknowledge request",
--   "description": "Send acknowledgment to tenant",
--   "type": "human_action|automated|decision|parallel",
--   "assigned_role": "maintenance_tech",
--   "actions": ["send_email", "create_ticket", "update_system"],
--   "completion_criteria": {...},
--   "timeout_minutes": 30,
--   "next_steps": ["step_002", "step_003"] // Can branch
-- }

-- Workflow Instances - Running instances of SOPs
CREATE TABLE workflow_instances (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sop_id UUID REFERENCES sops(id) NOT NULL,
    
    -- Context
    trigger_type VARCHAR(100) NOT NULL, -- email, manual, scheduled, api
    trigger_id VARCHAR(255), -- email_id, ticket_id, etc.
    context JSONB NOT NULL, -- All relevant data for the workflow
    
    -- State
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_step_id VARCHAR(100),
    completed_steps JSONB DEFAULT '[]'::jsonb,
    step_results JSONB DEFAULT '{}'::jsonb,
    
    -- Participants
    initiated_by UUID,
    assigned_to UUID,
    current_role VARCHAR(100),
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    due_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_status CHECK (status IN ('pending', 'in_progress', 'waiting', 'completed', 'failed', 'cancelled'))
);

-- Workflow Steps - Detailed tracking of each step execution
CREATE TABLE workflow_steps (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_instance_id UUID REFERENCES workflow_instances(id) NOT NULL,
    step_id VARCHAR(100) NOT NULL,
    step_name VARCHAR(255),
    
    -- Execution details
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    assigned_role VARCHAR(100),
    assigned_user UUID,
    
    -- Actions and results
    actions_taken JSONB DEFAULT '[]'::jsonb,
    result JSONB,
    output_data JSONB,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    timeout_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_step_status CHECK (status IN ('pending', 'in_progress', 'completed', 'failed', 'skipped', 'timeout'))
);

-- Agent Communications - Track agent-to-agent messages
CREATE TABLE agent_communications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_instance_id UUID REFERENCES workflow_instances(id),
    
    -- Communication details
    from_role VARCHAR(100) NOT NULL,
    to_role VARCHAR(100) NOT NULL,
    message_type VARCHAR(50) NOT NULL, -- request, response, escalation, notification
    
    -- Content
    subject VARCHAR(255),
    message TEXT NOT NULL,
    data JSONB,
    
    -- State
    status VARCHAR(50) DEFAULT 'sent',
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    responded_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT valid_message_type CHECK (message_type IN ('request', 'response', 'escalation', 'notification', 'handoff'))
);

-- Workflow Templates - Pre-configured workflows for common scenarios
CREATE TABLE workflow_templates (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    
    -- Template definition
    trigger_conditions JSONB, -- When to use this template
    initial_context JSONB, -- Default context values
    sop_id UUID REFERENCES sops(id),
    
    -- Customization
    configurable_fields JSONB, -- Fields that can be customized
    role_mappings JSONB, -- Dynamic role assignments
    
    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Workflow Metrics - Track performance
CREATE TABLE workflow_metrics (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    workflow_instance_id UUID REFERENCES workflow_instances(id),
    
    -- Metrics
    total_duration_minutes INTEGER,
    steps_completed INTEGER,
    steps_failed INTEGER,
    escalations_count INTEGER,
    
    -- Performance indicators
    sla_met BOOLEAN,
    bottleneck_steps JSONB,
    
    -- Metadata
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_workflow_instances_status ON workflow_instances(status);
CREATE INDEX idx_workflow_instances_sop_id ON workflow_instances(sop_id);
CREATE INDEX idx_workflow_steps_workflow_id ON workflow_steps(workflow_instance_id);
CREATE INDEX idx_workflow_steps_status ON workflow_steps(status);
CREATE INDEX idx_agent_communications_workflow_id ON agent_communications(workflow_instance_id);

-- Create views for monitoring
CREATE VIEW active_workflows AS
SELECT 
    wi.id,
    wi.sop_id,
    s.name as sop_name,
    wi.status,
    wi.current_step_id,
    wi.current_role,
    wi.started_at,
    wi.due_at,
    EXTRACT(EPOCH FROM (NOW() - wi.started_at))/60 as duration_minutes
FROM workflow_instances wi
JOIN sops s ON wi.sop_id = s.id
WHERE wi.status IN ('in_progress', 'waiting');

-- Create view for role workload
CREATE VIEW role_workload AS
SELECT 
    ws.assigned_role,
    COUNT(DISTINCT wi.id) as active_workflows,
    COUNT(ws.id) as pending_steps,
    AVG(EXTRACT(EPOCH FROM (ws.completed_at - ws.started_at))/60) as avg_step_duration_minutes
FROM workflow_steps ws
JOIN workflow_instances wi ON ws.workflow_instance_id = wi.id
WHERE wi.status = 'in_progress' AND ws.status IN ('pending', 'in_progress')
GROUP BY ws.assigned_role;

-- Function to get next available agent for a role
CREATE OR REPLACE FUNCTION get_next_available_agent(p_role VARCHAR)
RETURNS TABLE(user_id UUID, workload_count INTEGER) AS $$
BEGIN
    -- This would integrate with your staff table
    -- For now, returns mock data
    RETURN QUERY
    SELECT 
        gen_random_uuid() as user_id,
        0 as workload_count
    LIMIT 1;
END;
$$ LANGUAGE plpgsql;

-- Trigger to update workflow instance status
CREATE OR REPLACE FUNCTION update_workflow_status()
RETURNS TRIGGER AS $$
BEGIN
    -- Update workflow instance when step completes
    IF NEW.status = 'completed' THEN
        UPDATE workflow_instances
        SET 
            completed_steps = completed_steps || jsonb_build_array(NEW.step_id),
            updated_at = NOW()
        WHERE id = NEW.workflow_instance_id;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER workflow_step_completed
AFTER UPDATE OF status ON workflow_steps
FOR EACH ROW
WHEN (NEW.status = 'completed')
EXECUTE FUNCTION update_workflow_status();