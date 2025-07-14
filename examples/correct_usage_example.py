#!/usr/bin/env python3
"""
CORRECT Usage Example - Aictive Platform V2

This shows the RIGHT way to use the AI agents without SuperClaude confusion.
Remember: SuperClaude is what you use to BUILD the app, not what runs IN the app.
"""

import os
import asyncio
from datetime import datetime
import sys
sys.path.append('..')

from correct_ai_implementation import AictiveAIService, WorkflowCoordinator, DecisionHooks


async def correct_example():
    """
    This is how the platform ACTUALLY works in production
    """
    
    print("""
    ========================================
    CORRECT AI Implementation Example
    ========================================
    
    This uses:
    ✅ Anthropic API (actual runtime API)
    ✅ Role-specific prompting
    ✅ Python orchestration
    ✅ Simple decision logic
    
    This does NOT use:
    ❌ SuperClaude (that's for development)
    ❌ MCP servers (those are in YOUR Claude)
    ❌ Personas (those guide YOUR development)
    ❌ Commands like /thinkdeep (those are for YOU)
    """)
    
    # Initialize the REAL services
    ai_service = AictiveAIService()
    coordinator = WorkflowCoordinator()
    
    # Example 1: Single Agent Request
    print("\n1. Single Agent Example - Property Manager")
    print("-" * 50)
    
    maintenance_data = {
        "tenant": "Jane Doe",
        "unit": "205",
        "issue": "Heating not working",
        "description": "Thermostat shows error code E3, no warm air coming out",
        "temperature": "58°F inside",
        "submitted": datetime.now().isoformat()
    }
    
    # This calls the Anthropic API with a role-specific prompt
    result = await ai_service.process_request(
        role="property_manager",
        task="analyze_maintenance",
        data=maintenance_data
    )
    
    if result["success"]:
        print(f"✅ Analysis complete")
        print(f"   Result: {result['result']}")
    else:
        print(f"❌ Error: {result.get('error')}")
    
    # Example 2: Multi-Agent Workflow
    print("\n\n2. Multi-Agent Workflow Example")
    print("-" * 50)
    
    # This coordinates multiple agents using Python logic
    workflow_result = await coordinator.process_maintenance_workflow(maintenance_data)
    
    print(f"✅ Workflow ID: {workflow_result['workflow_id']}")
    print(f"   Steps completed: {len(workflow_result['steps'])}")
    
    for i, step in enumerate(workflow_result['steps']):
        agent = step.get('role', 'unknown')
        success = "✅" if step.get('success') else "❌"
        print(f"   Step {i+1}: {agent} {success}")
    
    # Example 3: Decision Hooks (Plain Python)
    print("\n\n3. Decision Hooks Example")
    print("-" * 50)
    
    # These are just Python functions, not SuperClaude magic
    if workflow_result['steps'] and workflow_result['steps'][0]['success']:
        analysis = workflow_result['steps'][0]['result']
        
        # Check if emergency
        is_emergency = await DecisionHooks.check_emergency(analysis)
        print(f"   Emergency detected: {'Yes 🚨' if is_emergency else 'No'}")
        
        # Check spending threshold
        cost_estimate = analysis.get('estimated_cost_range', {}).get('max', 0)
        needs_approval = await DecisionHooks.check_spending_threshold(cost_estimate)
        print(f"   Needs approval: {'Yes' if needs_approval else 'No'}")
    
    # Example 4: What NOT to do
    print("\n\n4. What NOT to Do")
    print("-" * 50)
    print("""
    ❌ DON'T try to:
    - Call superclaude.thinkdeep()
    - Use MCP servers from your app
    - Set agent "personas"
    - Use /commands in your code
    
    ✅ DO:
    - Use the Anthropic API
    - Write good prompts
    - Orchestrate with Python
    - Keep it simple
    """)


async def show_prompt_example():
    """
    Show what actually makes agents "intelligent"
    """
    print("\n\n5. The Secret: Good Prompting")
    print("-" * 50)
    print("Here's what ACTUALLY makes each agent intelligent:\n")
    
    property_manager_prompt = """You are an experienced property manager responsible for overall property operations. 
Your priorities are maintaining property value, ensuring tenant satisfaction, and compliance with regulations.
You make balanced decisions considering both tenant needs and owner interests.

Analyze the maintenance request and provide:
1. Urgency level (emergency/high/medium/low)
2. Likely cause and required repairs
3. Estimated cost range
4. Recommended vendors or internal handling
5. Tenant communication plan

Format your response as JSON.

Input Data:
{
  "tenant": "Jane Doe",
  "unit": "205", 
  "issue": "Heating not working",
  "description": "Thermostat shows error code E3, no warm air coming out",
  "temperature": "58°F inside"
}

Remember to:
- Be specific and actionable
- Consider legal compliance
- Maintain professional standards
- Format response as requested"""
    
    print("PROPERTY MANAGER PROMPT:")
    print("=" * 80)
    print(property_manager_prompt)
    print("=" * 80)
    print("\n✅ This prompt is what gives the agent its 'role' and capabilities")
    print("✅ No SuperClaude needed - just good prompt engineering!")


if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║     AICTIVE V2 - CORRECT IMPLEMENTATION EXAMPLE           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY") or os.getenv("ANTHROPIC_API_KEY").startswith("your_"):
        print("\n⚠️  No Anthropic API key found!")
        print("This example shows the CORRECT implementation pattern.")
        print("To run it for real, add your API key to .env\n")
        
        # Show the example anyway
        asyncio.run(show_prompt_example())
    else:
        # Run the full example
        asyncio.run(correct_example())
        asyncio.run(show_prompt_example())