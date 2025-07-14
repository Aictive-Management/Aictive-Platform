# Migration Guide: From Incorrect to Correct Implementation

## Quick Reference: What to Replace

### ❌ INCORRECT → ✅ CORRECT

```python
# ❌ WRONG: SuperClaude integration
from superclaude_integration import AictiveSuperClaudeOrchestrator
orchestrator = AictiveSuperClaudeOrchestrator()
result = await orchestrator.process_with_superclaude(
    role="property_manager",
    task_type="analyze",
    use_mcp=["context7"]  # MCP servers don't exist at runtime!
)

# ✅ CORRECT: Standard AI service
from correct_ai_implementation import AictiveAIService
ai_service = AictiveAIService()
result = await ai_service.process_request(
    role="property_manager",
    task="analyze_maintenance",
    data=request_data
)
```

## Files to Update

### 1. Replace Imports

In any file that imports SuperClaude-related modules:

```python
# ❌ Remove these imports:
from superclaude_integration import AictiveSuperClaudeOrchestrator
from swarm_hooks_integration import PropertyManagementSwarmV2

# ✅ Use these instead:
from correct_ai_implementation import AictiveAIService, WorkflowCoordinator
```

### 2. Update Database Schema

Remove SuperClaude-specific columns:

```sql
-- ❌ Remove these columns from agent_roles table:
ALTER TABLE agent_roles DROP COLUMN superclaude_persona;
ALTER TABLE agent_roles DROP COLUMN primary_commands;
ALTER TABLE agent_roles DROP COLUMN mcp_servers;

-- ✅ Add practical columns instead:
ALTER TABLE agent_roles ADD COLUMN decision_style TEXT;
ALTER TABLE agent_roles ADD COLUMN priority_focus TEXT;
```

### 3. Fix Agent Configurations

Replace SuperClaude concepts with real attributes:

```python
# ❌ WRONG: SuperClaude configuration
{
    "role": "property_manager",
    "persona": "analyzer",
    "commands": ["thinkdeep", "context"],
    "mcp_servers": ["calendar", "filesystem"]
}

# ✅ CORRECT: Real agent configuration
{
    "role": "property_manager",
    "focus": "Overall property operations",
    "decision_style": "balanced",
    "priority": "property_value_preservation",
    "capabilities": ["damage_assessment", "tenant_communication"]
}
```

### 4. Update API Endpoints

```python
# ❌ WRONG: Using SuperClaude orchestrator
@app.post("/api/agents/ask")
async def ask_agent(query: AgentQuery):
    response = await orchestrator.process_with_superclaude(
        role=query.role,
        task_type="answer_question",
        use_mcp=["context7"]
    )

# ✅ CORRECT: Using AI service
@app.post("/api/agents/ask")
async def ask_agent(query: AgentQuery):
    response = await ai_service.process_request(
        role=query.role,
        task="answer_question",
        data={"question": query.question}
    )
```

## Understanding the Concepts

### What Each Term ACTUALLY Means

| Term | What You Thought | What It Actually Is | What to Use Instead |
|------|------------------|---------------------|---------------------|
| SuperClaude | Runtime AI feature | Your development tool | Anthropic API |
| Personas | Agent personalities | Dev tool modes | Role-specific prompts |
| Commands (/thinkdeep) | API parameters | UI commands for you | Task-specific prompts |
| MCP Servers | Production services | Claude desktop tools | Regular APIs |
| Swarms | SuperClaude feature | Marketing term | Python orchestration |
| Hooks | SuperClaude hooks | Dev tool feature | Python functions |

## Step-by-Step Migration

### Step 1: Audit Your Code

Search for these terms and replace them:
```bash
# Find problematic files
grep -r "superclaude" .
grep -r "persona" .
grep -r "thinkdeep\|magic\|ultrathink" .
grep -r "mcp_servers\|context7\|sequential" .
```

### Step 2: Update Core Services

Replace the orchestrator initialization:
```python
# In main_v2.py or similar
# ❌ Remove:
orchestrator = AictiveSuperClaudeOrchestrator()
swarm = PropertyManagementSwarmV2()

# ✅ Add:
ai_service = AictiveAIService()
coordinator = WorkflowCoordinator()
```

### Step 3: Rewrite Agent Logic

Transform SuperClaude calls to AI service calls:
```python
# ❌ BEFORE:
result = await orchestrator.process_with_superclaude(
    role="property_manager",
    task_type="analyze_maintenance",
    data=request,
    use_mcp=["context7", "filesystem"]
)

# ✅ AFTER:
result = await ai_service.process_request(
    role="property_manager",
    task="analyze_maintenance",
    data=request
)
```

### Step 4: Update Tests

```python
# ❌ WRONG: Testing SuperClaude features
def test_superclaude_persona():
    assert agent.persona == "analyzer"
    assert "thinkdeep" in agent.commands

# ✅ CORRECT: Testing actual functionality
def test_property_manager_analysis():
    result = ai_service.process_request(
        role="property_manager",
        task="analyze_maintenance",
        data=test_request
    )
    assert result["success"]
    assert "urgency" in result["result"]
```

## Common Patterns to Fix

### Pattern 1: Persona-Based Decisions
```python
# ❌ WRONG:
if agent.persona == "analyzer":
    command = "thinkdeep"
elif agent.persona == "frontend":
    command = "magic"

# ✅ CORRECT:
if role == "property_manager":
    prompt_style = "analytical"
elif role == "leasing_agent":
    prompt_style = "customer_focused"
```

### Pattern 2: MCP Server Usage
```python
# ❌ WRONG:
mcp_context = get_mcp_server("context7")
enhanced_data = mcp_context.analyze(data)

# ✅ CORRECT:
# Just pass the data directly to the AI
result = await ai_service.process_request(role, task, data)
```

### Pattern 3: Command Execution
```python
# ❌ WRONG:
if task_complexity > 0.8:
    result = await execute_command("ultrathink", prompt)
else:
    result = await execute_command("thinkdeep", prompt)

# ✅ CORRECT:
# Adjust the prompt itself, not imaginary commands
if task_complexity > 0.8:
    prompt = build_detailed_analysis_prompt(data)
else:
    prompt = build_standard_prompt(data)
result = await ai_service.process_request(role, task, data)
```

## Verification Checklist

After migration, verify:

- [ ] No imports from `superclaude_integration.py`
- [ ] No references to personas, commands, or MCP servers
- [ ] All AI calls use `AictiveAIService` or similar
- [ ] Prompts are role-specific, not persona-based
- [ ] Tests check actual functionality, not SuperClaude features
- [ ] Documentation explains the correct approach
- [ ] No attempts to use development tools at runtime

## Remember

The intelligence in your system comes from:
1. **Well-crafted prompts** specific to each role
2. **Smart orchestration** of multiple agents
3. **Good software architecture**
4. **Proper use of AI APIs**

NOT from trying to use your development tools in production!