"""
SOP Orchestration Engine for Aictive Platform
Manages workflow execution with agent-to-agent communication
"""
import asyncio
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import logging
from dataclasses import dataclass, field
from supabase import create_client, Client
import os

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class StepStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    TIMEOUT = "timeout"

class StepType(Enum):
    HUMAN_ACTION = "human_action"
    AUTOMATED = "automated"
    DECISION = "decision"
    PARALLEL = "parallel"

@dataclass
class WorkflowStep:
    """Represents a single step in an SOP workflow"""
    step_id: str
    name: str
    description: str
    step_type: StepType
    assigned_role: str
    actions: List[str]
    completion_criteria: Dict[str, Any]
    timeout_minutes: int
    next_steps: List[str]
    conditions: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None

@dataclass
class WorkflowContext:
    """Context data for workflow execution"""
    workflow_instance_id: str
    trigger_type: str
    trigger_id: str
    data: Dict[str, Any] = field(default_factory=dict)
    step_results: Dict[str, Any] = field(default_factory=dict)
    current_step_id: Optional[str] = None
    completed_steps: List[str] = field(default_factory=list)

class SOPOrchestrationEngine:
    """Main orchestration engine for SOP workflows"""
    
    def __init__(self, supabase_url: str = None, supabase_key: str = None):
        # Initialize Supabase client
        url = supabase_url or os.getenv("SUPABASE_URL")
        key = supabase_key or os.getenv("SUPABASE_ANON_KEY")
        self.supabase: Client = create_client(url, key)
        
        # Agent registry (role -> agent instance)
        self.agents: Dict[str, 'BaseAgent'] = {}
        
        # Active workflows
        self.active_workflows: Dict[str, WorkflowContext] = {}
        
        # Event handlers
        self.event_handlers: Dict[str, List[callable]] = {}
        
    async def load_sop(self, sop_id: str) -> Dict[str, Any]:
        """Load SOP definition from database"""
        try:
            response = self.supabase.table('sops').select("*").eq('id', sop_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to load SOP {sop_id}: {str(e)}")
            raise
    
    async def create_workflow_instance(
        self,
        sop_id: str,
        trigger_type: str,
        trigger_id: str,
        initial_context: Dict[str, Any],
        initiated_by: Optional[str] = None
    ) -> str:
        """Create a new workflow instance"""
        try:
            # Load SOP
            sop = await self.load_sop(sop_id)
            
            # Calculate due date based on SOP time limit
            due_at = None
            if sop.get('time_limit_hours'):
                due_at = (datetime.utcnow() + timedelta(hours=sop['time_limit_hours'])).isoformat()
            
            # Create workflow instance
            workflow_data = {
                "sop_id": sop_id,
                "trigger_type": trigger_type,
                "trigger_id": trigger_id,
                "context": initial_context,
                "status": WorkflowStatus.PENDING.value,
                "initiated_by": initiated_by,
                "due_at": due_at
            }
            
            response = self.supabase.table('workflow_instances').insert(workflow_data).execute()
            workflow_instance = response.data[0]
            
            # Create context
            context = WorkflowContext(
                workflow_instance_id=workflow_instance['id'],
                trigger_type=trigger_type,
                trigger_id=trigger_id,
                data=initial_context
            )
            
            self.active_workflows[workflow_instance['id']] = context
            
            logger.info(f"Created workflow instance {workflow_instance['id']} for SOP {sop_id}")
            return workflow_instance['id']
            
        except Exception as e:
            logger.error(f"Failed to create workflow instance: {str(e)}")
            raise
    
    async def start_workflow(self, workflow_instance_id: str) -> None:
        """Start executing a workflow"""
        try:
            # Update status to in_progress
            self.supabase.table('workflow_instances').update({
                "status": WorkflowStatus.IN_PROGRESS.value,
                "started_at": datetime.utcnow().isoformat()
            }).eq('id', workflow_instance_id).execute()
            
            # Get workflow context
            context = self.active_workflows.get(workflow_instance_id)
            if not context:
                # Load from database
                instance = self.supabase.table('workflow_instances').select("*").eq('id', workflow_instance_id).single().execute()
                context = WorkflowContext(
                    workflow_instance_id=workflow_instance_id,
                    trigger_type=instance.data['trigger_type'],
                    trigger_id=instance.data['trigger_id'],
                    data=instance.data['context']
                )
                self.active_workflows[workflow_instance_id] = context
            
            # Load SOP steps
            instance = self.supabase.table('workflow_instances').select("*, sops(*)").eq('id', workflow_instance_id).single().execute()
            sop = instance.data['sops']
            steps = sop['steps']
            
            # Find and execute first step
            first_step = self._find_first_step(steps)
            if first_step:
                await self._execute_step(context, first_step, steps)
            
        except Exception as e:
            logger.error(f"Failed to start workflow {workflow_instance_id}: {str(e)}")
            await self._fail_workflow(workflow_instance_id, str(e))
    
    async def _execute_step(
        self,
        context: WorkflowContext,
        step: Dict[str, Any],
        all_steps: List[Dict[str, Any]]
    ) -> None:
        """Execute a single workflow step"""
        step_id = step['step_id']
        logger.info(f"Executing step {step_id} in workflow {context.workflow_instance_id}")
        
        try:
            # Create step record
            step_record = {
                "workflow_instance_id": context.workflow_instance_id,
                "step_id": step_id,
                "step_name": step['name'],
                "status": StepStatus.IN_PROGRESS.value,
                "assigned_role": step['assigned_role'],
                "started_at": datetime.utcnow().isoformat()
            }
            
            if step.get('timeout_minutes'):
                step_record['timeout_at'] = (
                    datetime.utcnow() + timedelta(minutes=step['timeout_minutes'])
                ).isoformat()
            
            response = self.supabase.table('workflow_steps').insert(step_record).execute()
            db_step_id = response.data[0]['id']
            
            # Update current step in workflow
            context.current_step_id = step_id
            self.supabase.table('workflow_instances').update({
                "current_step_id": step_id,
                "current_role": step['assigned_role']
            }).eq('id', context.workflow_instance_id).execute()
            
            # Execute based on step type
            step_type = StepType(step['type'])
            
            if step_type == StepType.AUTOMATED:
                result = await self._execute_automated_step(context, step)
            elif step_type == StepType.HUMAN_ACTION:
                result = await self._execute_human_step(context, step)
            elif step_type == StepType.DECISION:
                result = await self._execute_decision_step(context, step)
            elif step_type == StepType.PARALLEL:
                result = await self._execute_parallel_steps(context, step, all_steps)
            else:
                raise ValueError(f"Unknown step type: {step_type}")
            
            # Update step record with result
            self.supabase.table('workflow_steps').update({
                "status": StepStatus.COMPLETED.value,
                "completed_at": datetime.utcnow().isoformat(),
                "result": result,
                "output_data": result.get('output', {})
            }).eq('id', db_step_id).execute()
            
            # Store result in context
            context.step_results[step_id] = result
            context.completed_steps.append(step_id)
            
            # Determine next steps
            next_steps = self._determine_next_steps(step, result)
            
            # Execute next steps
            for next_step_id in next_steps:
                next_step = self._find_step_by_id(all_steps, next_step_id)
                if next_step:
                    await self._execute_step(context, next_step, all_steps)
            
            # Check if workflow is complete
            if not next_steps:
                await self._complete_workflow(context.workflow_instance_id)
                
        except Exception as e:
            logger.error(f"Failed to execute step {step_id}: {str(e)}")
            # Update step status
            self.supabase.table('workflow_steps').update({
                "status": StepStatus.FAILED.value,
                "completed_at": datetime.utcnow().isoformat(),
                "result": {"error": str(e)}
            }).eq('step_id', step_id).eq('workflow_instance_id', context.workflow_instance_id).execute()
            
            # Fail the workflow
            await self._fail_workflow(context.workflow_instance_id, f"Step {step_id} failed: {str(e)}")
    
    async def _execute_automated_step(
        self,
        context: WorkflowContext,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute an automated step using the assigned agent"""
        role = step['assigned_role']
        agent = self.agents.get(role)
        
        if not agent:
            raise ValueError(f"No agent registered for role: {role}")
        
        # Prepare input data
        input_data = {
            "context": context.data,
            "previous_results": context.step_results,
            "step_config": step
        }
        
        # Execute agent action
        actions = step.get('actions', [])
        results = {}
        
        for action in actions:
            action_result = await agent.execute_action(action, input_data)
            results[action] = action_result
        
        # Check completion criteria
        completion_met = self._check_completion_criteria(
            step.get('completion_criteria', {}),
            results
        )
        
        return {
            "completed": completion_met,
            "output": results,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_human_step(
        self,
        context: WorkflowContext,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a human action step"""
        role = step['assigned_role']
        
        # Send notification to human agent
        await self._notify_human_agent(role, context, step)
        
        # For demo purposes, simulate human completion after delay
        # In production, this would wait for actual human input
        await asyncio.sleep(5)
        
        return {
            "completed": True,
            "output": {
                "action_taken": "simulated_human_action",
                "notes": "Human agent completed the task"
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_decision_step(
        self,
        context: WorkflowContext,
        step: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a decision step"""
        role = step['assigned_role']
        agent = self.agents.get(role)
        
        if not agent:
            # Use human decision
            return await self._execute_human_step(context, step)
        
        # Get decision from agent
        decision_input = {
            "context": context.data,
            "previous_results": context.step_results,
            "decision_criteria": step.get('completion_criteria', {})
        }
        
        decision = await agent.make_decision(decision_input)
        
        return {
            "completed": True,
            "output": {
                "decision": decision,
                "reasoning": decision.get('reasoning', '')
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _execute_parallel_steps(
        self,
        context: WorkflowContext,
        step: Dict[str, Any],
        all_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Execute multiple steps in parallel"""
        parallel_step_ids = step.get('next_steps', [])
        parallel_steps = [
            self._find_step_by_id(all_steps, sid)
            for sid in parallel_step_ids
            if self._find_step_by_id(all_steps, sid)
        ]
        
        # Execute all parallel steps concurrently
        tasks = [
            self._execute_step(context, pstep, all_steps)
            for pstep in parallel_steps
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check for failures
        failures = [r for r in results if isinstance(r, Exception)]
        if failures:
            raise Exception(f"Parallel execution failed: {failures}")
        
        return {
            "completed": True,
            "output": {
                "parallel_results": [
                    context.step_results.get(sid, {})
                    for sid in parallel_step_ids
                ]
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _notify_human_agent(
        self,
        role: str,
        context: WorkflowContext,
        step: Dict[str, Any]
    ) -> None:
        """Notify human agent of required action"""
        # Create agent communication record
        notification = {
            "workflow_instance_id": context.workflow_instance_id,
            "from_role": "system",
            "to_role": role,
            "message_type": "notification",
            "subject": f"Action required: {step['name']}",
            "message": f"Please complete the following task: {step['description']}",
            "data": {
                "step_id": step['step_id'],
                "actions": step.get('actions', []),
                "deadline": step.get('timeout_minutes', 60)
            }
        }
        
        self.supabase.table('agent_communications').insert(notification).execute()
        
        # Trigger any registered notification handlers
        await self._trigger_event('human_action_required', {
            'role': role,
            'step': step,
            'context': context
        })
    
    async def send_agent_message(
        self,
        from_role: str,
        to_role: str,
        message_type: str,
        subject: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        workflow_instance_id: Optional[str] = None
    ) -> str:
        """Send a message between agents"""
        try:
            comm_data = {
                "from_role": from_role,
                "to_role": to_role,
                "message_type": message_type,
                "subject": subject,
                "message": message,
                "data": data or {},
                "status": "sent"
            }
            
            if workflow_instance_id:
                comm_data["workflow_instance_id"] = workflow_instance_id
            
            response = self.supabase.table('agent_communications').insert(comm_data).execute()
            comm_id = response.data[0]['id']
            
            # Notify receiving agent
            receiving_agent = self.agents.get(to_role)
            if receiving_agent:
                await receiving_agent.receive_message({
                    "id": comm_id,
                    "from": from_role,
                    "subject": subject,
                    "message": message,
                    "data": data
                })
            
            return comm_id
            
        except Exception as e:
            logger.error(f"Failed to send agent message: {str(e)}")
            raise
    
    def register_agent(self, role: str, agent: 'BaseAgent') -> None:
        """Register an agent for a specific role"""
        self.agents[role] = agent
        logger.info(f"Registered agent for role: {role}")
    
    def register_event_handler(self, event: str, handler: callable) -> None:
        """Register an event handler"""
        if event not in self.event_handlers:
            self.event_handlers[event] = []
        self.event_handlers[event].append(handler)
    
    async def _trigger_event(self, event: str, data: Dict[str, Any]) -> None:
        """Trigger event handlers"""
        handlers = self.event_handlers.get(event, [])
        for handler in handlers:
            try:
                await handler(data)
            except Exception as e:
                logger.error(f"Event handler error for {event}: {str(e)}")
    
    def _find_first_step(self, steps: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Find the first step in the workflow"""
        # First step is one that is not in any other step's next_steps
        all_next_steps = set()
        for step in steps:
            all_next_steps.update(step.get('next_steps', []))
        
        for step in steps:
            if step['step_id'] not in all_next_steps:
                return step
        
        # Default to first step if no clear entry point
        return steps[0] if steps else None
    
    def _find_step_by_id(
        self,
        steps: List[Dict[str, Any]],
        step_id: str
    ) -> Optional[Dict[str, Any]]:
        """Find a step by its ID"""
        for step in steps:
            if step['step_id'] == step_id:
                return step
        return None
    
    def _determine_next_steps(
        self,
        step: Dict[str, Any],
        result: Dict[str, Any]
    ) -> List[str]:
        """Determine next steps based on step result"""
        # Check conditions if any
        conditions = step.get('conditions', {})
        if conditions:
            # Evaluate conditions based on result
            for condition_name, next_step_id in conditions.items():
                if self._evaluate_condition(condition_name, result):
                    return [next_step_id]
        
        # Default to configured next steps
        return step.get('next_steps', [])
    
    def _evaluate_condition(
        self,
        condition: str,
        result: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition based on step result"""
        # Simple condition evaluation
        # In production, this would be more sophisticated
        if condition == "success":
            return result.get('completed', False)
        elif condition == "failure":
            return not result.get('completed', False)
        elif condition.startswith("decision:"):
            decision_value = condition.split(":", 1)[1]
            return result.get('output', {}).get('decision') == decision_value
        
        return False
    
    def _check_completion_criteria(
        self,
        criteria: Dict[str, Any],
        results: Dict[str, Any]
    ) -> bool:
        """Check if completion criteria are met"""
        if not criteria:
            return True
        
        for criterion, expected in criteria.items():
            if criterion == "all_actions_completed":
                if not all(r.get('completed', False) for r in results.values()):
                    return False
            elif criterion == "any_action_completed":
                if not any(r.get('completed', False) for r in results.values()):
                    return False
            # Add more criteria types as needed
        
        return True
    
    async def _complete_workflow(self, workflow_instance_id: str) -> None:
        """Mark workflow as completed"""
        self.supabase.table('workflow_instances').update({
            "status": WorkflowStatus.COMPLETED.value,
            "completed_at": datetime.utcnow().isoformat()
        }).eq('id', workflow_instance_id).execute()
        
        # Clean up active workflows
        if workflow_instance_id in self.active_workflows:
            del self.active_workflows[workflow_instance_id]
        
        logger.info(f"Workflow {workflow_instance_id} completed successfully")
        await self._trigger_event('workflow_completed', {'workflow_id': workflow_instance_id})
    
    async def _fail_workflow(self, workflow_instance_id: str, error: str) -> None:
        """Mark workflow as failed"""
        self.supabase.table('workflow_instances').update({
            "status": WorkflowStatus.FAILED.value,
            "completed_at": datetime.utcnow().isoformat(),
            "context": self.supabase.functions.jsonb_set(
                'context',
                '{error}',
                json.dumps(error)
            )
        }).eq('id', workflow_instance_id).execute()
        
        # Clean up active workflows
        if workflow_instance_id in self.active_workflows:
            del self.active_workflows[workflow_instance_id]
        
        logger.error(f"Workflow {workflow_instance_id} failed: {error}")
        await self._trigger_event('workflow_failed', {
            'workflow_id': workflow_instance_id,
            'error': error
        })


class BaseAgent:
    """Base class for role-based agents"""
    
    def __init__(self, role: str, orchestrator: SOPOrchestrationEngine):
        self.role = role
        self.orchestrator = orchestrator
        self.message_queue: List[Dict[str, Any]] = []
    
    async def execute_action(
        self,
        action: str,
        input_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a specific action"""
        raise NotImplementedError("Agents must implement execute_action")
    
    async def make_decision(
        self,
        decision_input: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Make a decision based on input"""
        raise NotImplementedError("Agents must implement make_decision")
    
    async def receive_message(self, message: Dict[str, Any]) -> None:
        """Receive a message from another agent"""
        self.message_queue.append(message)
        await self.process_message(message)
    
    async def process_message(self, message: Dict[str, Any]) -> None:
        """Process received message"""
        # Override in subclasses
        pass
    
    async def send_message(
        self,
        to_role: str,
        subject: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
        message_type: str = "request"
    ) -> str:
        """Send a message to another agent"""
        return await self.orchestrator.send_agent_message(
            from_role=self.role,
            to_role=to_role,
            message_type=message_type,
            subject=subject,
            message=message,
            data=data
        )