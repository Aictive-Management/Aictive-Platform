# AI Implementation Guide - Aictive Platform V2

## ⚠️ CRITICAL DISTINCTION: Development Tools vs Runtime Features

### Development Tools (What YOU use to BUILD the app)
- **SuperClaude**: Enhanced Claude interface with commands like `/thinkdeep`
- **MCP Servers**: File access, browser control in Claude desktop
- **Claude Code**: The tool you're using right now to develop
- **Personas**: Different modes Claude adopts while helping you code

### Runtime Features (What your APP uses in PRODUCTION)
- **Anthropic API**: The actual API your application calls
- **OpenAI API**: Optional additional AI service
- **Supabase**: Database and authentication
- **Inngest**: Background job processing
- **Meilisearch**: Search functionality

## ✅ CORRECT Implementation Pattern

```python
# CORRECT: Using Anthropic API in production
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
response = client.messages.create(
    model="claude-3-sonnet-20240229",
    messages=[{"role": "user", "content": prompt}]
)
```

## ❌ INCORRECT Implementation Pattern

```python
# WRONG: Trying to use SuperClaude features in production
result = await superclaude.thinkdeep(prompt)  # This doesn't exist!
persona = "analyzer"  # Personas are for developers, not runtime
mcp_server = "context7"  # MCP servers aren't accessible from your app
```

## The 13 Agents - How They Actually Work

Each agent is differentiated by:

### 1. Role-Specific Prompting
```python
# Property Manager Prompt
prompt = """You are an experienced property manager responsible for 
overall property operations. Your priorities are maintaining property 
value, ensuring tenant satisfaction, and regulatory compliance..."""

# Leasing Agent Prompt  
prompt = """You are a leasing agent focused on customer service and 
filling vacancies. You excel at property showings and qualifying 
prospects..."""
```

### 2. Task-Specific Instructions
```python
task_prompts = {
    "analyze_maintenance": "Assess urgency, estimate costs, recommend vendors...",
    "screen_application": "Evaluate creditworthiness, verify income, check references...",
    "schedule_showing": "Coordinate availability, prepare property, conduct tour..."
}
```

### 3. Decision Logic (Plain Python)
```python
# Not SuperClaude hooks - just Python functions
if urgency == "emergency":
    notify_on_call_staff()
    expedite_vendor_response()
```

## Architecture Layers

```
┌─────────────────────────────────────────────┐
│          Your Application Code              │
│  (Python, FastAPI, React, etc.)            │
├─────────────────────────────────────────────┤
│         AI Service Layer                    │
│  - Anthropic API client                    │
│  - Role-specific prompting                 │
│  - Response parsing                        │
├─────────────────────────────────────────────┤
│         External Services                   │
│  - Anthropic Claude API                    │
│  - OpenAI API (optional)                   │
│  - Supabase (database)                     │
│  - Inngest (background jobs)               │
│  - Meilisearch (search)                    │
└─────────────────────────────────────────────┘

Developer Tools (NOT part of the above):
- SuperClaude (for development)
- Claude Code (for development)
- MCP Servers (for development)
```

## File Naming Conventions

To avoid confusion, use clear naming:

### ✅ Good File Names
- `ai_service.py` - Runtime AI functionality
- `agent_prompts.py` - Role-specific prompts
- `workflow_coordinator.py` - Agent orchestration
- `anthropic_client.py` - API client wrapper

### ❌ Avoid These Names
- `superclaude_integration.py` - Implies runtime SuperClaude
- `mcp_connector.py` - MCP isn't available at runtime
- `persona_manager.py` - Personas are dev concepts

## Testing Without Confusion

```python
# Test file example
def test_property_manager_agent():
    """Test property manager agent using mock API"""
    
    # Mock the Anthropic API response
    mock_response = {
        "urgency": "high",
        "estimated_cost": "$200-400",
        "recommended_action": "Schedule plumber within 24 hours"
    }
    
    # Test the prompt building
    prompt = build_property_manager_prompt(maintenance_request)
    assert "property manager" in prompt.lower()
    
    # Don't test SuperClaude features - they don't exist at runtime!
```

## Documentation Standards

When documenting, always clarify:

```python
class PropertyManagerAgent:
    """
    Property Manager agent for the Aictive platform.
    
    Uses the Anthropic Claude API with role-specific prompting.
    Does NOT use SuperClaude (which is a development tool only).
    
    Capabilities:
    - Analyzes maintenance requests
    - Prioritizes based on urgency
    - Coordinates with vendors
    """
```

## Common Misconceptions to Avoid

1. **"Agents have SuperClaude personas"**
   - ❌ Wrong: Personas are for developers using Claude
   - ✅ Right: Agents have role-specific prompts

2. **"We can use MCP servers in production"**
   - ❌ Wrong: MCP servers are Claude desktop tools
   - ✅ Right: Use standard APIs and services

3. **"Commands like thinkdeep make agents smarter"**
   - ❌ Wrong: These are UI commands for developers
   - ✅ Right: Intelligence comes from good prompting

4. **"SuperClaude integration enhances AI capabilities"**
   - ❌ Wrong: SuperClaude isn't accessible from apps
   - ✅ Right: Use Anthropic's API with optimized prompts

## Checklist for New Features

Before implementing any AI feature, ask:

- [ ] Am I trying to use a SuperClaude command? (Don't!)
- [ ] Am I referencing MCP servers? (Use regular APIs instead)
- [ ] Am I using standard Anthropic/OpenAI APIs? (Good!)
- [ ] Are my prompts role-specific and well-crafted? (Essential!)
- [ ] Is my orchestration just Python code? (Perfect!)

## Remember

**SuperClaude helped you BUILD this application.**
**SuperClaude does NOT RUN IN this application.**

The intelligence comes from:
- Well-designed prompts
- Smart orchestration logic  
- Proper use of AI APIs
- Good software architecture

Not from trying to embed development tools into production code.