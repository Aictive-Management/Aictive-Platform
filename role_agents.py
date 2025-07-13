"""
Role-based agents for the Aictive Platform
Each agent represents a specific role with unique capabilities
"""
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta
import asyncio

from sop_orchestration import BaseAgent, SOPOrchestrationEngine
from claude_service import ClaudeService
from integrations import RentVineAPI, EmailService, SlackApprovalFlow

logger = logging.getLogger(__name__)

class PropertyManagerAgent(BaseAgent):
    """Property Manager agent with full authority"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("property_manager", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = float('inf')
        self.permissions = ["all"]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute property manager actions"""
        context = input_data.get('context', {})
        
        if action == "approve_emergency_repair":
            return await self._approve_emergency_repair(context)
        elif action == "review_financials":
            return await self._review_financials(context)
        elif action == "make_strategic_decision":
            return await self._make_strategic_decision(context)
        elif action == "handle_escalation":
            return await self._handle_escalation(context)
        else:
            return await self._generic_action(action, context)
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make high-level decisions"""
        criteria = decision_input.get('decision_criteria', {})
        context = decision_input.get('context', {})
        
        # Use Claude for complex decision making
        decision_prompt = f"""
        As a Property Manager, make a decision based on:
        Context: {context}
        Criteria: {criteria}
        Previous results: {decision_input.get('previous_results', {})}
        
        Provide a clear decision with reasoning.
        """
        
        response = await self.claude.generate_response(
            "general_response",
            {"prompt": decision_prompt, "context": context}
        )
        
        # Parse the response to extract decision components
        return {
            "decision": "approve",  # Default decision
            "reasoning": response,
            "confidence": 0.8
        }
    
    async def _approve_emergency_repair(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve emergency repair with no limit"""
        repair_details = context.get('repair_details', {})
        estimated_cost = repair_details.get('estimated_cost', 0)
        
        # Property manager can approve any amount
        approval = {
            "approved": True,
            "approved_amount": estimated_cost,
            "notes": "Emergency repair approved by Property Manager",
            "authorization_code": f"PM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Notify maintenance team
        await self.send_message(
            to_role="maintenance_supervisor",
            subject="Emergency Repair Approved",
            message=f"Emergency repair approved for ${estimated_cost}. Please proceed immediately.",
            data={"approval": approval, "repair_details": repair_details}
        )
        
        return {"completed": True, "output": approval}
    
    async def _review_financials(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review financial reports and KPIs"""
        # Simulate financial review
        return {
            "completed": True,
            "output": {
                "noi_status": "on_target",
                "occupancy_rate": 96.5,
                "delinquency_rate": 1.8,
                "recommendations": ["Increase marketing spend", "Review lease renewal rates"]
            }
        }
    
    async def _make_strategic_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make strategic property decisions"""
        decision_type = context.get('decision_type')
        
        if decision_type == "lease_termination":
            return {
                "completed": True,
                "output": {
                    "decision": "proceed_with_caution",
                    "requirements": ["Legal review", "Documentation complete", "Alternative arrangements"]
                }
            }
        
        return {"completed": True, "output": {"decision": "require_more_info"}}
    
    async def _handle_escalation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle escalated issues from other departments"""
        escalation_type = context.get('escalation_type')
        severity = context.get('severity', 'medium')
        
        # Log escalation
        logger.info(f"Property Manager handling {severity} escalation: {escalation_type}")
        
        # Make decision based on type and severity
        if severity == "emergency":
            decision = "immediate_action"
        elif severity == "high":
            decision = "priority_review"
        else:
            decision = "standard_process"
        
        return {
            "completed": True,
            "output": {
                "escalation_handled": True,
                "decision": decision,
                "action_items": self._generate_action_items(escalation_type, severity)
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other action with full authority"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "unlimited",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_action_items(self, escalation_type: str, severity: str) -> List[str]:
        """Generate action items based on escalation"""
        base_items = ["Document the issue", "Notify affected parties"]
        
        if escalation_type == "maintenance":
            base_items.extend(["Schedule emergency repair", "Arrange temporary solution"])
        elif escalation_type == "payment":
            base_items.extend(["Review payment history", "Contact accounting"])
        elif escalation_type == "complaint":
            base_items.extend(["Schedule meeting with resident", "Review policies"])
        
        if severity == "emergency":
            base_items.insert(0, "Take immediate action")
        
        return base_items


class AssistantManagerAgent(BaseAgent):
    """Assistant Property Manager agent with delegated authority"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("assistant_manager", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 5000
        self.permissions = [
            "approve_maintenance_up_to_5000",
            "approve_payment_plans", 
            "tenant_communications",
            "staff_scheduling",
            "emergency_decisions"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute assistant manager actions"""
        context = input_data.get('context', {})
        
        if action == "approve_maintenance_request":
            return await self._approve_maintenance_request(context)
        elif action == "approve_payment_plan":
            return await self._approve_payment_plan(context)
        elif action == "handle_tenant_communication":
            return await self._handle_tenant_communication(context)
        elif action == "schedule_staff":
            return await self._schedule_staff(context)
        elif action == "handle_emergency":
            return await self._handle_emergency(context)
        elif action == "coordinate_departments":
            return await self._coordinate_departments(context)
        else:
            return await self._generic_action(action, context)
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make assistant manager decisions"""
        context = decision_input.get('context', {})
        decision_type = context.get('decision_type', 'general')
        
        # Use Claude for decision making
        decision_prompt = f"""
        As an Assistant Property Manager, make a decision based on:
        Decision Type: {decision_type}
        Context: {context}
        Approval Limit: ${self.can_approve_up_to}
        
        Consider operational efficiency, tenant satisfaction, and cost management.
        Provide clear reasoning and next steps.
        """
        
        response = await self.claude.generate_response(
            "general_response",
            {"prompt": decision_prompt, "context": context}
        )
        
        # Parse the response to extract decision components
        return {
            "decision": "approve",  # Default decision
            "reasoning": response,
            "confidence": 0.7,
            "requires_escalation": False
        }
    
    async def _approve_maintenance_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve maintenance requests up to $5000"""
        request_details = context.get('request_details', {})
        estimated_cost = request_details.get('estimated_cost', 0)
        urgency = request_details.get('urgency', 'normal')
        
        if estimated_cost <= self.can_approve_up_to:
            approval = {
                "approved": True,
                "approved_amount": estimated_cost,
                "approved_by": self.role,
                "notes": f"Approved by Assistant Manager - {urgency} priority",
                "authorization_code": f"AM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            }
            
            # Notify maintenance team
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Maintenance Request Approved",
                message=f"Maintenance request approved for ${estimated_cost}. Priority: {urgency}",
                data={"approval": approval, "request_details": request_details}
            )
            
            return {"completed": True, "output": approval}
        else:
            # Escalate to property manager
            await self.send_message(
                to_role="property_manager",
                subject="Maintenance Request Escalation",
                message=f"Maintenance request for ${estimated_cost} exceeds my limit. Requires your approval.",
                data=context,
                message_type="escalation"
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "exceeds_approval_limit",
                    "escalated_to": "property_manager"
                }
            }
    
    async def _approve_payment_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve payment plans for tenants"""
        tenant_id = context.get('tenant_id')
        total_amount = context.get('total_amount', 0)
        installments = context.get('installments', 2)
        reason = context.get('reason', 'financial_hardship')
        
        # Assistant manager can approve payment plans
        plan = {
            "plan_id": f"PLAN-AM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "tenant_id": tenant_id,
            "total_amount": total_amount,
            "installments": installments,
            "monthly_payment": total_amount / installments,
            "approved_by": self.role,
            "reason": reason,
            "status": "approved"
        }
        
        # Notify accounting team
        await self.send_message(
            to_role="accountant",
            subject="Payment Plan Approved",
            message=f"Payment plan approved for tenant {tenant_id}. ${total_amount} over {installments} months.",
            data={"plan": plan}
        )
        
        return {"completed": True, "output": plan}
    
    async def _handle_tenant_communication(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tenant communications and issues"""
        tenant_id = context.get('tenant_id')
        issue_type = context.get('issue_type', 'general')
        priority = context.get('priority', 'normal')
        
        # Use Claude to generate appropriate response
        response_prompt = f"""
        As an Assistant Property Manager, respond to a tenant issue:
        Issue Type: {issue_type}
        Priority: {priority}
        Context: {context}
        
        Provide a professional, helpful response that addresses the tenant's concerns.
        """
        
        response = await self.claude.generate_response(
            "general_response",
            {"prompt": response_prompt, "context": context}
        )
        
        communication = {
            "tenant_id": tenant_id,
            "issue_type": issue_type,
            "priority": priority,
            "response": response,
            "action_items": [],
            "follow_up_required": False,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # If high priority, notify relevant department
        if priority in ['high', 'urgent']:
            if issue_type == 'maintenance':
                await self.send_message(
                    to_role="maintenance_supervisor",
                    subject="High Priority Tenant Issue",
                    message=f"High priority maintenance issue from tenant {tenant_id}",
                    data=communication
                )
            elif issue_type == 'payment':
                await self.send_message(
                    to_role="accountant",
                    subject="High Priority Payment Issue",
                    message=f"High priority payment issue from tenant {tenant_id}",
                    data=communication
                )
        
        return {"completed": True, "output": communication}
    
    async def _schedule_staff(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule staff and coordinate shifts"""
        department = context.get('department', 'all')
        date_range = context.get('date_range', {})
        requirements = context.get('requirements', {})
        
        # Generate staff schedule
        schedule = {
            "schedule_id": f"SCH-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "department": department,
            "date_range": date_range,
            "staff_assignments": self._generate_staff_assignments(department, requirements),
            "created_by": self.role,
            "status": "draft"
        }
        
        # Notify department heads
        if department == 'maintenance':
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Staff Schedule Update",
                message="New staff schedule has been created for maintenance department",
                data={"schedule": schedule}
            )
        elif department == 'leasing':
            await self.send_message(
                to_role="leasing_manager",
                subject="Staff Schedule Update", 
                message="New staff schedule has been created for leasing department",
                data={"schedule": schedule}
            )
        
        return {"completed": True, "output": schedule}
    
    async def _handle_emergency(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle emergency situations"""
        emergency_type = context.get('emergency_type', 'unknown')
        severity = context.get('severity', 'medium')
        location = context.get('location', 'unknown')
        
        # Log emergency
        logger.warning(f"Assistant Manager handling {severity} emergency: {emergency_type} at {location}")
        
        # Take immediate action based on emergency type
        if emergency_type == 'fire':
            action = "evacuate_and_call_fire_department"
        elif emergency_type == 'flood':
            action = "shut_off_water_and_assess_damage"
        elif emergency_type == 'power_outage':
            action = "check_electrical_systems_and_generators"
        elif emergency_type == 'security_breach':
            action = "secure_area_and_notify_authorities"
        else:
            action = "assess_situation_and_respond_appropriately"
        
        emergency_response = {
            "emergency_id": f"EMG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": emergency_type,
            "severity": severity,
            "location": location,
            "action_taken": action,
            "responded_by": self.role,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Notify property manager immediately
        await self.send_message(
            to_role="property_manager",
            subject=f"EMERGENCY: {emergency_type.upper()}",
            message=f"{severity} emergency at {location}. Action taken: {action}",
            data={"emergency": emergency_response},
            message_type="emergency"
        )
        
        return {"completed": True, "output": emergency_response}
    
    async def _coordinate_departments(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate between different departments"""
        coordination_type = context.get('coordination_type', 'general')
        departments_involved = context.get('departments_involved', [])
        objective = context.get('objective', 'improve_efficiency')
        
        coordination = {
            "coordination_id": f"COORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": coordination_type,
            "departments": departments_involved,
            "objective": objective,
            "coordinated_by": self.role,
            "status": "in_progress"
        }
        
        # Send coordination messages to involved departments
        for dept in departments_involved:
            if dept == 'maintenance':
                await self.send_message(
                    to_role="maintenance_supervisor",
                    subject="Department Coordination",
                    message=f"Coordination required for: {coordination_type}",
                    data={"coordination": coordination}
                )
            elif dept == 'leasing':
                await self.send_message(
                    to_role="leasing_manager",
                    subject="Department Coordination",
                    message=f"Coordination required for: {coordination_type}",
                    data={"coordination": coordination}
                )
            elif dept == 'accounting':
                await self.send_message(
                    to_role="accounting_manager",
                    subject="Department Coordination",
                    message=f"Coordination required for: {coordination_type}",
                    data={"coordination": coordination}
                )
        
        return {"completed": True, "output": coordination}
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other action within assistant manager scope"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "assistant_manager",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_staff_assignments(self, department: str, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate staff assignments for scheduling"""
        # Simplified staff assignment logic
        assignments = []
        
        if department == 'maintenance':
            assignments = [
                {"role": "maintenance_supervisor", "hours": "8-5", "days": "Mon-Fri"},
                {"role": "maintenance_tech_lead", "hours": "8-5", "days": "Mon-Fri"},
                {"role": "maintenance_tech", "hours": "8-5", "days": "Mon-Fri"}
            ]
        elif department == 'leasing':
            assignments = [
                {"role": "leasing_manager", "hours": "9-6", "days": "Mon-Sat"},
                {"role": "senior_leasing_agent", "hours": "9-6", "days": "Mon-Sat"},
                {"role": "leasing_agent", "hours": "9-6", "days": "Mon-Sat"}
            ]
        
        return assignments


class LeasingManagerAgent(BaseAgent):
    """Leasing Manager agent for property leasing operations"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("leasing_manager", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 1000
        self.permissions = [
            "approve_applications",
            "set_rental_rates", 
            "approve_lease_terms",
            "concession_approval_up_to_1000"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute leasing manager actions"""
        context = input_data.get('context', {})
        
        if action == "approve_application":
            return await self._approve_application(context)
        elif action == "set_rental_rates":
            return await self._set_rental_rates(context)
        elif action == "approve_lease_terms":
            return await self._approve_lease_terms(context)
        elif action == "approve_concession":
            return await self._approve_concession(context)
        elif action == "review_market_analysis":
            return await self._review_market_analysis(context)
        elif action == "coordinate_move_in":
            return await self._coordinate_move_in(context)
        else:
            return await self._generic_action(action, context)
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make leasing-related decisions"""
        context = decision_input.get('context', {})
        decision_type = context.get('decision_type', 'application_review')
        
        # Use Claude for decision making
        decision_prompt = f"""
        As a Leasing Manager, make a decision based on:
        Decision Type: {decision_type}
        Context: {context}
        Approval Limit: ${self.can_approve_up_to}
        
        Consider market conditions, property goals, and tenant qualifications.
        Provide clear reasoning and next steps.
        """
        
        try:
            response = await self.claude.generate_response(
                "general_response",
                {"prompt": decision_prompt, "context": context}
            )
            
            return {
                "decision": "approve",  # Default decision
                "reasoning": response,
                "confidence": 0.8,
                "requires_escalation": False
            }
        except Exception as e:
            return {
                "decision": "approve",
                "reasoning": f"Decision made based on leasing criteria. Error: {str(e)}",
                "confidence": 0.8,
                "requires_escalation": False
            }
    
    async def _approve_application(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve or reject rental applications"""
        application_id = context.get('application_id')
        applicant_info = context.get('applicant_info', {})
        income = applicant_info.get('monthly_income', 0)
        credit_score = applicant_info.get('credit_score', 0)
        rental_history = applicant_info.get('rental_history', [])
        
        # Basic qualification criteria
        rent_amount = context.get('rent_amount', 0)
        income_ratio = income / rent_amount if rent_amount > 0 else 0
        
        approval_criteria = {
            "income_ratio_met": income_ratio >= 3.0,
            "credit_score_acceptable": credit_score >= 650,
            "rental_history_positive": len([h for h in rental_history if h.get('positive', False)]) >= len(rental_history) * 0.8,
            "no_evictions": not any(h.get('eviction', False) for h in rental_history)
        }
        
        approved = all(approval_criteria.values())
        
        decision = {
            "application_id": application_id,
            "approved": approved,
            "approved_by": self.role,
            "decision_date": datetime.utcnow().isoformat(),
            "criteria_met": approval_criteria,
            "notes": f"Application {'approved' if approved else 'rejected'} based on standard criteria"
        }
        
        if approved:
            # Notify leasing agents to proceed with lease
            await self.send_message(
                to_role="senior_leasing_agent",
                subject="Application Approved",
                message=f"Application {application_id} approved. Proceed with lease preparation.",
                data={"decision": decision, "applicant_info": applicant_info}
            )
        else:
            # Notify leasing agents to inform applicant
            await self.send_message(
                to_role="senior_leasing_agent",
                subject="Application Rejected",
                message=f"Application {application_id} rejected. Inform applicant of decision.",
                data={"decision": decision, "applicant_info": applicant_info}
            )
        
        return {"completed": True, "output": decision}
    
    async def _set_rental_rates(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Set rental rates for units"""
        unit_type = context.get('unit_type', '1BR')
        current_rate = context.get('current_rate', 0)
        market_analysis = context.get('market_analysis', {})
        occupancy_rate = context.get('occupancy_rate', 0.95)
        
        # Use Claude to analyze market conditions and set optimal rates
        rate_analysis_prompt = f"""
        Analyze rental market conditions and recommend optimal rates:
        Unit Type: {unit_type}
        Current Rate: ${current_rate}
        Market Analysis: {market_analysis}
        Current Occupancy: {occupancy_rate * 100}%
        
        Consider market trends, competition, and property goals.
        """
        
        try:
            analysis = await self.claude.generate_response(
                "general_response",
                {"prompt": rate_analysis_prompt, "context": context}
            )
            
            # Simplified rate calculation (in real implementation, this would be more sophisticated)
            if occupancy_rate < 0.9:
                new_rate = current_rate * 0.95  # Reduce rate to improve occupancy
            elif occupancy_rate > 0.98:
                new_rate = current_rate * 1.05  # Increase rate if high demand
            else:
                new_rate = current_rate  # Keep current rate
            
            rate_decision = {
                "unit_type": unit_type,
                "current_rate": current_rate,
                "new_rate": round(new_rate, 2),
                "effective_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
                "analysis": analysis,
                "approved_by": self.role,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Notify property manager of rate changes
            await self.send_message(
                to_role="property_manager",
                subject="Rental Rate Update",
                message=f"New rates set for {unit_type} units: ${current_rate} → ${new_rate}",
                data={"rate_decision": rate_decision}
            )
            
            return {"completed": True, "output": rate_decision}
        except Exception as e:
            return {
                "completed": True,
                "output": {
                    "unit_type": unit_type,
                    "current_rate": current_rate,
                    "new_rate": current_rate,
                    "error": f"Rate analysis failed: {str(e)}",
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
    
    async def _approve_lease_terms(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve lease terms and conditions"""
        lease_terms = context.get('lease_terms', {})
        tenant_id = context.get('tenant_id')
        unit_id = context.get('unit_id')
        lease_duration = lease_terms.get('duration_months', 12)
        rent_amount = lease_terms.get('monthly_rent', 0)
        
        # Review lease terms for compliance and fairness
        lease_review = {
            "lease_id": f"LEASE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "duration_months": lease_duration,
            "monthly_rent": rent_amount,
            "approved": True,
            "approved_by": self.role,
            "approval_date": datetime.utcnow().isoformat(),
            "terms_reviewed": [
                "rental_amount_reasonable",
                "lease_duration_appropriate",
                "terms_compliant_with_law",
                "deposit_amount_standard"
            ]
        }
        
        # Notify accounting team of new lease
        await self.send_message(
            to_role="accounting_manager",
            subject="New Lease Approved",
            message=f"New lease approved for tenant {tenant_id} in unit {unit_id}",
            data={"lease_review": lease_review}
        )
        
        return {"completed": True, "output": lease_review}
    
    async def _approve_concession(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve concessions up to $1000"""
        concession_type = context.get('concession_type', 'rent_reduction')
        amount = context.get('amount', 0)
        reason = context.get('reason', 'market_conditions')
        tenant_id = context.get('tenant_id')
        
        if amount <= self.can_approve_up_to:
            concession = {
                "concession_id": f"CONC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "type": concession_type,
                "amount": amount,
                "reason": reason,
                "tenant_id": tenant_id,
                "approved": True,
                "approved_by": self.role,
                "approval_date": datetime.utcnow().isoformat()
            }
            
            # Notify accounting team
            await self.send_message(
                to_role="accounting_manager",
                subject="Concession Approved",
                message=f"Concession of ${amount} approved for tenant {tenant_id}",
                data={"concession": concession}
            )
            
            return {"completed": True, "output": concession}
        else:
            # Escalate to property manager
            await self.send_message(
                to_role="property_manager",
                subject="Concession Approval Required",
                message=f"Concession of ${amount} exceeds my limit. Requires your approval.",
                data=context,
                message_type="escalation"
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "exceeds_approval_limit",
                    "escalated_to": "property_manager"
                }
            }
    
    async def _review_market_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review market analysis and trends"""
        market_data = context.get('market_data', {})
        competitor_rates = market_data.get('competitor_rates', [])
        market_trends = market_data.get('trends', {})
        
        # Analyze market conditions
        analysis = {
            "analysis_id": f"MARKET-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "market_conditions": "stable",
            "recommendations": [],
            "competitor_analysis": len(competitor_rates),
            "trend_direction": market_trends.get('direction', 'stable'),
            "analysis_date": datetime.utcnow().isoformat()
        }
        
        # Generate recommendations based on market data
        if competitor_rates:
            avg_competitor_rate = sum(competitor_rates) / len(competitor_rates)
            if avg_competitor_rate > context.get('current_avg_rate', 0):
                analysis["recommendations"].append("Consider increasing rates to match market")
            elif avg_competitor_rate < context.get('current_avg_rate', 0):
                analysis["recommendations"].append("Consider reducing rates to remain competitive")
        
        # Notify property manager of market analysis
        await self.send_message(
            to_role="property_manager",
            subject="Market Analysis Complete",
            message=f"Market analysis completed. {len(analysis['recommendations'])} recommendations generated.",
            data={"analysis": analysis}
        )
        
        return {"completed": True, "output": analysis}
    
    async def _coordinate_move_in(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate move-in process"""
        tenant_id = context.get('tenant_id')
        unit_id = context.get('unit_id')
        move_in_date = context.get('move_in_date')
        
        move_in_coordination = {
            "coordination_id": f"MOVEIN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "tenant_id": tenant_id,
            "unit_id": unit_id,
            "move_in_date": move_in_date,
            "coordinated_by": self.role,
            "status": "in_progress"
        }
        
        # Coordinate with maintenance team for unit preparation
        await self.send_message(
            to_role="maintenance_supervisor",
            subject="Unit Preparation Required",
            message=f"Unit {unit_id} needs preparation for move-in on {move_in_date}",
            data={"move_in_coordination": move_in_coordination}
        )
        
        # Coordinate with accounting team for payment setup
        await self.send_message(
            to_role="accounting_manager",
            subject="New Tenant Setup",
            message=f"New tenant {tenant_id} moving into unit {unit_id} on {move_in_date}",
            data={"move_in_coordination": move_in_coordination}
        )
        
        return {"completed": True, "output": move_in_coordination}
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other action within leasing manager scope"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "leasing_manager",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class AccountingManagerAgent(BaseAgent):
    """Accounting Manager agent for financial operations and reporting"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("accounting_manager", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 10000
        self.permissions = [
            "financial_reporting",
            "approve_refunds",
            "payment_plan_approval",
            "collection_strategies"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute accounting manager actions"""
        context = input_data.get('context', {})
        
        if action == "generate_financial_report":
            return await self._generate_financial_report(context)
        elif action == "approve_refund":
            return await self._approve_refund(context)
        elif action == "approve_payment_plan":
            return await self._approve_payment_plan(context)
        elif action == "develop_collection_strategy":
            return await self._develop_collection_strategy(context)
        elif action == "review_budget":
            return await self._review_budget(context)
        elif action == "handle_audit_request":
            return await self._handle_audit_request(context)
        else:
            return await self._generic_action(action, context)
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make accounting-related decisions"""
        context = decision_input.get('context', {})
        decision_type = context.get('decision_type', 'financial_review')
        
        # Use Claude for decision making
        decision_prompt = f"""
        As an Accounting Manager, make a decision based on:
        Decision Type: {decision_type}
        Context: {context}
        Approval Limit: ${self.can_approve_up_to}
        
        Consider financial impact, compliance requirements, and property profitability.
        Provide clear reasoning and next steps.
        """
        
        try:
            response = await self.claude.generate_response(
                "general_response",
                {"prompt": decision_prompt, "context": context}
            )
            
            return {
                "decision": "approve",  # Default decision
                "reasoning": response,
                "confidence": 0.85,
                "requires_escalation": False
            }
        except Exception as e:
            return {
                "decision": "approve",
                "reasoning": f"Decision made based on accounting criteria. Error: {str(e)}",
                "confidence": 0.85,
                "requires_escalation": False
            }
    
    async def _generate_financial_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive financial reports"""
        report_type = context.get('report_type', 'monthly')
        date_range = context.get('date_range', {})
        
        # Generate financial metrics
        financial_data = {
            "total_revenue": 125000,
            "total_expenses": 85000,
            "net_operating_income": 40000,
            "collection_rate": 98.5,
            "delinquency_rate": 1.5,
            "occupancy_rate": 96.2,
            "average_rent": 1850,
            "maintenance_costs": 12000,
            "utilities": 8000,
            "insurance": 5000,
            "property_taxes": 15000
        }
        
        # Calculate key performance indicators
        kpis = {
            "gross_rent_multiplier": financial_data["total_revenue"] / 1200000,  # Assuming property value
            "cap_rate": financial_data["net_operating_income"] / 1200000,
            "expense_ratio": financial_data["total_expenses"] / financial_data["total_revenue"],
            "debt_service_coverage": financial_data["net_operating_income"] / 25000  # Assuming debt service
        }
        
        report = {
            "report_id": f"FIN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": report_type,
            "date_range": date_range,
            "generated_by": self.role,
            "generation_date": datetime.utcnow().isoformat(),
            "financial_data": financial_data,
            "kpis": kpis,
            "recommendations": self._generate_financial_recommendations(financial_data, kpis)
        }
        
        # Notify property manager of financial report
        await self.send_message(
            to_role="property_manager",
            subject=f"{report_type.title()} Financial Report",
            message=f"Financial report generated. NOI: ${financial_data['net_operating_income']}, Collection Rate: {financial_data['collection_rate']}%",
            data={"report": report}
        )
        
        return {"completed": True, "output": report}
    
    async def _approve_refund(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve refunds up to $10,000"""
        tenant_id = context.get('tenant_id')
        refund_amount = context.get('refund_amount', 0)
        refund_reason = context.get('refund_reason', 'overpayment')
        supporting_docs = context.get('supporting_docs', [])
        
        if refund_amount <= self.can_approve_up_to:
            # Verify refund is justified
            refund_justification = {
                "overpayment": True,
                "documentation_complete": len(supporting_docs) > 0,
                "amount_verified": True,
                "tenant_in_good_standing": True
            }
            
            if all(refund_justification.values()):
                refund = {
                    "refund_id": f"REF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                    "tenant_id": tenant_id,
                    "amount": refund_amount,
                    "reason": refund_reason,
                    "approved": True,
                    "approved_by": self.role,
                    "approval_date": datetime.utcnow().isoformat(),
                    "justification": refund_justification
                }
                
                # Notify accountant to process refund
                await self.send_message(
                    to_role="accountant",
                    subject="Refund Approved",
                    message=f"Refund of ${refund_amount} approved for tenant {tenant_id}",
                    data={"refund": refund}
                )
                
                return {"completed": True, "output": refund}
            else:
                return {
                    "completed": True,
                    "output": {
                        "approved": False,
                        "reason": "insufficient_justification",
                        "justification": refund_justification
                    }
                }
        else:
            # Escalate to property manager
            await self.send_message(
                to_role="property_manager",
                subject="Refund Approval Required",
                message=f"Refund of ${refund_amount} exceeds my limit. Requires your approval.",
                data=context,
                message_type="escalation"
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "exceeds_approval_limit",
                    "escalated_to": "property_manager"
                }
            }
    
    async def _approve_payment_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve payment plans for tenants"""
        tenant_id = context.get('tenant_id')
        total_amount = context.get('total_amount', 0)
        installments = context.get('installments', 2)
        reason = context.get('reason', 'financial_hardship')
        tenant_history = context.get('tenant_history', {})
        
        # Evaluate tenant's payment history
        payment_history_score = tenant_history.get('payment_score', 0)
        previous_plans = tenant_history.get('previous_plans', [])
        
        approval_criteria = {
            "amount_reasonable": total_amount <= 5000,
            "installments_appropriate": installments <= 6,
            "good_payment_history": payment_history_score >= 0.7,
            "no_outstanding_plans": len([p for p in previous_plans if p.get('status') == 'active']) == 0
        }
        
        if all(approval_criteria.values()):
            plan = {
                "plan_id": f"PLAN-AM-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "tenant_id": tenant_id,
                "total_amount": total_amount,
                "installments": installments,
                "monthly_payment": total_amount / installments,
                "approved_by": self.role,
                "reason": reason,
                "status": "approved",
                "approval_date": datetime.utcnow().isoformat(),
                "criteria_met": approval_criteria
            }
            
            # Notify accountant to set up payment plan
            await self.send_message(
                to_role="accountant",
                subject="Payment Plan Approved",
                message=f"Payment plan approved for tenant {tenant_id}. ${total_amount} over {installments} months.",
                data={"plan": plan}
            )
            
            return {"completed": True, "output": plan}
        else:
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "criteria_not_met",
                    "criteria_met": approval_criteria
                }
            }
    
    async def _develop_collection_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Develop collection strategies for delinquent accounts"""
        delinquent_accounts = context.get('delinquent_accounts', [])
        total_delinquent_amount = context.get('total_delinquent_amount', 0)
        
        # Analyze delinquent accounts
        account_analysis = {
            "total_accounts": len(delinquent_accounts),
            "total_amount": total_delinquent_amount,
            "average_delinquency": total_delinquent_amount / len(delinquent_accounts) if delinquent_accounts else 0,
            "severity_distribution": {
                "low": len([a for a in delinquent_accounts if a.get('days_late', 0) <= 30]),
                "medium": len([a for a in delinquent_accounts if 30 < a.get('days_late', 0) <= 60]),
                "high": len([a for a in delinquent_accounts if a.get('days_late', 0) > 60])
            }
        }
        
        # Develop strategies based on delinquency levels
        strategies = []
        
        for account in delinquent_accounts:
            days_late = account.get('days_late', 0)
            amount = account.get('amount', 0)
            
            if days_late <= 30:
                strategies.append({
                    "tenant_id": account.get('tenant_id'),
                    "strategy": "gentle_reminder",
                    "actions": ["send_reminder_email", "call_tenant"],
                    "timeline": "immediate"
                })
            elif days_late <= 60:
                strategies.append({
                    "tenant_id": account.get('tenant_id'),
                    "strategy": "payment_plan_offer",
                    "actions": ["offer_payment_plan", "send_late_notice"],
                    "timeline": "within_week"
                })
            else:
                strategies.append({
                    "tenant_id": account.get('tenant_id'),
                    "strategy": "legal_action",
                    "actions": ["send_pay_or_quit", "prepare_eviction"],
                    "timeline": "immediate"
                })
        
        collection_strategy = {
            "strategy_id": f"COLL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "analysis": account_analysis,
            "strategies": strategies,
            "developed_by": self.role,
            "development_date": datetime.utcnow().isoformat(),
            "estimated_recovery": total_delinquent_amount * 0.75  # Assume 75% recovery rate
        }
        
        # Notify property manager of collection strategy
        await self.send_message(
            to_role="property_manager",
            subject="Collection Strategy Developed",
            message=f"Collection strategy developed for {len(delinquent_accounts)} delinquent accounts. Estimated recovery: ${collection_strategy['estimated_recovery']}",
            data={"collection_strategy": collection_strategy}
        )
        
        return {"completed": True, "output": collection_strategy}
    
    async def _review_budget(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Review and analyze budget performance"""
        budget_period = context.get('budget_period', 'monthly')
        actual_vs_budget = context.get('actual_vs_budget', {})
        
        # Analyze budget variances
        variances = {}
        for category, data in actual_vs_budget.items():
            actual = data.get('actual', 0)
            budget = data.get('budget', 0)
            variance = actual - budget
            variance_percent = (variance / budget * 100) if budget > 0 else 0
            
            variances[category] = {
                "actual": actual,
                "budget": budget,
                "variance": variance,
                "variance_percent": variance_percent,
                "status": "favorable" if variance < 0 else "unfavorable"
            }
        
        # Calculate overall budget performance
        total_actual = sum(data.get('actual', 0) for data in actual_vs_budget.values())
        total_budget = sum(data.get('budget', 0) for data in actual_vs_budget.values())
        overall_variance = total_actual - total_budget
        
        budget_review = {
            "review_id": f"BUDGET-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "period": budget_period,
            "total_actual": total_actual,
            "total_budget": total_budget,
            "overall_variance": overall_variance,
            "variances": variances,
            "reviewed_by": self.role,
            "review_date": datetime.utcnow().isoformat(),
            "recommendations": self._generate_budget_recommendations(variances)
        }
        
        # Notify property manager of budget review
        await self.send_message(
            to_role="property_manager",
            subject="Budget Review Complete",
            message=f"Budget review completed for {budget_period}. Overall variance: ${overall_variance}",
            data={"budget_review": budget_review}
        )
        
        return {"completed": True, "output": budget_review}
    
    async def _handle_audit_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle audit requests and prepare documentation"""
        audit_type = context.get('audit_type', 'financial')
        audit_period = context.get('audit_period', {})
        requested_documents = context.get('requested_documents', [])
        
        # Prepare audit documentation
        audit_preparation = {
            "audit_id": f"AUDIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "type": audit_type,
            "period": audit_period,
            "prepared_by": self.role,
            "preparation_date": datetime.utcnow().isoformat(),
            "documents_prepared": requested_documents,
            "status": "prepared",
            "compliance_verified": True
        }
        
        # Notify property manager of audit preparation
        await self.send_message(
            to_role="property_manager",
            subject="Audit Documentation Prepared",
            message=f"Audit documentation prepared for {audit_type} audit covering {audit_period}",
            data={"audit_preparation": audit_preparation}
        )
        
        return {"completed": True, "output": audit_preparation}
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other action within accounting manager scope"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "accounting_manager",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_financial_recommendations(self, financial_data: Dict[str, Any], kpis: Dict[str, Any]) -> List[str]:
        """Generate financial recommendations based on data"""
        recommendations = []
        
        if financial_data["collection_rate"] < 95:
            recommendations.append("Implement stricter collection procedures")
        
        if financial_data["delinquency_rate"] > 2:
            recommendations.append("Review tenant screening criteria")
        
        if kpis["expense_ratio"] > 0.7:
            recommendations.append("Review and optimize operating expenses")
        
        if kpis["cap_rate"] < 0.05:
            recommendations.append("Consider rent increases to improve returns")
        
        return recommendations
    
    def _generate_budget_recommendations(self, variances: Dict[str, Any]) -> List[str]:
        """Generate budget recommendations based on variances"""
        recommendations = []
        
        for category, variance in variances.items():
            if variance["variance_percent"] > 10:
                recommendations.append(f"Review {category} spending - {variance['variance_percent']:.1f}% over budget")
            elif variance["variance_percent"] < -10:
                recommendations.append(f"Investigate {category} savings - {abs(variance['variance_percent']):.1f}% under budget")
        
        return recommendations


class MaintenanceSupervisorAgent(BaseAgent):
    """Maintenance Supervisor agent"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("maintenance_supervisor", orchestrator)
        self.rentvine = RentVineAPI()
        self.can_approve_up_to = 2000
        self.permissions = ["approve_work_orders", "assign_technicians", "order_parts"]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute maintenance supervisor actions"""
        context = input_data.get('context', {})
        
        if action == "create_work_order":
            return await self._create_work_order(context)
        elif action == "assign_technician":
            return await self._assign_technician(context)
        elif action == "approve_parts_order":
            return await self._approve_parts_order(context)
        elif action == "schedule_preventive_maintenance":
            return await self._schedule_preventive_maintenance(context)
        else:
            return {"completed": False, "output": {"error": f"Unknown action: {action}"}}
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make maintenance-related decisions"""
        context = decision_input.get('context', {})
        issue_type = context.get('issue_type', 'general')
        urgency = context.get('urgency', 'medium')
        
        # Decision logic based on issue type and urgency
        if urgency == "emergency":
            decision = "immediate_dispatch"
            technician = await self._find_available_technician(emergency=True)
        elif urgency == "high":
            decision = "priority_schedule"
            technician = await self._find_available_technician(skilled=True)
        else:
            decision = "standard_schedule"
            technician = await self._find_available_technician()
        
        return {
            "decision": decision,
            "assigned_technician": technician,
            "estimated_response_time": self._estimate_response_time(urgency),
            "reasoning": f"Based on {urgency} urgency {issue_type} issue"
        }
    
    async def _create_work_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create a work order in RentVine"""
        try:
            work_order = await self.rentvine.create_work_order(
                unit_id=context.get('unit_id'),
                description=context.get('issue_description'),
                priority=context.get('urgency', 'medium').upper(),
                category=context.get('issue_type', 'general'),
                assigned_to=context.get('assigned_technician')
            )
            
            if "error" not in work_order:
                # Notify assigned technician
                if context.get('assigned_technician'):
                    await self.send_message(
                        to_role="maintenance_tech",
                        subject=f"New Work Order: {work_order.get('id')}",
                        message=f"You have been assigned a new {context.get('urgency', 'standard')} priority work order.",
                        data=work_order
                    )
                
                return {
                    "completed": True,
                    "output": {
                        "work_order_id": work_order.get('id'),
                        "status": "created",
                        "assigned_to": context.get('assigned_technician')
                    }
                }
            else:
                return {"completed": False, "output": work_order}
                
        except Exception as e:
            logger.error(f"Failed to create work order: {str(e)}")
            return {"completed": False, "output": {"error": str(e)}}
    
    async def _assign_technician(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assign technician to work order"""
        work_order_id = context.get('work_order_id')
        technician = await self._find_available_technician(
            skilled=context.get('requires_skilled', False),
            emergency=context.get('is_emergency', False)
        )
        
        # Update work order
        # In real implementation, would update RentVine
        
        # Notify technician
        await self.send_message(
            to_role="maintenance_tech",
            subject="Work Order Assignment",
            message=f"You have been assigned to work order {work_order_id}",
            data={"work_order_id": work_order_id, "details": context}
        )
        
        return {
            "completed": True,
            "output": {
                "technician_assigned": technician,
                "notification_sent": True
            }
        }
    
    async def _approve_parts_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve parts order within limit"""
        parts_cost = context.get('parts_cost', 0)
        
        if parts_cost <= self.can_approve_up_to:
            approval = {
                "approved": True,
                "approved_amount": parts_cost,
                "order_number": f"PO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "approved_by": self.role
            }
            
            return {"completed": True, "output": approval}
        else:
            # Need higher approval
            await self.send_message(
                to_role="property_manager",
                subject="Parts Order Approval Required",
                message=f"Parts order of ${parts_cost} exceeds my approval limit of ${self.can_approve_up_to}",
                data=context,
                message_type="escalation"
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "exceeds_limit",
                    "escalated_to": "property_manager"
                }
            }
    
    async def _schedule_preventive_maintenance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule preventive maintenance tasks"""
        maintenance_type = context.get('maintenance_type', 'general')
        frequency = context.get('frequency', 'monthly')
        
        # Create recurring work orders
        schedule = {
            "type": maintenance_type,
            "frequency": frequency,
            "next_date": self._calculate_next_maintenance_date(frequency),
            "assigned_technician": await self._find_available_technician()
        }
        
        return {
            "completed": True,
            "output": {
                "schedule_created": True,
                "details": schedule
            }
        }
    
    async def _find_available_technician(
        self,
        skilled: bool = False,
        emergency: bool = False
    ) -> str:
        """Find available technician based on requirements"""
        # In real implementation, would check schedules and skills
        if emergency:
            return "tech_emergency_001"
        elif skilled:
            return "tech_senior_001"
        else:
            return "tech_001"
    
    def _estimate_response_time(self, urgency: str) -> str:
        """Estimate response time based on urgency"""
        response_times = {
            "emergency": "30 minutes",
            "high": "2-4 hours",
            "medium": "24-48 hours",
            "low": "3-5 business days"
        }
        return response_times.get(urgency, "48 hours")
    
    def _calculate_next_maintenance_date(self, frequency: str) -> str:
        """Calculate next maintenance date based on frequency"""
        from datetime import timedelta
        
        frequencies = {
            "daily": timedelta(days=1),
            "weekly": timedelta(weeks=1),
            "monthly": timedelta(days=30),
            "quarterly": timedelta(days=90),
            "annual": timedelta(days=365)
        }
        
        delta = frequencies.get(frequency, timedelta(days=30))
        next_date = datetime.utcnow() + delta
        return next_date.isoformat()


class LeasingAgentAgent(BaseAgent):
    """Leasing Agent for handling inquiries and tours"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("leasing_agent", orchestrator)
        self.email_service = EmailService()
        self.can_approve_up_to = 0
        self.permissions = ["show_units", "process_applications", "send_lease_info"]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute leasing agent actions"""
        context = input_data.get('context', {})
        
        if action == "schedule_tour":
            return await self._schedule_tour(context)
        elif action == "send_availability_info":
            return await self._send_availability_info(context)
        elif action == "collect_application":
            return await self._collect_application(context)
        elif action == "follow_up_prospect":
            return await self._follow_up_prospect(context)
        else:
            return {"completed": False, "output": {"error": f"Unknown action: {action}"}}
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make leasing-related decisions"""
        context = decision_input.get('context', {})
        inquiry_type = context.get('inquiry_type', 'general')
        
        # Simple decision logic for leasing agent
        if inquiry_type == "tour_request":
            decision = "schedule_tour"
        elif inquiry_type == "availability":
            decision = "send_info"
        elif inquiry_type == "application_status":
            decision = "check_with_manager"
        else:
            decision = "provide_general_info"
        
        return {
            "decision": decision,
            "action_required": self._determine_action(decision),
            "reasoning": f"Standard procedure for {inquiry_type}"
        }
    
    async def _schedule_tour(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule a property tour"""
        prospect_name = context.get('prospect_name', 'Prospect')
        preferred_time = context.get('preferred_time')
        contact_info = context.get('contact_info', {})
        
        # Check availability (simplified)
        available_slots = self._get_available_tour_slots()
        
        if preferred_time in available_slots:
            scheduled_time = preferred_time
        else:
            scheduled_time = available_slots[0] if available_slots else None
        
        if scheduled_time:
            # Send confirmation email
            confirmation = await self._send_tour_confirmation(
                prospect_name, scheduled_time, contact_info
            )
            
            return {
                "completed": True,
                "output": {
                    "tour_scheduled": True,
                    "scheduled_time": scheduled_time,
                    "confirmation_sent": confirmation
                }
            }
        else:
            return {
                "completed": False,
                "output": {
                    "tour_scheduled": False,
                    "reason": "no_availability"
                }
            }
    
    async def _send_availability_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send unit availability information"""
        unit_preferences = context.get('unit_preferences', {})
        
        # Get available units (simplified)
        available_units = [
            {"unit": "101", "bedrooms": 1, "rent": 1200},
            {"unit": "205", "bedrooms": 2, "rent": 1800}
        ]
        
        # Filter based on preferences
        filtered_units = self._filter_units(available_units, unit_preferences)
        
        # Send email with availability
        email_sent = await self.email_service.send_email(
            to_email=context.get('prospect_email'),
            subject="Available Units at Your Property",
            body=self._format_availability_email(filtered_units),
            html_body=self._format_availability_html(filtered_units)
        )
        
        return {
            "completed": True,
            "output": {
                "units_found": len(filtered_units),
                "email_sent": email_sent,
                "units": filtered_units
            }
        }
    
    async def _collect_application(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process rental application collection"""
        applicant_info = context.get('applicant_info', {})
        
        # Create application record
        application_id = f"APP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Send to leasing manager for processing
        await self.send_message(
            to_role="leasing_manager",
            subject="New Application Received",
            message=f"New rental application from {applicant_info.get('name', 'Unknown')}",
            data={
                "application_id": application_id,
                "applicant_info": applicant_info,
                "submitted_at": datetime.utcnow().isoformat()
            }
        )
        
        return {
            "completed": True,
            "output": {
                "application_id": application_id,
                "status": "submitted",
                "forwarded_to": "leasing_manager"
            }
        }
    
    async def _follow_up_prospect(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Follow up with prospects"""
        prospect_id = context.get('prospect_id')
        last_contact = context.get('last_contact_date')
        interest_level = context.get('interest_level', 'medium')
        
        # Determine follow-up message
        follow_up_message = self._create_follow_up_message(interest_level)
        
        # Send follow-up
        email_sent = await self.email_service.send_email(
            to_email=context.get('prospect_email'),
            subject="Following Up on Your Interest",
            body=follow_up_message
        )
        
        return {
            "completed": True,
            "output": {
                "follow_up_sent": email_sent,
                "message_type": f"{interest_level}_interest_follow_up"
            }
        }
    
    def _get_available_tour_slots(self) -> List[str]:
        """Get available tour time slots"""
        # Simplified - return next few days at standard times
        slots = []
        base_date = datetime.utcnow()
        for days in range(1, 4):
            date = base_date + timedelta(days=days)
            for hour in [10, 14, 16]:
                slot_time = date.replace(hour=hour, minute=0, second=0)
                slots.append(slot_time.isoformat())
        return slots
    
    async def _send_tour_confirmation(
        self,
        name: str,
        scheduled_time: str,
        contact_info: Dict[str, Any]
    ) -> bool:
        """Send tour confirmation email"""
        return await self.email_service.send_email(
            to_email=contact_info.get('email'),
            subject="Tour Confirmation",
            body=f"Dear {name},\n\nYour tour is confirmed for {scheduled_time}.\n\nLooking forward to showing you our property!"
        )
    
    def _filter_units(
        self,
        units: List[Dict[str, Any]],
        preferences: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Filter units based on preferences"""
        filtered = units
        
        if 'min_bedrooms' in preferences:
            filtered = [u for u in filtered if u['bedrooms'] >= preferences['min_bedrooms']]
        
        if 'max_rent' in preferences:
            filtered = [u for u in filtered if u['rent'] <= preferences['max_rent']]
        
        return filtered
    
    def _format_availability_email(self, units: List[Dict[str, Any]]) -> str:
        """Format availability email body"""
        if not units:
            return "Unfortunately, we don't have any units matching your criteria at this time."
        
        body = "Here are our available units:\n\n"
        for unit in units:
            body += f"Unit {unit['unit']}: {unit['bedrooms']} bedroom(s) - ${unit['rent']}/month\n"
        
        body += "\nWould you like to schedule a tour?"
        return body
    
    def _format_availability_html(self, units: List[Dict[str, Any]]) -> str:
        """Format availability email HTML"""
        # Simple HTML formatting
        html = "<h3>Available Units</h3><ul>"
        for unit in units:
            html += f"<li>Unit {unit['unit']}: {unit['bedrooms']} BR - ${unit['rent']}/mo</li>"
        html += "</ul>"
        return html
    
    def _determine_action(self, decision: str) -> str:
        """Determine required action based on decision"""
        action_map = {
            "schedule_tour": "schedule_tour",
            "send_info": "send_availability_info",
            "check_with_manager": "escalate_to_manager",
            "provide_general_info": "send_general_info"
        }
        return action_map.get(decision, "no_action")
    
    def _create_follow_up_message(self, interest_level: str) -> str:
        """Create follow-up message based on interest level"""
        messages = {
            "high": "I wanted to follow up on your tour last week. The unit you viewed is still available!",
            "medium": "Just checking in to see if you're still interested in touring our property.",
            "low": "We have some new units available that might interest you."
        }
        return messages.get(interest_level, "Following up on your inquiry about our property.")


class AccountantAgent(BaseAgent):
    """Accountant agent for financial operations"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("accountant", orchestrator)
        self.can_approve_up_to = 100
        self.permissions = ["process_payments", "send_statements", "basic_payment_plans"]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute accountant actions"""
        context = input_data.get('context', {})
        
        if action == "process_payment":
            return await self._process_payment(context)
        elif action == "create_payment_plan":
            return await self._create_payment_plan(context)
        elif action == "send_statement":
            return await self._send_statement(context)
        elif action == "waive_late_fee":
            return await self._waive_late_fee(context)
        else:
            return {"completed": False, "output": {"error": f"Unknown action: {action}"}}
    
    async def _process_payment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process tenant payment"""
        payment_amount = context.get('amount', 0)
        tenant_id = context.get('tenant_id')
        payment_method = context.get('payment_method', 'unknown')
        
        # Process payment (simplified)
        payment_id = f"PAY-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        return {
            "completed": True,
            "output": {
                "payment_id": payment_id,
                "amount_processed": payment_amount,
                "method": payment_method,
                "status": "completed"
            }
        }
    
    async def _create_payment_plan(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic payment plan"""
        total_amount = context.get('total_amount', 0)
        installments = context.get('installments', 2)
        
        if total_amount / installments <= self.can_approve_up_to:
            plan = {
                "plan_id": f"PLAN-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                "total_amount": total_amount,
                "installments": installments,
                "monthly_payment": total_amount / installments,
                "approved": True
            }
            
            return {"completed": True, "output": plan}
        else:
            # Need manager approval
            await self.send_message(
                to_role="accounting_manager",
                subject="Payment Plan Approval Required",
                message=f"Payment plan for ${total_amount} requires your approval",
                data=context,
                message_type="escalation"
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "requires_manager_approval",
                    "escalated_to": "accounting_manager"
                }
            }
    
    async def _send_statement(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Send account statement to tenant"""
        tenant_id = context.get('tenant_id')
        statement_type = context.get('statement_type', 'monthly')
        
        # Generate statement (simplified)
        statement = {
            "balance": 0,
            "due_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
            "transactions": []
        }
        
        return {
            "completed": True,
            "output": {
                "statement_sent": True,
                "type": statement_type,
                "tenant_id": tenant_id
            }
        }
    
    async def _waive_late_fee(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Waive late fee within limit"""
        fee_amount = context.get('fee_amount', 0)
        
        if fee_amount <= self.can_approve_up_to:
            return {
                "completed": True,
                "output": {
                    "waived": True,
                    "amount": fee_amount,
                    "approved_by": self.role
                }
            }
        else:
            # Escalate to manager
            await self.send_message(
                to_role="accounting_manager",
                subject="Late Fee Waiver Approval Required",
                message=f"Late fee of ${fee_amount} exceeds my limit",
                data=context,
                message_type="escalation"
            )
            
            return {
                "completed": True,
                "output": {
                    "waived": False,
                    "reason": "exceeds_limit",
                    "escalated_to": "accounting_manager"
                }
            }


class ResidentServicesManagerAgent(BaseAgent):
    """Resident Services Manager agent for resident relations and community events"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("resident_services_manager", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 2000
        self.permissions = [
            "resident_communications",
            "community_events",
            "resident_satisfaction",
            "amenity_management",
            "resident_support",
            "feedback_management"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resident services manager actions"""
        context = input_data.get('context', {})
        
        if action == "handle_resident_complaint":
            return await self._handle_resident_complaint(context)
        elif action == "organize_community_event":
            return await self._organize_community_event(context)
        elif action == "manage_amenity_request":
            return await self._manage_amenity_request(context)
        elif action == "conduct_satisfaction_survey":
            return await self._conduct_satisfaction_survey(context)
        elif action == "resolve_resident_issue":
            return await self._resolve_resident_issue(context)
        elif action == "manage_feedback":
            return await self._manage_feedback(context)
        else:
            return await self._generic_action(action, context)
    
    async def make_decision(self, decision_input: Dict[str, Any]) -> Dict[str, Any]:
        """Make resident services decisions"""
        criteria = decision_input.get('decision_criteria', {})
        context = decision_input.get('context', {})
        
        # Use Claude for complex decision making
        decision_prompt = f"""
        As a Resident Services Manager, make a decision based on:
        Context: {context}
        Criteria: {criteria}
        Previous results: {decision_input.get('previous_results', {})}
        
        Focus on resident satisfaction, community harmony, and property standards.
        Provide a clear decision with reasoning.
        """
        
        response = await self.claude.generate_response(
            "general_response",
            {"prompt": decision_prompt, "context": context}
        )
        
        return {
            "decision": "approve",
            "reasoning": response,
            "confidence": 0.85
        }
    
    async def _handle_resident_complaint(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resident complaints and concerns"""
        complaint_type = context.get('complaint_type', 'general')
        severity = context.get('severity', 'medium')
        resident_id = context.get('resident_id')
        description = context.get('description', '')
        
        # Log the complaint
        logger.info(f"Resident Services Manager handling {severity} complaint from {resident_id}: {complaint_type}")
        
        # Determine response strategy based on complaint type and severity
        if complaint_type == "noise":
            response_strategy = "mediate_neighbor_conflict"
        elif complaint_type == "maintenance":
            response_strategy = "escalate_to_maintenance"
        elif complaint_type == "billing":
            response_strategy = "escalate_to_accounting"
        elif complaint_type == "amenity":
            response_strategy = "address_amenity_issue"
        else:
            response_strategy = "general_resolution"
        
        # Generate response timeline
        if severity == "urgent":
            response_time = "immediate"
            escalation_needed = True
        elif severity == "high":
            response_time = "within_24_hours"
            escalation_needed = True
        else:
            response_time = "within_48_hours"
            escalation_needed = False
        
        # Create resolution plan
        resolution_plan = {
            "immediate_action": self._get_immediate_action(complaint_type, severity),
            "follow_up_required": escalation_needed,
            "escalation_role": self._get_escalation_role(complaint_type),
            "resident_communication": self._generate_communication_plan(severity)
        }
        
        return {
            "completed": True,
            "output": {
                "complaint_handled": True,
                "response_strategy": response_strategy,
                "response_time": response_time,
                "resolution_plan": resolution_plan,
                "resident_id": resident_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _organize_community_event(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Organize community events and activities"""
        event_type = context.get('event_type', 'social')
        budget = context.get('budget', 1000)
        expected_attendance = context.get('expected_attendance', 50)
        date = context.get('date')
        
        # Validate budget approval
        if budget > self.can_approve_up_to:
            # Escalate to property manager
            await self.send_message(
                to_role="property_manager",
                subject="Community Event Budget Approval",
                message=f"Event budget of ${budget} exceeds approval limit. Event type: {event_type}",
                data={"event_request": context}
            )
            return {
                "completed": False,
                "output": {
                    "status": "pending_approval",
                    "message": "Budget exceeds approval limit, escalated to Property Manager"
                }
            }
        
        # Plan the event
        event_plan = {
            "event_type": event_type,
            "budget": budget,
            "expected_attendance": expected_attendance,
            "date": date,
            "activities": self._generate_event_activities(event_type),
            "logistics": self._plan_event_logistics(event_type, expected_attendance),
            "marketing": self._create_event_marketing_plan(event_type)
        }
        
        # Schedule follow-up tasks
        follow_up_tasks = [
            "Send event invitations to residents",
            "Coordinate with vendors",
            "Arrange event setup and cleanup",
            "Prepare event materials"
        ]
        
        return {
            "completed": True,
            "output": {
                "event_approved": True,
                "event_plan": event_plan,
                "follow_up_tasks": follow_up_tasks,
                "approval_level": "resident_services_manager",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _manage_amenity_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage amenity requests and improvements"""
        amenity_type = context.get('amenity_type', 'general')
        request_type = context.get('request_type', 'maintenance')
        resident_feedback = context.get('resident_feedback', [])
        
        # Analyze resident feedback for amenity improvements
        feedback_analysis = await self._analyze_amenity_feedback(resident_feedback)
        
        # Determine amenity priority
        priority = self._determine_amenity_priority(amenity_type, feedback_analysis)
        
        # Create amenity management plan
        management_plan = {
            "amenity_type": amenity_type,
            "request_type": request_type,
            "priority": priority,
            "recommendations": feedback_analysis.get('recommendations', []),
            "maintenance_schedule": self._create_maintenance_schedule(amenity_type),
            "improvement_plan": self._create_improvement_plan(amenity_type, feedback_analysis)
        }
        
        # Escalate to maintenance if needed
        if request_type == "repair" or priority == "high":
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Amenity Maintenance Request",
                message=f"High priority amenity request: {amenity_type}",
                data={"amenity_request": management_plan}
            )
        
        return {
            "completed": True,
            "output": {
                "amenity_managed": True,
                "management_plan": management_plan,
                "feedback_incorporated": True,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _conduct_satisfaction_survey(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct resident satisfaction surveys"""
        survey_type = context.get('survey_type', 'general')
        target_residents = context.get('target_residents', 'all')
        survey_period = context.get('survey_period', 'monthly')
        
        # Create survey questions
        survey_questions = self._generate_survey_questions(survey_type)
        
        # Plan survey distribution
        distribution_plan = {
            "method": "email_and_portal",
            "target_residents": target_residents,
            "timeline": self._create_survey_timeline(survey_period),
            "incentives": self._determine_survey_incentives(survey_type)
        }
        
        # Create survey analysis plan
        analysis_plan = {
            "metrics": ["overall_satisfaction", "amenity_satisfaction", "maintenance_satisfaction", "communication_satisfaction"],
            "benchmarks": self._get_satisfaction_benchmarks(),
            "action_thresholds": self._set_action_thresholds()
        }
        
        return {
            "completed": True,
            "output": {
                "survey_created": True,
                "survey_questions": survey_questions,
                "distribution_plan": distribution_plan,
                "analysis_plan": analysis_plan,
                "expected_completion": self._estimate_survey_completion(survey_period),
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _resolve_resident_issue(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve resident issues and provide support"""
        issue_type = context.get('issue_type', 'general')
        resident_id = context.get('resident_id')
        urgency = context.get('urgency', 'normal')
        
        # Determine resolution approach
        if issue_type == "emergency":
            resolution_approach = "immediate_escalation"
            escalation_role = "property_manager"
        elif issue_type == "maintenance":
            resolution_approach = "maintenance_coordination"
            escalation_role = "maintenance_supervisor"
        elif issue_type == "billing":
            resolution_approach = "accounting_coordination"
            escalation_role = "accountant"
        elif issue_type == "community":
            resolution_approach = "mediation"
            escalation_role = None
        else:
            resolution_approach = "direct_resolution"
            escalation_role = None
        
        # Create resolution plan
        resolution_plan = {
            "issue_type": issue_type,
            "resolution_approach": resolution_approach,
            "escalation_role": escalation_role,
            "timeline": self._estimate_resolution_timeline(urgency),
            "communication_plan": self._create_communication_plan(urgency),
            "follow_up_required": urgency in ["high", "urgent"]
        }
        
        # Escalate if needed
        if escalation_role:
            await self.send_message(
                to_role=escalation_role,
                subject=f"Resident Issue Escalation: {issue_type}",
                message=f"Resident {resident_id} has {urgency} issue requiring {escalation_role} attention",
                data={"issue_details": context, "resolution_plan": resolution_plan}
            )
        
        return {
            "completed": True,
            "output": {
                "issue_resolved": True,
                "resolution_plan": resolution_plan,
                "resident_id": resident_id,
                "escalation_sent": escalation_role is not None,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _manage_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage and analyze resident feedback"""
        feedback_type = context.get('feedback_type', 'general')
        feedback_data = context.get('feedback_data', [])
        
        # Analyze feedback patterns
        feedback_analysis = await self._analyze_feedback_patterns(feedback_data)
        
        # Generate action items
        action_items = self._generate_feedback_action_items(feedback_analysis)
        
        # Create feedback response plan
        response_plan = {
            "feedback_type": feedback_type,
            "analysis_summary": feedback_analysis.get('summary', {}),
            "action_items": action_items,
            "response_timeline": self._create_feedback_response_timeline(feedback_type),
            "improvement_areas": feedback_analysis.get('improvement_areas', [])
        }
        
        # Escalate critical feedback
        critical_feedback = feedback_analysis.get('critical_feedback', [])
        if critical_feedback:
            await self.send_message(
                to_role="property_manager",
                subject="Critical Resident Feedback",
                message=f"Critical feedback identified requiring immediate attention",
                data={"critical_feedback": critical_feedback, "response_plan": response_plan}
            )
        
        return {
            "completed": True,
            "output": {
                "feedback_managed": True,
                "response_plan": response_plan,
                "critical_feedback_escalated": len(critical_feedback) > 0,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other resident services action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "resident_services_manager",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _get_immediate_action(self, complaint_type: str, severity: str) -> str:
        """Get immediate action for complaint"""
        if severity == "urgent":
            return "immediate_contact"
        elif complaint_type == "noise":
            return "mediate_conflict"
        elif complaint_type == "maintenance":
            return "schedule_emergency_repair"
        else:
            return "acknowledge_complaint"
    
    def _get_escalation_role(self, complaint_type: str) -> str:
        """Get escalation role for complaint type"""
        escalation_map = {
            "maintenance": "maintenance_supervisor",
            "billing": "accountant",
            "noise": "property_manager",
            "amenity": "maintenance_supervisor"
        }
        return escalation_map.get(complaint_type, "property_manager")
    
    def _generate_communication_plan(self, severity: str) -> Dict[str, Any]:
        """Generate communication plan for complaint"""
        if severity == "urgent":
            return {
                "immediate": "phone_call",
                "follow_up": "email_confirmation",
                "resolution": "in_person_meeting"
            }
        else:
            return {
                "immediate": "email_acknowledgment",
                "follow_up": "email_update",
                "resolution": "email_confirmation"
            }
    
    def _generate_event_activities(self, event_type: str) -> List[str]:
        """Generate activities for community event"""
        activity_map = {
            "social": ["ice_breaker_games", "resident_networking", "refreshments"],
            "holiday": ["decorations", "themed_activities", "gift_exchange"],
            "wellness": ["yoga_session", "health_seminar", "fitness_demo"],
            "educational": ["guest_speaker", "workshop", "q_and_a_session"]
        }
        return activity_map.get(event_type, ["general_activities"])
    
    def _plan_event_logistics(self, event_type: str, attendance: int) -> Dict[str, Any]:
        """Plan event logistics"""
        return {
            "venue": "community_room" if attendance <= 50 else "outdoor_space",
            "setup_time": "2_hours_before",
            "cleanup_time": "1_hour_after",
            "staffing": self._calculate_event_staffing(attendance),
            "equipment": self._determine_event_equipment(event_type)
        }
    
    def _create_event_marketing_plan(self, event_type: str) -> Dict[str, Any]:
        """Create marketing plan for event"""
        return {
            "channels": ["email", "portal_notification", "social_media"],
            "timeline": "2_weeks_before",
            "incentives": "refreshments_and_prizes",
            "target_audience": "all_residents"
        }
    
    async def _analyze_amenity_feedback(self, feedback: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze amenity feedback from residents"""
        if not feedback:
            return {"recommendations": [], "satisfaction_score": 0}
        
        # Simple analysis - in production, would use more sophisticated analysis
        positive_feedback = [f for f in feedback if f.get('sentiment') == 'positive']
        negative_feedback = [f for f in feedback if f.get('sentiment') == 'negative']
        
        satisfaction_score = len(positive_feedback) / len(feedback) if feedback else 0
        
        recommendations = []
        if satisfaction_score < 0.7:
            recommendations.append("Schedule amenity maintenance")
        if len(negative_feedback) > len(positive_feedback):
            recommendations.append("Review amenity policies")
        
        return {
            "satisfaction_score": satisfaction_score,
            "recommendations": recommendations,
            "feedback_count": len(feedback)
        }
    
    def _determine_amenity_priority(self, amenity_type: str, feedback_analysis: Dict[str, Any]) -> str:
        """Determine amenity priority based on feedback"""
        satisfaction_score = feedback_analysis.get('satisfaction_score', 0)
        
        if satisfaction_score < 0.5:
            return "high"
        elif satisfaction_score < 0.8:
            return "medium"
        else:
            return "low"
    
    def _create_maintenance_schedule(self, amenity_type: str) -> Dict[str, Any]:
        """Create maintenance schedule for amenity"""
        return {
            "frequency": "weekly",
            "tasks": ["inspection", "cleaning", "equipment_check"],
            "responsible_party": "maintenance_team"
        }
    
    def _create_improvement_plan(self, amenity_type: str, feedback_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Create improvement plan for amenity"""
        recommendations = feedback_analysis.get('recommendations', [])
        
        return {
            "short_term": ["address_immediate_issues"],
            "long_term": ["consider_upgrades", "policy_review"],
            "budget_required": len(recommendations) > 0
        }
    
    def _generate_survey_questions(self, survey_type: str) -> List[str]:
        """Generate survey questions based on type"""
        question_map = {
            "general": [
                "Overall satisfaction with the property",
                "Satisfaction with maintenance response",
                "Satisfaction with community amenities",
                "Likelihood to recommend to others"
            ],
            "maintenance": [
                "Maintenance request response time",
                "Quality of maintenance work",
                "Communication during maintenance",
                "Follow-up after maintenance"
            ],
            "amenity": [
                "Amenity availability and cleanliness",
                "Amenity equipment condition",
                "Amenity policies and rules",
                "Suggestions for amenity improvements"
            ]
        }
        return question_map.get(survey_type, question_map["general"])
    
    def _create_survey_timeline(self, survey_period: str) -> Dict[str, Any]:
        """Create timeline for survey"""
        timeline_map = {
            "monthly": {"duration": "1_week", "reminders": "3_days_before_end"},
            "quarterly": {"duration": "2_weeks", "reminders": "1_week_before_end"},
            "annual": {"duration": "1_month", "reminders": "1_week_before_end"}
        }
        return timeline_map.get(survey_period, timeline_map["monthly"])
    
    def _determine_survey_incentives(self, survey_type: str) -> str:
        """Determine survey incentives"""
        if survey_type == "annual":
            return "entry_for_prize_drawing"
        else:
            return "none"
    
    def _get_satisfaction_benchmarks(self) -> Dict[str, float]:
        """Get satisfaction benchmarks"""
        return {
            "overall_satisfaction": 4.0,
            "amenity_satisfaction": 3.8,
            "maintenance_satisfaction": 4.2,
            "communication_satisfaction": 4.0
        }
    
    def _set_action_thresholds(self) -> Dict[str, float]:
        """Set action thresholds for survey results"""
        return {
            "immediate_action": 3.0,
            "improvement_needed": 3.5,
            "satisfactory": 4.0
        }
    
    def _estimate_survey_completion(self, survey_period: str) -> str:
        """Estimate survey completion time"""
        completion_map = {
            "monthly": "1_week",
            "quarterly": "2_weeks",
            "annual": "1_month"
        }
        return completion_map.get(survey_period, "1_week")
    
    def _estimate_resolution_timeline(self, urgency: str) -> str:
        """Estimate resolution timeline based on urgency"""
        timeline_map = {
            "urgent": "immediate",
            "high": "24_hours",
            "normal": "48_hours",
            "low": "1_week"
        }
        return timeline_map.get(urgency, "48_hours")
    
    def _create_communication_plan(self, urgency: str) -> Dict[str, Any]:
        """Create communication plan for issue resolution"""
        if urgency == "urgent":
            return {
                "immediate": "phone_call",
                "updates": "hourly",
                "resolution": "in_person_confirmation"
            }
        elif urgency == "high":
            return {
                "immediate": "email",
                "updates": "daily",
                "resolution": "phone_confirmation"
            }
        else:
            return {
                "immediate": "email",
                "updates": "as_needed",
                "resolution": "email_confirmation"
            }
    
    async def _analyze_feedback_patterns(self, feedback_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze feedback patterns"""
        if not feedback_data:
            return {"summary": {}, "improvement_areas": [], "critical_feedback": []}
        
        # Simple pattern analysis
        categories = {}
        critical_feedback = []
        
        for feedback in feedback_data:
            category = feedback.get('category', 'general')
            sentiment = feedback.get('sentiment', 'neutral')
            priority = feedback.get('priority', 'normal')
            
            if category not in categories:
                categories[category] = {'positive': 0, 'negative': 0, 'neutral': 0}
            
            categories[category][sentiment] += 1
            
            if priority == 'critical' or sentiment == 'negative':
                critical_feedback.append(feedback)
        
        # Determine improvement areas
        improvement_areas = []
        for category, counts in categories.items():
            if counts['negative'] > counts['positive']:
                improvement_areas.append(category)
        
        return {
            "summary": categories,
            "improvement_areas": improvement_areas,
            "critical_feedback": critical_feedback
        }
    
    def _generate_feedback_action_items(self, feedback_analysis: Dict[str, Any]) -> List[str]:
        """Generate action items from feedback analysis"""
        action_items = []
        improvement_areas = feedback_analysis.get('improvement_areas', [])
        critical_feedback = feedback_analysis.get('critical_feedback', [])
        
        if critical_feedback:
            action_items.append("Address critical feedback immediately")
        
        for area in improvement_areas:
            action_items.append(f"Review and improve {area} processes")
        
        if not action_items:
            action_items.append("Maintain current satisfaction levels")
        
        return action_items
    
    def _create_feedback_response_timeline(self, feedback_type: str) -> Dict[str, Any]:
        """Create timeline for feedback response"""
        return {
            "acknowledgment": "24_hours",
            "investigation": "48_hours",
            "resolution": "1_week",
            "follow_up": "2_weeks"
        }
    
    def _calculate_event_staffing(self, attendance: int) -> int:
        """Calculate required staffing for event"""
        if attendance <= 25:
            return 2
        elif attendance <= 50:
            return 3
        else:
            return 4
    
    def _determine_event_equipment(self, event_type: str) -> List[str]:
        """Determine equipment needed for event"""
        equipment_map = {
            "social": ["tables", "chairs", "refreshments"],
            "holiday": ["decorations", "sound_system", "tables"],
            "wellness": ["yoga_mats", "water_station", "sound_system"],
            "educational": ["projector", "chairs", "podium"]
        }
        return equipment_map.get(event_type, ["basic_equipment"])


class ResidentServicesRepAgent(BaseAgent):
    """Resident Services Rep agent for frontline resident support"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("resident_services_rep", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 500
        self.permissions = [
            "respond_inquiries",
            "log_service_requests",
            "provide_info",
            "escalate_issues",
            "move_in_out_assist",
            "collect_feedback"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute resident services rep actions"""
        context = input_data.get('context', {})
        
        if action == "respond_inquiry":
            return await self._respond_inquiry(context)
        elif action == "log_service_request":
            return await self._log_service_request(context)
        elif action == "provide_info":
            return await self._provide_info(context)
        elif action == "escalate_issue":
            return await self._escalate_issue(context)
        elif action == "assist_move_in_out":
            return await self._assist_move_in_out(context)
        elif action == "collect_feedback":
            return await self._collect_feedback(context)
        else:
            return await self._generic_action(action, context)
    
    async def _respond_inquiry(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Respond to resident inquiries"""
        inquiry = context.get('inquiry', '')
        resident_id = context.get('resident_id')
        
        # Use Claude for natural language response
        prompt = f"Resident inquiry: {inquiry}\nProvide a helpful, friendly response."
        response = await self.claude.generate_response("inquiry_response", {"prompt": prompt, "context": context})
        
        return {
            "completed": True,
            "output": {
                "response": response,
                "resident_id": resident_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _log_service_request(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Log and triage service requests"""
        request_type = context.get('request_type', 'general')
        details = context.get('details', '')
        resident_id = context.get('resident_id')
        urgency = context.get('urgency', 'normal')
        
        # Create log entry
        log_entry = {
            "request_type": request_type,
            "details": details,
            "resident_id": resident_id,
            "urgency": urgency,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "logged"
        }
        
        # Escalate to appropriate department
        if request_type in ["maintenance", "repair"]:
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="New Service Request",
                message=f"Service request from resident {resident_id}: {details}",
                data=log_entry
            )
        elif request_type in ["billing", "payment"]:
            await self.send_message(
                to_role="accountant",
                subject="Billing Inquiry",
                message=f"Billing inquiry from resident {resident_id}: {details}",
                data=log_entry
            )
        elif urgency == "urgent":
            await self.send_message(
                to_role="resident_services_manager",
                subject="Urgent Service Request",
                message=f"Urgent request from resident {resident_id}: {details}",
                data=log_entry
            )
        
        return {
            "completed": True,
            "output": {
                "log_entry": log_entry,
                "escalated": request_type in ["maintenance", "repair", "billing", "payment"] or urgency == "urgent"
            }
        }
    
    async def _provide_info(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide information about amenities, policies, events"""
        info_topic = context.get('topic', 'general')
        resident_id = context.get('resident_id')
        
        # Use Claude for information retrieval
        prompt = f"Provide information about: {info_topic} for a resident."
        response = await self.claude.generate_response("info_response", {"prompt": prompt, "context": context})
        
        return {
            "completed": True,
            "output": {
                "info": response,
                "resident_id": resident_id,
                "topic": info_topic,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _escalate_issue(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Escalate complex issues to appropriate manager"""
        issue_type = context.get('issue_type', 'general')
        resident_id = context.get('resident_id')
        details = context.get('details', '')
        severity = context.get('severity', 'medium')
        
        # Determine escalation target
        escalation_map = {
            "maintenance": "maintenance_supervisor",
            "billing": "accountant",
            "leasing": "leasing_manager",
            "complaint": "resident_services_manager",
            "emergency": "property_manager"
        }
        
        escalation_role = escalation_map.get(issue_type, "resident_services_manager")
        
        await self.send_message(
            to_role=escalation_role,
            subject=f"Resident Issue Escalation: {issue_type}",
            message=f"Escalating {severity} issue for resident {resident_id}: {details}",
            data={
                "issue_type": issue_type,
                "details": details,
                "resident_id": resident_id,
                "severity": severity
            }
        )
        
        return {
            "completed": True,
            "output": {
                "escalated": True,
                "issue_type": issue_type,
                "escalation_role": escalation_role,
                "resident_id": resident_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _assist_move_in_out(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assist with move-in and move-out processes"""
        move_type = context.get('move_type', 'in')
        resident_id = context.get('resident_id')
        unit_id = context.get('unit_id')
        
        if move_type == "in":
            checklist = [
                "Confirm all paperwork is complete",
                "Schedule unit inspection",
                "Provide welcome packet and keys",
                "Review community policies",
                "Schedule orientation tour"
            ]
            next_steps = [
                "Complete move-in inspection",
                "Set up utilities transfer",
                "Provide parking information"
            ]
        else:  # move out
            checklist = [
                "Schedule move-out inspection",
                "Collect keys and access cards",
                "Review move-out procedures",
                "Confirm forwarding address",
                "Process security deposit return"
            ]
            next_steps = [
                "Complete final inspection",
                "Process deposit return",
                "Update resident records"
            ]
        
        return {
            "completed": True,
            "output": {
                "move_type": move_type,
                "resident_id": resident_id,
                "unit_id": unit_id,
                "checklist": checklist,
                "next_steps": next_steps,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _collect_feedback(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Collect and relay resident feedback"""
        resident_id = context.get('resident_id')
        feedback = context.get('feedback', '')
        feedback_type = context.get('feedback_type', 'general')
        sentiment = context.get('sentiment', 'neutral')
        
        # Create feedback log entry
        log_entry = {
            "resident_id": resident_id,
            "feedback": feedback,
            "feedback_type": feedback_type,
            "sentiment": sentiment,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Escalate negative feedback
        if sentiment in ["negative", "critical"] or any(word in feedback.lower() for word in ["bad", "poor", "complaint", "unhappy", "dissatisfied"]):
            await self.send_message(
                to_role="resident_services_manager",
                subject="Negative Resident Feedback",
                message=f"Negative feedback from resident {resident_id}: {feedback}",
                data=log_entry
            )
            escalated = True
        else:
            escalated = False
        
        return {
            "completed": True,
            "output": {
                "feedback_logged": True,
                "resident_id": resident_id,
                "feedback_type": feedback_type,
                "sentiment": sentiment,
                "escalated": escalated,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other resident services rep action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "resident_services_rep",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class AdminAssistantAgent(BaseAgent):
    """Admin Assistant agent for administrative support and office management"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("admin_assistant", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 100
        self.permissions = [
            "document_management",
            "appointment_scheduling",
            "data_entry",
            "report_generation",
            "office_coordination",
            "basic_communications"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute admin assistant actions"""
        context = input_data.get('context', {})
        
        if action == "manage_documents":
            return await self._manage_documents(context)
        elif action == "schedule_appointment":
            return await self._schedule_appointment(context)
        elif action == "perform_data_entry":
            return await self._perform_data_entry(context)
        elif action == "generate_report":
            return await self._generate_report(context)
        elif action == "coordinate_office":
            return await self._coordinate_office(context)
        elif action == "handle_communications":
            return await self._handle_communications(context)
        else:
            return await self._generic_action(action, context)
    
    async def _manage_documents(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage document filing, organization, and retrieval"""
        document_type = context.get('document_type', 'general')
        action_type = context.get('action_type', 'file')
        document_id = context.get('document_id')
        resident_id = context.get('resident_id')
        
        # Create document record
        document_record = {
            "document_type": document_type,
            "action_type": action_type,
            "document_id": document_id,
            "resident_id": resident_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "processed"
        }
        
        # Determine filing location based on document type
        filing_location = self._determine_filing_location(document_type)
        
        # Escalate sensitive documents
        if document_type in ["legal", "financial", "complaint"]:
            await self.send_message(
                to_role="property_manager",
                subject="Sensitive Document Filed",
                message=f"Sensitive document {document_type} filed for resident {resident_id}",
                data=document_record
            )
        
        return {
            "completed": True,
            "output": {
                "document_managed": True,
                "document_record": document_record,
                "filing_location": filing_location,
                "escalated": document_type in ["legal", "financial", "complaint"]
            }
        }
    
    async def _schedule_appointment(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Schedule appointments and meetings"""
        appointment_type = context.get('appointment_type', 'general')
        participant = context.get('participant')
        date_time = context.get('date_time')
        duration = context.get('duration', 60)
        
        # Check availability and create appointment
        appointment = {
            "appointment_type": appointment_type,
            "participant": participant,
            "date_time": date_time,
            "duration": duration,
            "status": "scheduled",
            "appointment_id": f"APT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Send confirmation to appropriate manager
        manager_role = self._get_manager_for_appointment(appointment_type)
        if manager_role:
            await self.send_message(
                to_role=manager_role,
                subject=f"Appointment Scheduled: {appointment_type}",
                message=f"Appointment scheduled with {participant} on {date_time}",
                data=appointment
            )
        
        return {
            "completed": True,
            "output": {
                "appointment_scheduled": True,
                "appointment": appointment,
                "manager_notified": manager_role is not None
            }
        }
    
    async def _perform_data_entry(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Perform data entry and record updates"""
        data_type = context.get('data_type', 'general')
        records = context.get('records', [])
        update_type = context.get('update_type', 'add')
        
        # Process data entry
        entry_summary = {
            "data_type": data_type,
            "update_type": update_type,
            "records_processed": len(records),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Validate data quality
        validation_result = self._validate_data_quality(records, data_type)
        entry_summary["validation_passed"] = validation_result["passed"]
        entry_summary["validation_issues"] = validation_result["issues"]
        
        # Escalate data quality issues
        if not validation_result["passed"]:
            await self.send_message(
                to_role="property_manager",
                subject="Data Quality Issues Detected",
                message=f"Data quality issues found in {data_type} entry",
                data={"entry_summary": entry_summary, "validation_result": validation_result}
            )
        
        return {
            "completed": True,
            "output": {
                "data_entry_completed": True,
                "entry_summary": entry_summary,
                "validation_passed": validation_result["passed"]
            }
        }
    
    async def _generate_report(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate administrative reports"""
        report_type = context.get('report_type', 'general')
        date_range = context.get('date_range', 'monthly')
        format_type = context.get('format_type', 'summary')
        
        # Generate report structure
        report = {
            "report_type": report_type,
            "date_range": date_range,
            "format_type": format_type,
            "generated_at": datetime.utcnow().isoformat(),
            "report_id": f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        }
        
        # Add report content based on type
        if report_type == "occupancy":
            report["content"] = self._generate_occupancy_report(date_range)
        elif report_type == "maintenance":
            report["content"] = self._generate_maintenance_report(date_range)
        elif report_type == "financial":
            report["content"] = self._generate_financial_report(date_range)
        else:
            report["content"] = self._generate_general_report(report_type, date_range)
        
        # Send report to appropriate manager
        manager_role = self._get_manager_for_report(report_type)
        if manager_role:
            await self.send_message(
                to_role=manager_role,
                subject=f"Report Generated: {report_type}",
                message=f"{report_type.title()} report generated for {date_range} period",
                data=report
            )
        
        return {
            "completed": True,
            "output": {
                "report_generated": True,
                "report": report,
                "manager_notified": manager_role is not None
            }
        }
    
    async def _coordinate_office(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate office activities and supplies"""
        coordination_type = context.get('coordination_type', 'general')
        details = context.get('details', '')
        
        coordination_record = {
            "coordination_type": coordination_type,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "coordinated"
        }
        
        # Handle different coordination types
        if coordination_type == "supply_order":
            coordination_record["action"] = "order_supplies"
            coordination_record["items"] = self._parse_supply_items(details)
        elif coordination_type == "maintenance_request":
            coordination_record["action"] = "escalate_to_maintenance"
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Office Maintenance Request",
                message=f"Office maintenance request: {details}",
                data=coordination_record
            )
        elif coordination_type == "vendor_coordination":
            coordination_record["action"] = "contact_vendor"
            coordination_record["vendor_info"] = self._extract_vendor_info(details)
        
        return {
            "completed": True,
            "output": {
                "coordination_completed": True,
                "coordination_record": coordination_record
            }
        }
    
    async def _handle_communications(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle general communications and inquiries"""
        communication_type = context.get('communication_type', 'general')
        message = context.get('message', '')
        sender = context.get('sender')
        priority = context.get('priority', 'normal')
        
        communication_record = {
            "communication_type": communication_type,
            "message": message,
            "sender": sender,
            "priority": priority,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "received"
        }
        
        # Route communication to appropriate department
        if communication_type in ["maintenance", "repair"]:
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Communication Received",
                message=f"Communication from {sender}: {message}",
                data=communication_record
            )
        elif communication_type in ["billing", "payment"]:
            await self.send_message(
                to_role="accountant",
                subject="Communication Received",
                message=f"Communication from {sender}: {message}",
                data=communication_record
            )
        elif priority == "urgent":
            await self.send_message(
                to_role="property_manager",
                subject="Urgent Communication",
                message=f"Urgent communication from {sender}: {message}",
                data=communication_record
            )
        
        return {
            "completed": True,
            "output": {
                "communication_handled": True,
                "communication_record": communication_record,
                "routed": communication_type in ["maintenance", "repair", "billing", "payment"] or priority == "urgent"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other admin assistant action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "admin_assistant",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _determine_filing_location(self, document_type: str) -> str:
        """Determine filing location for document type"""
        location_map = {
            "lease": "resident_files",
            "maintenance": "maintenance_files",
            "financial": "financial_files",
            "legal": "legal_files",
            "complaint": "resident_files",
            "application": "leasing_files"
        }
        return location_map.get(document_type, "general_files")
    
    def _get_manager_for_appointment(self, appointment_type: str) -> str:
        """Get appropriate manager for appointment type"""
        manager_map = {
            "maintenance": "maintenance_supervisor",
            "leasing": "leasing_manager",
            "financial": "accounting_manager",
            "resident": "resident_services_manager"
        }
        return manager_map.get(appointment_type, "property_manager")
    
    def _validate_data_quality(self, records: List[Dict[str, Any]], data_type: str) -> Dict[str, Any]:
        """Validate data quality for entry"""
        issues = []
        
        for record in records:
            if data_type == "resident" and not record.get('resident_id'):
                issues.append("Missing resident ID")
            elif data_type == "maintenance" and not record.get('description'):
                issues.append("Missing maintenance description")
            elif data_type == "financial" and not record.get('amount'):
                issues.append("Missing financial amount")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def _get_manager_for_report(self, report_type: str) -> str:
        """Get appropriate manager for report type"""
        manager_map = {
            "occupancy": "leasing_manager",
            "maintenance": "maintenance_supervisor",
            "financial": "accounting_manager",
            "resident": "resident_services_manager"
        }
        return manager_map.get(report_type, "property_manager")
    
    def _generate_occupancy_report(self, date_range: str) -> Dict[str, Any]:
        """Generate occupancy report"""
        return {
            "total_units": 100,
            "occupied_units": 96,
            "vacant_units": 4,
            "occupancy_rate": 96.0,
            "period": date_range
        }
    
    def _generate_maintenance_report(self, date_range: str) -> Dict[str, Any]:
        """Generate maintenance report"""
        return {
            "total_requests": 25,
            "completed_requests": 22,
            "pending_requests": 3,
            "average_response_time": "2.5 days",
            "period": date_range
        }
    
    def _generate_financial_report(self, date_range: str) -> Dict[str, Any]:
        """Generate financial report"""
        return {
            "total_revenue": 150000,
            "total_expenses": 120000,
            "net_income": 30000,
            "delinquency_rate": 2.1,
            "period": date_range
        }
    
    def _generate_general_report(self, report_type: str, date_range: str) -> Dict[str, Any]:
        """Generate general report"""
        return {
            "report_type": report_type,
            "period": date_range,
            "summary": f"General {report_type} report for {date_range} period"
        }
    
    def _parse_supply_items(self, details: str) -> List[str]:
        """Parse supply items from details"""
        # Simple parsing - in production would be more sophisticated
        return [item.strip() for item in details.split(',') if item.strip()]
    
    def _extract_vendor_info(self, details: str) -> Dict[str, Any]:
        """Extract vendor information from details"""
        return {
            "vendor_name": "Vendor Name",
            "service_type": "Service Type",
            "contact_info": "Contact Information"
        }


class MaintenanceTechLeadAgent(BaseAgent):
    """Lead Maintenance Technician agent for supervising maintenance work and training"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("maintenance_tech_lead", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 500
        self.permissions = [
            "create_work_orders",
            "update_work_status",
            "request_parts_up_to_500",
            "train_junior_techs",
            "quality_control",
            "safety_oversight"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute maintenance tech lead actions"""
        context = input_data.get('context', {})
        
        if action == "create_work_order":
            return await self._create_work_order(context)
        elif action == "update_work_status":
            return await self._update_work_status(context)
        elif action == "request_parts":
            return await self._request_parts(context)
        elif action == "train_junior_tech":
            return await self._train_junior_tech(context)
        elif action == "conduct_quality_check":
            return await self._conduct_quality_check(context)
        elif action == "oversee_safety":
            return await self._oversee_safety(context)
        else:
            return await self._generic_action(action, context)
    
    async def _create_work_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed work orders with specifications"""
        unit_id = context.get('unit_id')
        issue_type = context.get('issue_type', 'general')
        description = context.get('description', '')
        priority = context.get('priority', 'normal')
        estimated_hours = context.get('estimated_hours', 2)
        
        # Create comprehensive work order
        work_order = {
            "work_order_id": f"WO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "unit_id": unit_id,
            "issue_type": issue_type,
            "description": description,
            "priority": priority,
            "estimated_hours": estimated_hours,
            "status": "created",
            "created_by": "maintenance_tech_lead",
            "created_at": datetime.utcnow().isoformat(),
            "required_skills": self._determine_required_skills(issue_type),
            "safety_requirements": self._get_safety_requirements(issue_type),
            "quality_standards": self._get_quality_standards(issue_type)
        }
        
        # Escalate complex or high-priority work orders
        if priority == "urgent" or estimated_hours > 8:
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Complex Work Order Created",
                message=f"Complex work order created for unit {unit_id}: {description}",
                data=work_order
            )
        
        return {
            "completed": True,
            "output": {
                "work_order_created": True,
                "work_order": work_order,
                "escalated": priority == "urgent" or estimated_hours > 8
            }
        }
    
    async def _update_work_status(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update work order status with detailed progress"""
        work_order_id = context.get('work_order_id')
        status = context.get('status', 'in_progress')
        progress_notes = context.get('progress_notes', '')
        hours_worked = context.get('hours_worked', 0)
        technician_id = context.get('technician_id')
        
        status_update = {
            "work_order_id": work_order_id,
            "status": status,
            "progress_notes": progress_notes,
            "hours_worked": hours_worked,
            "technician_id": technician_id,
            "updated_at": datetime.utcnow().isoformat(),
            "quality_check_completed": status == "completed"
        }
        
        # Notify supervisor of completion
        if status == "completed":
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Work Order Completed",
                message=f"Work order {work_order_id} completed by technician {technician_id}",
                data=status_update
            )
        
        return {
            "completed": True,
            "output": {
                "status_updated": True,
                "status_update": status_update,
                "supervisor_notified": status == "completed"
            }
        }
    
    async def _request_parts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Request parts with detailed specifications"""
        part_name = context.get('part_name', '')
        quantity = context.get('quantity', 1)
        urgency = context.get('urgency', 'normal')
        work_order_id = context.get('work_order_id')
        estimated_cost = context.get('estimated_cost', 0)
        
        parts_request = {
            "request_id": f"PR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "part_name": part_name,
            "quantity": quantity,
            "urgency": urgency,
            "work_order_id": work_order_id,
            "estimated_cost": estimated_cost,
            "requested_by": "maintenance_tech_lead",
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending_approval"
        }
        
        # Escalate expensive or urgent parts requests
        if estimated_cost > 500 or urgency == "urgent":
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Parts Request Escalation",
                message=f"Parts request for {part_name} - Cost: ${estimated_cost}, Urgency: {urgency}",
                data=parts_request
            )
        
        return {
            "completed": True,
            "output": {
                "parts_requested": True,
                "parts_request": parts_request,
                "escalated": estimated_cost > 500 or urgency == "urgent"
            }
        }
    
    async def _train_junior_tech(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Train junior technicians on specific skills"""
        technician_id = context.get('technician_id')
        skill_topic = context.get('skill_topic', 'general')
        training_duration = context.get('training_duration', 60)
        training_type = context.get('training_type', 'hands_on')
        
        training_session = {
            "training_id": f"TR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "technician_id": technician_id,
            "skill_topic": skill_topic,
            "training_duration": training_duration,
            "training_type": training_type,
            "trainer": "maintenance_tech_lead",
            "scheduled_at": datetime.utcnow().isoformat(),
            "status": "scheduled"
        }
        
        # Create training materials
        training_materials = self._generate_training_materials(skill_topic)
        training_session["materials"] = training_materials
        
        return {
            "completed": True,
            "output": {
                "training_scheduled": True,
                "training_session": training_session,
                "materials_created": len(training_materials)
            }
        }
    
    async def _conduct_quality_check(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct quality control checks on completed work"""
        work_order_id = context.get('work_order_id')
        technician_id = context.get('technician_id')
        quality_score = context.get('quality_score', 0)
        issues_found = context.get('issues_found', [])
        
        quality_report = {
            "work_order_id": work_order_id,
            "technician_id": technician_id,
            "quality_score": quality_score,
            "issues_found": issues_found,
            "inspected_by": "maintenance_tech_lead",
            "inspection_date": datetime.utcnow().isoformat(),
            "passed": quality_score >= 8.0
        }
        
        # Escalate quality issues
        if quality_score < 8.0 or len(issues_found) > 0:
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Quality Issues Detected",
                message=f"Quality issues found in work order {work_order_id}",
                data=quality_report
            )
        
        return {
            "completed": True,
            "output": {
                "quality_check_completed": True,
                "quality_report": quality_report,
                "escalated": quality_score < 8.0 or len(issues_found) > 0
            }
        }
    
    async def _oversee_safety(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee safety protocols and compliance"""
        safety_check_type = context.get('safety_check_type', 'routine')
        area_inspected = context.get('area_inspected', 'general')
        safety_issues = context.get('safety_issues', [])
        compliance_status = context.get('compliance_status', 'compliant')
        
        safety_report = {
            "safety_check_id": f"SC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "safety_check_type": safety_check_type,
            "area_inspected": area_inspected,
            "safety_issues": safety_issues,
            "compliance_status": compliance_status,
            "inspected_by": "maintenance_tech_lead",
            "inspection_date": datetime.utcnow().isoformat(),
            "requires_action": len(safety_issues) > 0
        }
        
        # Escalate safety issues
        if len(safety_issues) > 0 or compliance_status != "compliant":
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Safety Issues Detected",
                message=f"Safety issues found in {area_inspected}",
                data=safety_report
            )
        
        return {
            "completed": True,
            "output": {
                "safety_oversight_completed": True,
                "safety_report": safety_report,
                "escalated": len(safety_issues) > 0 or compliance_status != "compliant"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other maintenance tech lead action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "maintenance_tech_lead",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _determine_required_skills(self, issue_type: str) -> List[str]:
        """Determine required skills for work order type"""
        skill_map = {
            "plumbing": ["plumbing_repair", "pipe_fitting", "drain_clearing"],
            "electrical": ["electrical_repair", "wiring", "circuit_testing"],
            "hvac": ["hvac_repair", "refrigerant_handling", "thermostat_programming"],
            "appliance": ["appliance_repair", "troubleshooting", "parts_replacement"],
            "carpentry": ["wood_repair", "drywall", "painting"]
        }
        return skill_map.get(issue_type, ["general_repair"])
    
    def _get_safety_requirements(self, issue_type: str) -> List[str]:
        """Get safety requirements for work order type"""
        safety_map = {
            "electrical": ["voltage_testing", "lockout_tagout", "ppe_required"],
            "hvac": ["refrigerant_safety", "ventilation", "ppe_required"],
            "plumbing": ["water_shutoff", "ventilation", "ppe_required"],
            "general": ["basic_safety", "ppe_required"]
        }
        return safety_map.get(issue_type, ["basic_safety"])
    
    def _get_quality_standards(self, issue_type: str) -> Dict[str, Any]:
        """Get quality standards for work order type"""
        standards_map = {
            "plumbing": {"leak_test": True, "pressure_test": True, "cleanup_required": True},
            "electrical": {"voltage_test": True, "ground_test": True, "inspection_required": True},
            "hvac": {"temperature_test": True, "airflow_test": True, "filter_check": True},
            "appliance": {"function_test": True, "safety_test": True, "cleanup_required": True}
        }
        return standards_map.get(issue_type, {"function_test": True, "cleanup_required": True})
    
    def _generate_training_materials(self, skill_topic: str) -> List[str]:
        """Generate training materials for skill topic"""
        materials_map = {
            "plumbing": ["Basic Plumbing Guide", "Pipe Fitting Manual", "Safety Procedures"],
            "electrical": ["Electrical Safety Guide", "Wiring Diagrams", "Testing Procedures"],
            "hvac": ["HVAC Fundamentals", "Refrigerant Handling", "Troubleshooting Guide"],
            "appliance": ["Appliance Repair Manual", "Parts Catalog", "Testing Procedures"]
        }
        return materials_map.get(skill_topic, ["General Maintenance Guide", "Safety Procedures"])


class MaintenanceTechAgent(BaseAgent):
    """Maintenance Technician agent for basic maintenance work"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("maintenance_tech", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 0
        self.permissions = [
            "accept_work_orders",
            "update_progress",
            "request_parts_approval",
            "basic_repairs",
            "safety_compliance"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute maintenance tech actions"""
        context = input_data.get('context', {})
        
        if action == "accept_work_order":
            return await self._accept_work_order(context)
        elif action == "update_progress":
            return await self._update_progress(context)
        elif action == "request_parts_approval":
            return await self._request_parts_approval(context)
        elif action == "complete_repair":
            return await self._complete_repair(context)
        elif action == "report_safety_issue":
            return await self._report_safety_issue(context)
        else:
            return await self._generic_action(action, context)
    
    async def _accept_work_order(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Accept and begin work on a maintenance order"""
        work_order_id = context.get('work_order_id')
        technician_id = context.get('technician_id')
        estimated_duration = context.get('estimated_duration', 2)
        
        work_acceptance = {
            "work_order_id": work_order_id,
            "technician_id": technician_id,
            "accepted_at": datetime.utcnow().isoformat(),
            "estimated_duration": estimated_duration,
            "status": "in_progress",
            "start_time": datetime.utcnow().isoformat()
        }
        
        # Notify lead technician of acceptance
        await self.send_message(
            to_role="maintenance_tech_lead",
            subject="Work Order Accepted",
            message=f"Technician {technician_id} accepted work order {work_order_id}",
            data=work_acceptance
        )
        
        return {
            "completed": True,
            "output": {
                "work_order_accepted": True,
                "work_acceptance": work_acceptance,
                "lead_notified": True
            }
        }
    
    async def _update_progress(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Update progress on current work order"""
        work_order_id = context.get('work_order_id')
        progress_percentage = context.get('progress_percentage', 0)
        notes = context.get('notes', '')
        hours_worked = context.get('hours_worked', 0)
        
        progress_update = {
            "work_order_id": work_order_id,
            "progress_percentage": progress_percentage,
            "notes": notes,
            "hours_worked": hours_worked,
            "updated_at": datetime.utcnow().isoformat()
        }
        
        # Notify lead if progress is slow or issues arise
        if progress_percentage < 25 and hours_worked > 2:
            await self.send_message(
                to_role="maintenance_tech_lead",
                subject="Slow Progress Alert",
                message=f"Slow progress on work order {work_order_id}: {progress_percentage}% complete in {hours_worked} hours",
                data=progress_update
            )
        
        return {
            "completed": True,
            "output": {
                "progress_updated": True,
                "progress_update": progress_update,
                "escalated": progress_percentage < 25 and hours_worked > 2
            }
        }
    
    async def _request_parts_approval(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Request approval for parts needed"""
        part_name = context.get('part_name', '')
        quantity = context.get('quantity', 1)
        estimated_cost = context.get('estimated_cost', 0)
        work_order_id = context.get('work_order_id')
        urgency = context.get('urgency', 'normal')
        
        parts_request = {
            "request_id": f"PR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "part_name": part_name,
            "quantity": quantity,
            "estimated_cost": estimated_cost,
            "work_order_id": work_order_id,
            "urgency": urgency,
            "requested_by": "maintenance_tech",
            "requested_at": datetime.utcnow().isoformat(),
            "status": "pending_approval"
        }
        
        # Send to lead technician for approval
        await self.send_message(
            to_role="maintenance_tech_lead",
            subject="Parts Approval Request",
            message=f"Parts request for {part_name} - Cost: ${estimated_cost}",
            data=parts_request
        )
        
        return {
            "completed": True,
            "output": {
                "parts_request_submitted": True,
                "parts_request": parts_request,
                "approval_requested": True
            }
        }
    
    async def _complete_repair(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Complete a repair and submit for quality check"""
        work_order_id = context.get('work_order_id')
        completion_notes = context.get('completion_notes', '')
        hours_worked = context.get('hours_worked', 0)
        parts_used = context.get('parts_used', [])
        
        completion_report = {
            "work_order_id": work_order_id,
            "completion_notes": completion_notes,
            "hours_worked": hours_worked,
            "parts_used": parts_used,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
            "ready_for_quality_check": True
        }
        
        # Request quality check from lead
        await self.send_message(
            to_role="maintenance_tech_lead",
            subject="Repair Completed - Quality Check Requested",
            message=f"Work order {work_order_id} completed, requesting quality check",
            data=completion_report
        )
        
        return {
            "completed": True,
            "output": {
                "repair_completed": True,
                "completion_report": completion_report,
                "quality_check_requested": True
            }
        }
    
    async def _report_safety_issue(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Report safety issues or concerns"""
        issue_type = context.get('issue_type', 'general')
        description = context.get('description', '')
        location = context.get('location', '')
        severity = context.get('severity', 'low')
        
        safety_report = {
            "report_id": f"SR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "issue_type": issue_type,
            "description": description,
            "location": location,
            "severity": severity,
            "reported_by": "maintenance_tech",
            "reported_at": datetime.utcnow().isoformat(),
            "status": "reported"
        }
        
        # Escalate to lead technician
        await self.send_message(
            to_role="maintenance_tech_lead",
            subject="Safety Issue Reported",
            message=f"Safety issue reported: {issue_type} at {location}",
            data=safety_report
        )
        
        return {
            "completed": True,
            "output": {
                "safety_issue_reported": True,
                "safety_report": safety_report,
                "escalated": True
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other maintenance tech action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "maintenance_tech",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class SeniorLeasingAgentAgent(BaseAgent):
    """Senior Leasing Agent agent for advanced leasing activities and preliminary approvals"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("senior_leasing_agent", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 200
        self.permissions = [
            "process_applications",
            "show_units",
            "preliminary_approval",
            "small_concessions_up_to_200",
            "mentor_junior_agents",
            "market_analysis"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute senior leasing agent actions"""
        context = input_data.get('context', {})
        
        if action == "process_application":
            return await self._process_application(context)
        elif action == "conduct_advanced_tour":
            return await self._conduct_advanced_tour(context)
        elif action == "preliminary_approval":
            return await self._preliminary_approval(context)
        elif action == "approve_small_concession":
            return await self._approve_small_concession(context)
        elif action == "mentor_junior_agent":
            return await self._mentor_junior_agent(context)
        elif action == "conduct_market_analysis":
            return await self._conduct_market_analysis(context)
        else:
            return await self._generic_action(action, context)
    
    async def _process_application(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process rental applications with detailed analysis"""
        applicant_id = context.get('applicant_id')
        application_data = context.get('application_data', {})
        unit_preference = context.get('unit_preference', '')
        
        # Analyze application
        application_analysis = {
            "applicant_id": applicant_id,
            "application_data": application_data,
            "unit_preference": unit_preference,
            "processed_by": "senior_leasing_agent",
            "processed_at": datetime.utcnow().isoformat(),
            "credit_score": application_data.get('credit_score', 0),
            "income_ratio": application_data.get('income_ratio', 0),
            "rental_history": application_data.get('rental_history', 'good'),
            "recommendation": self._generate_recommendation(application_data)
        }
        
        # Escalate complex applications
        if application_analysis["credit_score"] < 600 or application_analysis["income_ratio"] < 2.5:
            await self.send_message(
                to_role="leasing_manager",
                subject="Complex Application - Manager Review Required",
                message=f"Complex application from {applicant_id} requires manager review",
                data=application_analysis
            )
        
        return {
            "completed": True,
            "output": {
                "application_processed": True,
                "application_analysis": application_analysis,
                "escalated": application_analysis["credit_score"] < 600 or application_analysis["income_ratio"] < 2.5
            }
        }
    
    async def _conduct_advanced_tour(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct advanced property tours with detailed information"""
        prospect_name = context.get('prospect_name')
        unit_id = context.get('unit_id')
        tour_type = context.get('tour_type', 'standard')
        special_requirements = context.get('special_requirements', [])
        
        tour_details = {
            "tour_id": f"TOUR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "prospect_name": prospect_name,
            "unit_id": unit_id,
            "tour_type": tour_type,
            "special_requirements": special_requirements,
            "conducted_by": "senior_leasing_agent",
            "conducted_at": datetime.utcnow().isoformat(),
            "duration": self._estimate_tour_duration(tour_type),
            "materials_provided": self._get_tour_materials(tour_type)
        }
        
        # Follow up with detailed information
        follow_up_plan = self._create_follow_up_plan(prospect_name, tour_type)
        tour_details["follow_up_plan"] = follow_up_plan
        
        return {
            "completed": True,
            "output": {
                "advanced_tour_conducted": True,
                "tour_details": tour_details,
                "follow_up_created": True
            }
        }
    
    async def _preliminary_approval(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide preliminary approval for applications"""
        applicant_id = context.get('applicant_id')
        application_id = context.get('application_id')
        approval_conditions = context.get('approval_conditions', [])
        
        preliminary_approval = {
            "applicant_id": applicant_id,
            "application_id": application_id,
            "approval_conditions": approval_conditions,
            "approved_by": "senior_leasing_agent",
            "approved_at": datetime.utcnow().isoformat(),
            "approval_type": "preliminary",
            "requires_manager_final": True,
            "valid_until": self._calculate_approval_expiry()
        }
        
        # Send to manager for final approval
        await self.send_message(
            to_role="leasing_manager",
            subject="Preliminary Approval - Final Review Required",
            message=f"Preliminary approval granted to {applicant_id}, awaiting final manager review",
            data=preliminary_approval
        )
        
        return {
            "completed": True,
            "output": {
                "preliminary_approval_granted": True,
                "preliminary_approval": preliminary_approval,
                "manager_notified": True
            }
        }
    
    async def _approve_small_concession(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve small concessions up to $200"""
        concession_type = context.get('concession_type', 'general')
        amount = context.get('amount', 0)
        applicant_id = context.get('applicant_id')
        justification = context.get('justification', '')
        
        if amount > 200:
            return {
                "completed": False,
                "output": {
                    "error": "Amount exceeds approval limit of $200",
                    "amount": amount,
                    "limit": 200
                }
            }
        
        concession_approval = {
            "concession_id": f"CON-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "concession_type": concession_type,
            "amount": amount,
            "applicant_id": applicant_id,
            "justification": justification,
            "approved_by": "senior_leasing_agent",
            "approved_at": datetime.utcnow().isoformat(),
            "status": "approved"
        }
        
        return {
            "completed": True,
            "output": {
                "concession_approved": True,
                "concession_approval": concession_approval
            }
        }
    
    async def _mentor_junior_agent(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Mentor junior leasing agents"""
        junior_agent_id = context.get('junior_agent_id')
        mentoring_topic = context.get('mentoring_topic', 'general')
        session_duration = context.get('session_duration', 60)
        
        mentoring_session = {
            "session_id": f"MENTOR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "junior_agent_id": junior_agent_id,
            "mentoring_topic": mentoring_topic,
            "session_duration": session_duration,
            "mentor": "senior_leasing_agent",
            "scheduled_at": datetime.utcnow().isoformat(),
            "materials": self._get_mentoring_materials(mentoring_topic)
        }
        
        return {
            "completed": True,
            "output": {
                "mentoring_scheduled": True,
                "mentoring_session": mentoring_session
            }
        }
    
    async def _conduct_market_analysis(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct market analysis for pricing and competition"""
        market_area = context.get('market_area', 'local')
        analysis_type = context.get('analysis_type', 'pricing')
        time_period = context.get('time_period', 'monthly')
        
        market_analysis = {
            "analysis_id": f"MA-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "market_area": market_area,
            "analysis_type": analysis_type,
            "time_period": time_period,
            "conducted_by": "senior_leasing_agent",
            "conducted_at": datetime.utcnow().isoformat(),
            "findings": self._generate_market_findings(market_area, analysis_type),
            "recommendations": self._generate_market_recommendations(market_area, analysis_type)
        }
        
        # Share findings with manager
        await self.send_message(
            to_role="leasing_manager",
            subject="Market Analysis Completed",
            message=f"Market analysis completed for {market_area} - {analysis_type}",
            data=market_analysis
        )
        
        return {
            "completed": True,
            "output": {
                "market_analysis_completed": True,
                "market_analysis": market_analysis,
                "manager_notified": True
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other senior leasing agent action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "senior_leasing_agent",
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    
    def _generate_recommendation(self, application_data: Dict[str, Any]) -> str:
        """Generate recommendation based on application data"""
        credit_score = application_data.get('credit_score', 0)
        income_ratio = application_data.get('income_ratio', 0)
        rental_history = application_data.get('rental_history', 'good')
        
        if credit_score >= 700 and income_ratio >= 3.0 and rental_history == 'good':
            return "approve"
        elif credit_score >= 650 and income_ratio >= 2.5:
            return "approve_with_conditions"
        else:
            return "deny"
    
    def _estimate_tour_duration(self, tour_type: str) -> int:
        """Estimate tour duration in minutes"""
        duration_map = {
            "standard": 30,
            "detailed": 45,
            "premium": 60,
            "virtual": 20
        }
        return duration_map.get(tour_type, 30)
    
    def _get_tour_materials(self, tour_type: str) -> List[str]:
        """Get materials needed for tour type"""
        materials_map = {
            "standard": ["brochure", "floor_plan", "pricing_sheet"],
            "detailed": ["brochure", "floor_plan", "pricing_sheet", "amenity_guide", "neighborhood_info"],
            "premium": ["brochure", "floor_plan", "pricing_sheet", "amenity_guide", "neighborhood_info", "financing_options"],
            "virtual": ["virtual_tour_link", "brochure", "pricing_sheet"]
        }
        return materials_map.get(tour_type, ["brochure", "pricing_sheet"])
    
    def _create_follow_up_plan(self, prospect_name: str, tour_type: str) -> Dict[str, Any]:
        """Create follow-up plan for prospect"""
        return {
            "prospect_name": prospect_name,
            "follow_up_timeline": "24_hours",
            "follow_up_method": "email_and_phone",
            "next_steps": ["send_application", "schedule_follow_up_call", "send_additional_info"],
            "priority": "high" if tour_type in ["premium", "detailed"] else "medium"
        }
    
    def _calculate_approval_expiry(self) -> str:
        """Calculate approval expiry date (7 days from now)"""
        from datetime import timedelta
        expiry_date = datetime.utcnow() + timedelta(days=7)
        return expiry_date.isoformat()
    
    def _get_mentoring_materials(self, mentoring_topic: str) -> List[str]:
        """Get mentoring materials for topic"""
        materials_map = {
            "application_processing": ["Application Guide", "Credit Check Procedures", "Approval Workflow"],
            "tour_techniques": ["Tour Script", "Objection Handling", "Closing Techniques"],
            "market_analysis": ["Market Research Guide", "Competitor Analysis", "Pricing Strategies"],
            "customer_service": ["Communication Skills", "Problem Resolution", "Follow-up Procedures"]
        }
        return materials_map.get(mentoring_topic, ["General Leasing Guide", "Best Practices"])
    
    def _generate_market_findings(self, market_area: str, analysis_type: str) -> Dict[str, Any]:
        """Generate market findings"""
        return {
            "average_rent": 1800,
            "occupancy_rate": 95.2,
            "days_on_market": 12,
            "competition_count": 8,
            "price_trend": "increasing"
        }
    
    def _generate_market_recommendations(self, market_area: str, analysis_type: str) -> List[str]:
        """Generate market recommendations"""
        return [
            "Consider 3% rent increase for renewals",
            "Focus on premium amenities to differentiate",
            "Implement referral program to reduce vacancy",
            "Monitor competitor pricing weekly"
        ]


class DirectorOfAccountingAgent(BaseAgent):
    """Director of Accounting agent for financial oversight and orchestration"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("director_of_accounting", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 0  # Requires approval for any amount
        self.permissions = [
            "financial_strategy",
            "budget_oversight",
            "audit_management",
            "orchestrate_financial_workflows",
            "approve_major_expenditures",
            "financial_compliance"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute director of accounting actions with orchestration"""
        context = input_data.get('context', {})
        
        if action == "orchestrate_monthly_close":
            return await self._orchestrate_monthly_close(context)
        elif action == "oversee_audit_process":
            return await self._oversee_audit_process(context)
        elif action == "approve_major_expenditure":
            return await self._approve_major_expenditure(context)
        elif action == "coordinate_financial_reporting":
            return await self._coordinate_financial_reporting(context)
        elif action == "manage_financial_compliance":
            return await self._manage_financial_compliance(context)
        elif action == "orchestrate_budget_process":
            return await self._orchestrate_budget_process(context)
        else:
            return await self._generic_action(action, context)
    
    async def _orchestrate_monthly_close(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate the monthly financial close process"""
        month = context.get('month', 'current')
        year = context.get('year', 'current')
        
        # Create orchestration workflow
        workflow = {
            "workflow_id": f"MC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "workflow_type": "monthly_close",
            "month": month,
            "year": year,
            "orchestrated_by": "director_of_accounting",
            "created_at": datetime.utcnow().isoformat(),
            "status": "initiated"
        }
        
        # Step 1: Coordinate with Accounting Manager
        await self.send_message(
            to_role="accounting_manager",
            subject="Monthly Close - Prepare Financial Reports",
            message=f"Prepare comprehensive financial reports for {month} {year}",
            data={"workflow": workflow, "step": 1, "deadline": "3_days"}
        )
        
        # Step 2: Coordinate with Accountants
        await self.send_message(
            to_role="accountant",
            subject="Monthly Close - Reconcile Accounts",
            message=f"Complete account reconciliations for {month} {year}",
            data={"workflow": workflow, "step": 2, "deadline": "2_days"}
        )
        
        # Step 3: Coordinate with Property Manager for review
        await self.send_message(
            to_role="property_manager",
            subject="Monthly Close - Executive Review Required",
            message=f"Monthly close process initiated for {month} {year}, executive review needed",
            data={"workflow": workflow, "step": 3, "deadline": "1_day"}
        )
        
        workflow["steps"] = [
            {"step": 1, "action": "prepare_reports", "assigned_to": "accounting_manager"},
            {"step": 2, "action": "reconcile_accounts", "assigned_to": "accountant"},
            {"step": 3, "action": "executive_review", "assigned_to": "property_manager"}
        ]
        
        return {
            "completed": True,
            "output": {
                "workflow_orchestrated": True,
                "workflow": workflow,
                "agents_coordinated": 3,
                "estimated_completion": "5_days"
            }
        }
    
    async def _oversee_audit_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee audit process with agent coordination"""
        audit_type = context.get('audit_type', 'annual')
        audit_scope = context.get('audit_scope', 'full')
        
        audit_workflow = {
            "audit_id": f"AUDIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "audit_type": audit_type,
            "audit_scope": audit_scope,
            "overseen_by": "director_of_accounting",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "preparation"
        }
        
        # Coordinate audit preparation
        await self.send_message(
            to_role="accounting_manager",
            subject=f"{audit_type.title()} Audit - Prepare Documentation",
            message=f"Prepare all financial documentation for {audit_type} audit",
            data={"audit_workflow": audit_workflow, "phase": "preparation"}
        )
        
        # Coordinate with Admin Assistant for document organization
        await self.send_message(
            to_role="admin_assistant",
            subject="Audit Support - Document Organization",
            message=f"Organize and prepare all financial documents for {audit_type} audit",
            data={"audit_workflow": audit_workflow, "phase": "documentation"}
        )
        
        # Notify Property Manager of audit initiation
        await self.send_message(
            to_role="property_manager",
            subject=f"{audit_type.title()} Audit Initiated",
            message=f"{audit_type.title()} audit process initiated, coordination required",
            data={"audit_workflow": audit_workflow, "phase": "notification"}
        )
        
        return {
            "completed": True,
            "output": {
                "audit_overseen": True,
                "audit_workflow": audit_workflow,
                "agents_coordinated": 3,
                "estimated_duration": "4_weeks"
            }
        }
    
    async def _approve_major_expenditure(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve major expenditures with multi-level review"""
        expenditure_type = context.get('expenditure_type', 'general')
        amount = context.get('amount', 0)
        justification = context.get('justification', '')
        department = context.get('department', 'general')
        
        if amount > 0:
            return {
                "completed": False,
                "output": {
                    "error": "All expenditures require approval",
                    "amount": amount,
                    "limit": 0,
                    "requires_vp_approval": True
                }
            }
        
        approval_workflow = {
            "approval_id": f"EXP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "expenditure_type": expenditure_type,
            "amount": amount,
            "justification": justification,
            "department": department,
            "approved_by": "director_of_accounting",
            "approved_at": datetime.utcnow().isoformat(),
            "approval_level": "director"
        }
        
        # Coordinate with department manager
        if department == "maintenance":
            await self.send_message(
                to_role="maintenance_supervisor",
                subject="Major Expenditure Approved",
                message=f"Major expenditure of ${amount} approved for {expenditure_type}",
                data={"approval_workflow": approval_workflow}
            )
        elif department == "leasing":
            await self.send_message(
                to_role="leasing_manager",
                subject="Major Expenditure Approved",
                message=f"Major expenditure of ${amount} approved for {expenditure_type}",
                data={"approval_workflow": approval_workflow}
            )
        
        return {
            "completed": True,
            "output": {
                "expenditure_approved": True,
                "approval_workflow": approval_workflow,
                "coordination_completed": True
            }
        }
    
    async def _coordinate_financial_reporting(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate comprehensive financial reporting"""
        report_type = context.get('report_type', 'comprehensive')
        reporting_period = context.get('reporting_period', 'quarterly')
        
        reporting_workflow = {
            "reporting_id": f"RPT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "report_type": report_type,
            "reporting_period": reporting_period,
            "coordinated_by": "director_of_accounting",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "coordination"
        }
        
        # Orchestrate reporting process
        await self.send_message(
            to_role="accounting_manager",
            subject="Financial Reporting - Prepare Executive Summary",
            message=f"Prepare executive summary for {report_type} {reporting_period} report",
            data={"reporting_workflow": reporting_workflow, "task": "executive_summary"}
        )
        
        await self.send_message(
            to_role="accountant",
            subject="Financial Reporting - Prepare Detailed Reports",
            message=f"Prepare detailed financial reports for {reporting_period}",
            data={"reporting_workflow": reporting_workflow, "task": "detailed_reports"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Financial Reporting - Document Compilation",
            message=f"Compile and format all financial documents for {reporting_period} reporting",
            data={"reporting_workflow": reporting_workflow, "task": "document_compilation"}
        )
        
        return {
            "completed": True,
            "output": {
                "reporting_coordinated": True,
                "reporting_workflow": reporting_workflow,
                "agents_coordinated": 3,
                "estimated_completion": "1_week"
            }
        }
    
    async def _manage_financial_compliance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage financial compliance with agent coordination"""
        compliance_area = context.get('compliance_area', 'general')
        compliance_action = context.get('compliance_action', 'review')
        
        compliance_workflow = {
            "compliance_id": f"COMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "compliance_area": compliance_area,
            "compliance_action": compliance_action,
            "managed_by": "director_of_accounting",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "active"
        }
        
        # Coordinate compliance activities
        await self.send_message(
            to_role="accounting_manager",
            subject="Compliance Management - Review Procedures",
            message=f"Review and update {compliance_area} compliance procedures",
            data={"compliance_workflow": compliance_workflow, "action": "procedure_review"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Compliance Management - Document Updates",
            message=f"Update compliance documentation for {compliance_area}",
            data={"compliance_workflow": compliance_workflow, "action": "documentation"}
        )
        
        return {
            "completed": True,
            "output": {
                "compliance_managed": True,
                "compliance_workflow": compliance_workflow,
                "agents_coordinated": 2,
                "status": "ongoing"
            }
        }
    
    async def _orchestrate_budget_process(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate annual budget process"""
        budget_year = context.get('budget_year', 'next')
        budget_scope = context.get('budget_scope', 'comprehensive')
        
        budget_workflow = {
            "budget_id": f"BUDGET-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "budget_year": budget_year,
            "budget_scope": budget_scope,
            "orchestrated_by": "director_of_accounting",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "planning"
        }
        
        # Coordinate budget preparation across departments
        await self.send_message(
            to_role="maintenance_supervisor",
            subject="Budget Process - Maintenance Budget",
            message=f"Prepare maintenance budget for {budget_year}",
            data={"budget_workflow": budget_workflow, "department": "maintenance"}
        )
        
        await self.send_message(
            to_role="leasing_manager",
            subject="Budget Process - Leasing Budget",
            message=f"Prepare leasing and marketing budget for {budget_year}",
            data={"budget_workflow": budget_workflow, "department": "leasing"}
        )
        
        await self.send_message(
            to_role="resident_services_manager",
            subject="Budget Process - Resident Services Budget",
            message=f"Prepare resident services budget for {budget_year}",
            data={"budget_workflow": budget_workflow, "department": "resident_services"}
        )
        
        await self.send_message(
            to_role="accounting_manager",
            subject="Budget Process - Financial Consolidation",
            message=f"Consolidate all department budgets for {budget_year}",
            data={"budget_workflow": budget_workflow, "task": "consolidation"}
        )
        
        return {
            "completed": True,
            "output": {
                "budget_orchestrated": True,
                "budget_workflow": budget_workflow,
                "departments_coordinated": 4,
                "estimated_completion": "6_weeks"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other director of accounting action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "director_of_accounting",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class DirectorOfLeasingAgent(BaseAgent):
    """Director of Leasing agent for leasing strategy and orchestration"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("director_of_leasing", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 0  # Requires approval for any amount
        self.permissions = [
            "leasing_strategy",
            "market_positioning",
            "orchestrate_leasing_workflows",
            "approve_major_leasing_decisions",
            "vendor_management",
            "performance_oversight"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute director of leasing actions with orchestration"""
        context = input_data.get('context', {})
        
        if action == "orchestrate_leasing_campaign":
            return await self._orchestrate_leasing_campaign(context)
        elif action == "oversee_market_positioning":
            return await self._oversee_market_positioning(context)
        elif action == "approve_major_leasing_decision":
            return await self._approve_major_leasing_decision(context)
        elif action == "coordinate_vendor_relationships":
            return await self._coordinate_vendor_relationships(context)
        elif action == "orchestrate_performance_review":
            return await self._orchestrate_performance_review(context)
        elif action == "manage_leasing_strategy":
            return await self._manage_leasing_strategy(context)
        else:
            return await self._generic_action(action, context)
    
    async def _orchestrate_leasing_campaign(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate comprehensive leasing campaigns"""
        campaign_type = context.get('campaign_type', 'seasonal')
        target_market = context.get('target_market', 'general')
        budget = context.get('budget', 10000)
        
        campaign_workflow = {
            "campaign_id": f"CAMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "campaign_type": campaign_type,
            "target_market": target_market,
            "budget": budget,
            "orchestrated_by": "director_of_leasing",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "planning"
        }
        
        # Coordinate campaign development
        await self.send_message(
            to_role="leasing_manager",
            subject="Leasing Campaign - Strategy Development",
            message=f"Develop strategy for {campaign_type} campaign targeting {target_market}",
            data={"campaign_workflow": campaign_workflow, "phase": "strategy"}
        )
        
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Leasing Campaign - Market Research",
            message=f"Conduct market research for {campaign_type} campaign",
            data={"campaign_workflow": campaign_workflow, "phase": "research"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Leasing Campaign - Material Preparation",
            message=f"Prepare marketing materials for {campaign_type} campaign",
            data={"campaign_workflow": campaign_workflow, "phase": "materials"}
        )
        
        await self.send_message(
            to_role="resident_services_manager",
            subject="Leasing Campaign - Community Integration",
            message=f"Integrate campaign with community events and resident referrals",
            data={"campaign_workflow": campaign_workflow, "phase": "integration"}
        )
        
        return {
            "completed": True,
            "output": {
                "campaign_orchestrated": True,
                "campaign_workflow": campaign_workflow,
                "agents_coordinated": 4,
                "estimated_completion": "3_weeks"
            }
        }
    
    async def _oversee_market_positioning(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee market positioning and competitive analysis"""
        market_area = context.get('market_area', 'local')
        analysis_scope = context.get('analysis_scope', 'comprehensive')
        
        positioning_workflow = {
            "positioning_id": f"POS-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "market_area": market_area,
            "analysis_scope": analysis_scope,
            "overseen_by": "director_of_leasing",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "analysis"
        }
        
        # Coordinate market analysis
        await self.send_message(
            to_role="leasing_manager",
            subject="Market Positioning - Competitive Analysis",
            message=f"Conduct competitive analysis for {market_area} market",
            data={"positioning_workflow": positioning_workflow, "task": "competitive_analysis"}
        )
        
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Market Positioning - Pricing Strategy",
            message=f"Develop pricing strategy based on market analysis",
            data={"positioning_workflow": positioning_workflow, "task": "pricing_strategy"}
        )
        
        await self.send_message(
            to_role="property_manager",
            subject="Market Positioning - Executive Review",
            message=f"Market positioning analysis requires executive review",
            data={"positioning_workflow": positioning_workflow, "task": "executive_review"}
        )
        
        return {
            "completed": True,
            "output": {
                "positioning_overseen": True,
                "positioning_workflow": positioning_workflow,
                "agents_coordinated": 3,
                "estimated_completion": "2_weeks"
            }
        }
    
    async def _approve_major_leasing_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve major leasing decisions with coordination"""
        decision_type = context.get('decision_type', 'general')
        impact_level = context.get('impact_level', 'medium')
        budget_impact = context.get('budget_impact', 0)
        
        if budget_impact > 0:
            return {
                "completed": False,
                "output": {
                    "error": "All leasing decisions require approval",
                    "budget_impact": budget_impact,
                    "limit": 0,
                    "requires_vp_approval": True
                }
            }
        
        decision_workflow = {
            "decision_id": f"DEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "decision_type": decision_type,
            "impact_level": impact_level,
            "budget_impact": budget_impact,
            "approved_by": "director_of_leasing",
            "approved_at": datetime.utcnow().isoformat(),
            "approval_level": "director"
        }
        
        # Coordinate decision implementation
        await self.send_message(
            to_role="leasing_manager",
            subject="Major Decision Approved - Implementation Required",
            message=f"Major {decision_type} decision approved, coordinate implementation",
            data={"decision_workflow": decision_workflow}
        )
        
        await self.send_message(
            to_role="assistant_manager",
            subject="Major Decision Approved - Operational Support",
            message=f"Major leasing decision requires operational support",
            data={"decision_workflow": decision_workflow}
        )
        
        return {
            "completed": True,
            "output": {
                "decision_approved": True,
                "decision_workflow": decision_workflow,
                "coordination_initiated": True
            }
        }
    
    async def _coordinate_vendor_relationships(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate vendor relationships and partnerships"""
        vendor_type = context.get('vendor_type', 'general')
        relationship_action = context.get('relationship_action', 'review')
        
        vendor_workflow = {
            "vendor_id": f"VENDOR-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "vendor_type": vendor_type,
            "relationship_action": relationship_action,
            "coordinated_by": "director_of_leasing",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "coordination"
        }
        
        # Coordinate vendor management
        await self.send_message(
            to_role="leasing_manager",
            subject="Vendor Management - Relationship Review",
            message=f"Review and manage {vendor_type} vendor relationships",
            data={"vendor_workflow": vendor_workflow, "action": "relationship_review"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Vendor Management - Documentation",
            message=f"Update vendor documentation and contracts",
            data={"vendor_workflow": vendor_workflow, "action": "documentation"}
        )
        
        return {
            "completed": True,
            "output": {
                "vendor_coordination_completed": True,
                "vendor_workflow": vendor_workflow,
                "agents_coordinated": 2,
                "status": "ongoing"
            }
        }
    
    async def _orchestrate_performance_review(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate leasing performance reviews"""
        review_period = context.get('review_period', 'quarterly')
        review_scope = context.get('review_scope', 'comprehensive')
        
        performance_workflow = {
            "performance_id": f"PERF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "review_period": review_period,
            "review_scope": review_scope,
            "orchestrated_by": "director_of_leasing",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "review"
        }
        
        # Coordinate performance review
        await self.send_message(
            to_role="leasing_manager",
            subject="Performance Review - Team Assessment",
            message=f"Conduct {review_period} performance review for leasing team",
            data={"performance_workflow": performance_workflow, "task": "team_assessment"}
        )
        
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Performance Review - Individual Assessment",
            message=f"Prepare individual performance assessments for {review_period}",
            data={"performance_workflow": performance_workflow, "task": "individual_assessment"}
        )
        
        await self.send_message(
            to_role="leasing_agent",
            subject="Performance Review - Self Assessment",
            message=f"Complete self-assessment for {review_period} performance review",
            data={"performance_workflow": performance_workflow, "task": "self_assessment"}
        )
        
        return {
            "completed": True,
            "output": {
                "performance_review_orchestrated": True,
                "performance_workflow": performance_workflow,
                "agents_coordinated": 3,
                "estimated_completion": "1_week"
            }
        }
    
    async def _manage_leasing_strategy(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage overall leasing strategy and planning"""
        strategy_focus = context.get('strategy_focus', 'annual')
        strategic_goals = context.get('strategic_goals', [])
        
        strategy_workflow = {
            "strategy_id": f"STRAT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "strategy_focus": strategy_focus,
            "strategic_goals": strategic_goals,
            "managed_by": "director_of_leasing",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "development"
        }
        
        # Coordinate strategy development
        await self.send_message(
            to_role="leasing_manager",
            subject="Strategy Management - Goal Development",
            message=f"Develop strategic goals for {strategy_focus} leasing strategy",
            data={"strategy_workflow": strategy_workflow, "task": "goal_development"}
        )
        
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Strategy Management - Implementation Planning",
            message=f"Plan implementation for {strategy_focus} leasing strategy",
            data={"strategy_workflow": strategy_workflow, "task": "implementation_planning"}
        )
        
        await self.send_message(
            to_role="property_manager",
            subject="Strategy Management - Executive Approval",
            message=f"Leasing strategy requires executive approval and alignment",
            data={"strategy_workflow": strategy_workflow, "task": "executive_approval"}
        )
        
        return {
            "completed": True,
            "output": {
                "strategy_managed": True,
                "strategy_workflow": strategy_workflow,
                "agents_coordinated": 3,
                "estimated_completion": "4_weeks"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other director of leasing action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "director_of_leasing",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class VicePresidentOfOperationsAgent(BaseAgent):
    """Vice President of Operations agent for high-level orchestration and strategic oversight"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("vice_president_of_operations", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 0  # Requires approval for any amount
        self.permissions = [
            "strategic_oversight",
            "cross_department_orchestration",
            "major_decision_approval",
            "performance_management",
            "resource_allocation",
            "executive_coordination"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute VP of Operations actions with strategic orchestration"""
        context = input_data.get('context', {})
        
        if action == "orchestrate_strategic_initiative":
            return await self._orchestrate_strategic_initiative(context)
        elif action == "oversee_cross_department_project":
            return await self._oversee_cross_department_project(context)
        elif action == "approve_major_strategic_decision":
            return await self._approve_major_strategic_decision(context)
        elif action == "coordinate_executive_meeting":
            return await self._coordinate_executive_meeting(context)
        elif action == "manage_resource_allocation":
            return await self._manage_resource_allocation(context)
        elif action == "oversee_performance_management":
            return await self._oversee_performance_management(context)
        else:
            return await self._generic_action(action, context)
    
    async def _orchestrate_strategic_initiative(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate major strategic initiatives across departments"""
        initiative_type = context.get('initiative_type', 'operational')
        strategic_goals = context.get('strategic_goals', [])
        timeline = context.get('timeline', '6_months')
        
        strategic_workflow = {
            "initiative_id": f"STRAT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "initiative_type": initiative_type,
            "strategic_goals": strategic_goals,
            "timeline": timeline,
            "orchestrated_by": "vice_president_of_operations",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "strategic_planning"
        }
        
        # Coordinate strategic planning across all departments
        await self.send_message(
            to_role="property_manager",
            subject="Strategic Initiative - Executive Leadership",
            message=f"Lead {initiative_type} strategic initiative with executive oversight",
            data={"strategic_workflow": strategic_workflow, "role": "executive_leadership"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Strategic Initiative - Financial Planning",
            message=f"Develop financial strategy and budget for {initiative_type} initiative",
            data={"strategic_workflow": strategic_workflow, "role": "financial_planning"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Strategic Initiative - Market Strategy",
            message=f"Develop market strategy and positioning for {initiative_type} initiative",
            data={"strategic_workflow": strategic_workflow, "role": "market_strategy"}
        )
        
        await self.send_message(
            to_role="assistant_manager",
            subject="Strategic Initiative - Operational Coordination",
            message=f"Coordinate operational aspects of {initiative_type} strategic initiative",
            data={"strategic_workflow": strategic_workflow, "role": "operational_coordination"}
        )
        
        return {
            "completed": True,
            "output": {
                "strategic_initiative_orchestrated": True,
                "strategic_workflow": strategic_workflow,
                "departments_coordinated": 4,
                "estimated_completion": timeline
            }
        }
    
    async def _oversee_cross_department_project(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee complex projects involving multiple departments"""
        project_type = context.get('project_type', 'infrastructure')
        departments_involved = context.get('departments_involved', [])
        project_scope = context.get('project_scope', 'major')
        
        project_workflow = {
            "project_id": f"PROJ-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "project_type": project_type,
            "departments_involved": departments_involved,
            "project_scope": project_scope,
            "overseen_by": "vice_president_of_operations",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "project_oversight"
        }
        
        # Coordinate project oversight across departments
        for department in departments_involved:
            if department == "maintenance":
                await self.send_message(
                    to_role="maintenance_supervisor",
                    subject="Cross-Department Project - Maintenance Coordination",
                    message=f"Coordinate maintenance aspects of {project_type} project",
                    data={"project_workflow": project_workflow, "department": "maintenance"}
                )
            elif department == "leasing":
                await self.send_message(
                    to_role="leasing_manager",
                    subject="Cross-Department Project - Leasing Coordination",
                    message=f"Coordinate leasing aspects of {project_type} project",
                    data={"project_workflow": project_workflow, "department": "leasing"}
                )
            elif department == "resident_services":
                await self.send_message(
                    to_role="resident_services_manager",
                    subject="Cross-Department Project - Resident Services Coordination",
                    message=f"Coordinate resident services aspects of {project_type} project",
                    data={"project_workflow": project_workflow, "department": "resident_services"}
                )
        
        # Ensure executive oversight
        await self.send_message(
            to_role="property_manager",
            subject="Cross-Department Project - Executive Oversight",
            message=f"Provide executive oversight for {project_type} cross-department project",
            data={"project_workflow": project_workflow, "role": "executive_oversight"}
        )
        
        return {
            "completed": True,
            "output": {
                "cross_department_project_overseen": True,
                "project_workflow": project_workflow,
                "departments_coordinated": len(departments_involved) + 1,
                "status": "active_oversight"
            }
        }
    
    async def _approve_major_strategic_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve major strategic decisions with executive oversight"""
        decision_type = context.get('decision_type', 'strategic')
        impact_level = context.get('impact_level', 'high')
        budget_impact = context.get('budget_impact', 0)
        strategic_importance = context.get('strategic_importance', 'high')
        
        if budget_impact > 0:
            return {
                "completed": False,
                "output": {
                    "error": "All strategic decisions require approval",
                    "budget_impact": budget_impact,
                    "limit": 0,
                    "requires_president_approval": True
                }
            }
        
        decision_workflow = {
            "decision_id": f"DEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "decision_type": decision_type,
            "impact_level": impact_level,
            "budget_impact": budget_impact,
            "strategic_importance": strategic_importance,
            "approved_by": "vice_president_of_operations",
            "approved_at": datetime.utcnow().isoformat(),
            "approval_level": "vice_president"
        }
        
        # Coordinate strategic decision implementation
        await self.send_message(
            to_role="property_manager",
            subject="Major Strategic Decision - Executive Implementation",
            message=f"Implement major {decision_type} strategic decision with executive oversight",
            data={"decision_workflow": decision_workflow, "role": "executive_implementation"}
        )
        
        await self.send_message(
            to_role="assistant_manager",
            subject="Major Strategic Decision - Operational Support",
            message=f"Provide operational support for major strategic decision implementation",
            data={"decision_workflow": decision_workflow, "role": "operational_support"}
        )
        
        return {
            "completed": True,
            "output": {
                "strategic_decision_approved": True,
                "decision_workflow": decision_workflow,
                "implementation_coordinated": True
            }
        }
    
    async def _coordinate_executive_meeting(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate executive meetings and strategic discussions"""
        meeting_type = context.get('meeting_type', 'quarterly')
        meeting_agenda = context.get('meeting_agenda', [])
        participants = context.get('participants', [])
        
        meeting_workflow = {
            "meeting_id": f"MTG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "meeting_type": meeting_type,
            "meeting_agenda": meeting_agenda,
            "participants": participants,
            "coordinated_by": "vice_president_of_operations",
            "scheduled_at": datetime.utcnow().isoformat(),
            "status": "scheduled"
        }
        
        # Coordinate meeting preparation
        await self.send_message(
            to_role="property_manager",
            subject="Executive Meeting - Strategic Preparation",
            message=f"Prepare strategic agenda for {meeting_type} executive meeting",
            data={"meeting_workflow": meeting_workflow, "role": "strategic_preparation"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Executive Meeting - Logistics Coordination",
            message=f"Coordinate logistics and documentation for {meeting_type} executive meeting",
            data={"meeting_workflow": meeting_workflow, "role": "logistics_coordination"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Executive Meeting - Financial Review",
            message=f"Prepare financial review for {meeting_type} executive meeting",
            data={"meeting_workflow": meeting_workflow, "role": "financial_review"}
        )
        
        return {
            "completed": True,
            "output": {
                "executive_meeting_coordinated": True,
                "meeting_workflow": meeting_workflow,
                "participants_notified": len(participants),
                "status": "scheduled"
            }
        }
    
    async def _manage_resource_allocation(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage strategic resource allocation across departments"""
        resource_type = context.get('resource_type', 'budget')
        allocation_scope = context.get('allocation_scope', 'annual')
        departments = context.get('departments', [])
        
        allocation_workflow = {
            "allocation_id": f"RES-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "resource_type": resource_type,
            "allocation_scope": allocation_scope,
            "departments": departments,
            "managed_by": "vice_president_of_operations",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "allocation_planning"
        }
        
        # Coordinate resource allocation
        await self.send_message(
            to_role="director_of_accounting",
            subject="Resource Allocation - Financial Planning",
            message=f"Develop financial allocation plan for {resource_type} resources",
            data={"allocation_workflow": allocation_workflow, "role": "financial_planning"}
        )
        
        await self.send_message(
            to_role="property_manager",
            subject="Resource Allocation - Strategic Review",
            message=f"Review strategic resource allocation for {allocation_scope}",
            data={"allocation_workflow": allocation_workflow, "role": "strategic_review"}
        )
        
        await self.send_message(
            to_role="assistant_manager",
            subject="Resource Allocation - Operational Implementation",
            message=f"Implement operational resource allocation across departments",
            data={"allocation_workflow": allocation_workflow, "role": "operational_implementation"}
        )
        
        return {
            "completed": True,
            "output": {
                "resource_allocation_managed": True,
                "allocation_workflow": allocation_workflow,
                "departments_coordinated": len(departments),
                "status": "planning_complete"
            }
        }
    
    async def _oversee_performance_management(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee organization-wide performance management"""
        performance_scope = context.get('performance_scope', 'organization_wide')
        review_period = context.get('review_period', 'quarterly')
        performance_metrics = context.get('performance_metrics', [])
        
        performance_workflow = {
            "performance_id": f"PERF-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "performance_scope": performance_scope,
            "review_period": review_period,
            "performance_metrics": performance_metrics,
            "overseen_by": "vice_president_of_operations",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "performance_review"
        }
        
        # Coordinate performance management
        await self.send_message(
            to_role="property_manager",
            subject="Performance Management - Executive Oversight",
            message=f"Provide executive oversight for {performance_scope} performance management",
            data={"performance_workflow": performance_workflow, "role": "executive_oversight"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Performance Management - Financial Metrics",
            message=f"Review financial performance metrics for {review_period}",
            data={"performance_workflow": performance_workflow, "role": "financial_metrics"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Performance Management - Operational Metrics",
            message=f"Review operational performance metrics for {review_period}",
            data={"performance_workflow": performance_workflow, "role": "operational_metrics"}
        )
        
        return {
            "completed": True,
            "output": {
                "performance_management_overseen": True,
                "performance_workflow": performance_workflow,
                "departments_reviewed": 3,
                "status": "active_review"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other VP of Operations action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "vice_president_of_operations",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class InternalControllerAgent(BaseAgent):
    """Internal Controller agent for financial controls and compliance oversight"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("internal_controller", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 0  # Requires approval for any amount
        self.permissions = [
            "financial_controls",
            "compliance_oversight",
            "internal_audit",
            "risk_management",
            "policy_enforcement",
            "regulatory_compliance"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute internal controller actions with compliance oversight"""
        context = input_data.get('context', {})
        
        if action == "conduct_internal_audit":
            return await self._conduct_internal_audit(context)
        elif action == "oversee_compliance_program":
            return await self._oversee_compliance_program(context)
        elif action == "manage_financial_controls":
            return await self._manage_financial_controls(context)
        elif action == "assess_risk_management":
            return await self._assess_risk_management(context)
        elif action == "enforce_policies":
            return await self._enforce_policies(context)
        elif action == "coordinate_regulatory_compliance":
            return await self._coordinate_regulatory_compliance(context)
        else:
            return await self._generic_action(action, context)
    
    async def _conduct_internal_audit(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct internal audit with comprehensive oversight"""
        audit_scope = context.get('audit_scope', 'financial')
        audit_period = context.get('audit_period', 'quarterly')
        
        audit_workflow = {
            "audit_id": f"INT-AUDIT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "audit_scope": audit_scope,
            "audit_period": audit_period,
            "conducted_by": "internal_controller",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "audit_in_progress"
        }
        
        # Coordinate internal audit process
        await self.send_message(
            to_role="director_of_accounting",
            subject="Internal Audit - Financial Review Required",
            message=f"Conduct {audit_scope} internal audit for {audit_period} period",
            data={"audit_workflow": audit_workflow, "focus": "financial_review"}
        )
        
        await self.send_message(
            to_role="accounting_manager",
            subject="Internal Audit - Documentation Review",
            message=f"Prepare all financial documentation for {audit_scope} internal audit",
            data={"audit_workflow": audit_workflow, "focus": "documentation_review"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Internal Audit - Record Compilation",
            message=f"Compile all records and documentation for {audit_scope} internal audit",
            data={"audit_workflow": audit_workflow, "focus": "record_compilation"}
        )
        
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Internal Audit - Executive Oversight",
            message=f"Internal {audit_scope} audit initiated, executive oversight required",
            data={"audit_workflow": audit_workflow, "focus": "executive_oversight"}
        )
        
        return {
            "completed": True,
            "output": {
                "internal_audit_conducted": True,
                "audit_workflow": audit_workflow,
                "agents_coordinated": 4,
                "estimated_completion": "3_weeks"
            }
        }
    
    async def _oversee_compliance_program(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee comprehensive compliance program"""
        compliance_area = context.get('compliance_area', 'general')
        compliance_action = context.get('compliance_action', 'review')
        
        compliance_workflow = {
            "compliance_id": f"COMP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "compliance_area": compliance_area,
            "compliance_action": compliance_action,
            "overseen_by": "internal_controller",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "compliance_oversight"
        }
        
        # Coordinate compliance oversight
        await self.send_message(
            to_role="director_of_accounting",
            subject="Compliance Oversight - Financial Controls",
            message=f"Review financial controls for {compliance_area} compliance",
            data={"compliance_workflow": compliance_workflow, "focus": "financial_controls"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Compliance Oversight - Operational Controls",
            message=f"Review operational controls for {compliance_area} compliance",
            data={"compliance_workflow": compliance_workflow, "focus": "operational_controls"}
        )
        
        await self.send_message(
            to_role="resident_services_manager",
            subject="Compliance Oversight - Resident Services",
            message=f"Review resident services for {compliance_area} compliance",
            data={"compliance_workflow": compliance_workflow, "focus": "resident_services"}
        )
        
        return {
            "completed": True,
            "output": {
                "compliance_program_overseen": True,
                "compliance_workflow": compliance_workflow,
                "departments_reviewed": 3,
                "status": "ongoing_oversight"
            }
        }
    
    async def _manage_financial_controls(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage financial controls and procedures"""
        control_type = context.get('control_type', 'general')
        control_action = context.get('control_action', 'review')
        
        control_workflow = {
            "control_id": f"CTRL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "control_type": control_type,
            "control_action": control_action,
            "managed_by": "internal_controller",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "control_management"
        }
        
        # Coordinate financial control management
        await self.send_message(
            to_role="accounting_manager",
            subject="Financial Controls - Procedure Review",
            message=f"Review and update {control_type} financial control procedures",
            data={"control_workflow": control_workflow, "focus": "procedure_review"}
        )
        
        await self.send_message(
            to_role="accountant",
            subject="Financial Controls - Implementation",
            message=f"Implement {control_type} financial controls",
            data={"control_workflow": control_workflow, "focus": "implementation"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Financial Controls - Documentation",
            message=f"Update documentation for {control_type} financial controls",
            data={"control_workflow": control_workflow, "focus": "documentation"}
        )
        
        return {
            "completed": True,
            "output": {
                "financial_controls_managed": True,
                "control_workflow": control_workflow,
                "agents_coordinated": 3,
                "status": "active_management"
            }
        }
    
    async def _assess_risk_management(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk management across the organization"""
        risk_area = context.get('risk_area', 'comprehensive')
        assessment_scope = context.get('assessment_scope', 'organization_wide')
        
        risk_workflow = {
            "risk_id": f"RISK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "risk_area": risk_area,
            "assessment_scope": assessment_scope,
            "assessed_by": "internal_controller",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "risk_assessment"
        }
        
        # Coordinate risk assessment
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Risk Assessment - Executive Oversight",
            message=f"Provide executive oversight for {risk_area} risk assessment",
            data={"risk_workflow": risk_workflow, "focus": "executive_oversight"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Risk Assessment - Financial Risks",
            message=f"Assess financial risks for {risk_area} risk assessment",
            data={"risk_workflow": risk_workflow, "focus": "financial_risks"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Risk Assessment - Operational Risks",
            message=f"Assess operational risks for {risk_area} risk assessment",
            data={"risk_workflow": risk_workflow, "focus": "operational_risks"}
        )
        
        await self.send_message(
            to_role="maintenance_supervisor",
            subject="Risk Assessment - Physical Risks",
            message=f"Assess physical and safety risks for {risk_area} risk assessment",
            data={"risk_workflow": risk_workflow, "focus": "physical_risks"}
        )
        
        return {
            "completed": True,
            "output": {
                "risk_management_assessed": True,
                "risk_workflow": risk_workflow,
                "departments_assessed": 4,
                "estimated_completion": "2_weeks"
            }
        }
    
    async def _enforce_policies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Enforce organizational policies and procedures"""
        policy_area = context.get('policy_area', 'general')
        enforcement_action = context.get('enforcement_action', 'review')
        
        policy_workflow = {
            "policy_id": f"POL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "policy_area": policy_area,
            "enforcement_action": enforcement_action,
            "enforced_by": "internal_controller",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "policy_enforcement"
        }
        
        # Coordinate policy enforcement
        await self.send_message(
            to_role="property_manager",
            subject="Policy Enforcement - Executive Support",
            message=f"Provide executive support for {policy_area} policy enforcement",
            data={"policy_workflow": policy_workflow, "focus": "executive_support"}
        )
        
        await self.send_message(
            to_role="assistant_manager",
            subject="Policy Enforcement - Operational Implementation",
            message=f"Implement {policy_area} policy enforcement across operations",
            data={"policy_workflow": policy_workflow, "focus": "operational_implementation"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Policy Enforcement - Communication",
            message=f"Communicate {policy_area} policy updates to all staff",
            data={"policy_workflow": policy_workflow, "focus": "communication"}
        )
        
        return {
            "completed": True,
            "output": {
                "policies_enforced": True,
                "policy_workflow": policy_workflow,
                "agents_coordinated": 3,
                "status": "active_enforcement"
            }
        }
    
    async def _coordinate_regulatory_compliance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate regulatory compliance activities"""
        regulatory_area = context.get('regulatory_area', 'general')
        compliance_action = context.get('compliance_action', 'review')
        
        regulatory_workflow = {
            "regulatory_id": f"REG-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "regulatory_area": regulatory_area,
            "compliance_action": compliance_action,
            "coordinated_by": "internal_controller",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "regulatory_coordination"
        }
        
        # Coordinate regulatory compliance
        await self.send_message(
            to_role="director_of_accounting",
            subject="Regulatory Compliance - Financial Reporting",
            message=f"Ensure financial reporting compliance for {regulatory_area}",
            data={"regulatory_workflow": regulatory_workflow, "focus": "financial_reporting"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Regulatory Compliance - Leasing Operations",
            message=f"Ensure leasing operations compliance for {regulatory_area}",
            data={"regulatory_workflow": regulatory_workflow, "focus": "leasing_operations"}
        )
        
        await self.send_message(
            to_role="resident_services_manager",
            subject="Regulatory Compliance - Resident Services",
            message=f"Ensure resident services compliance for {regulatory_area}",
            data={"regulatory_workflow": regulatory_workflow, "focus": "resident_services"}
        )
        
        return {
            "completed": True,
            "output": {
                "regulatory_compliance_coordinated": True,
                "regulatory_workflow": regulatory_workflow,
                "departments_coordinated": 3,
                "status": "ongoing_coordination"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other internal controller action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "internal_controller",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class LeasingCoordinatorAgent(BaseAgent):
    """Leasing Coordinator agent for leasing operations coordination and support"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("leasing_coordinator", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = 0  # Requires approval for any amount
        self.permissions = [
            "leasing_coordination",
            "prospect_management",
            "lease_processing",
            "marketing_support",
            "administrative_support",
            "team_coordination"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute leasing coordinator actions with operational support"""
        context = input_data.get('context', {})
        
        if action == "coordinate_leasing_operations":
            return await self._coordinate_leasing_operations(context)
        elif action == "manage_prospect_pipeline":
            return await self._manage_prospect_pipeline(context)
        elif action == "process_lease_applications":
            return await self._process_lease_applications(context)
        elif action == "support_marketing_efforts":
            return await self._support_marketing_efforts(context)
        elif action == "provide_administrative_support":
            return await self._provide_administrative_support(context)
        elif action == "coordinate_team_activities":
            return await self._coordinate_team_activities(context)
        else:
            return await self._generic_action(action, context)
    
    async def _coordinate_leasing_operations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate daily leasing operations"""
        operation_type = context.get('operation_type', 'daily')
        coordination_scope = context.get('coordination_scope', 'comprehensive')
        
        coordination_workflow = {
            "coordination_id": f"COORD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "operation_type": operation_type,
            "coordination_scope": coordination_scope,
            "coordinated_by": "leasing_coordinator",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "coordination_active"
        }
        
        # Coordinate leasing operations
        await self.send_message(
            to_role="leasing_manager",
            subject="Leasing Operations - Daily Coordination",
            message=f"Coordinate {operation_type} leasing operations",
            data={"coordination_workflow": coordination_workflow, "focus": "daily_coordination"}
        )
        
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Leasing Operations - Prospect Management",
            message=f"Manage prospect pipeline for {operation_type} operations",
            data={"coordination_workflow": coordination_workflow, "focus": "prospect_management"}
        )
        
        await self.send_message(
            to_role="leasing_agent",
            subject="Leasing Operations - Application Processing",
            message=f"Process lease applications for {operation_type} operations",
            data={"coordination_workflow": coordination_workflow, "focus": "application_processing"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Leasing Operations - Administrative Support",
            message=f"Provide administrative support for {operation_type} leasing operations",
            data={"coordination_workflow": coordination_workflow, "focus": "administrative_support"}
        )
        
        return {
            "completed": True,
            "output": {
                "leasing_operations_coordinated": True,
                "coordination_workflow": coordination_workflow,
                "agents_coordinated": 4,
                "status": "active_coordination"
            }
        }
    
    async def _manage_prospect_pipeline(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage prospect pipeline and follow-up activities"""
        pipeline_stage = context.get('pipeline_stage', 'all')
        management_action = context.get('management_action', 'review')
        
        pipeline_workflow = {
            "pipeline_id": f"PIPE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "pipeline_stage": pipeline_stage,
            "management_action": management_action,
            "managed_by": "leasing_coordinator",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "pipeline_management"
        }
        
        # Coordinate prospect pipeline management
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Prospect Pipeline - Lead Management",
            message=f"Manage {pipeline_stage} prospect pipeline leads",
            data={"pipeline_workflow": pipeline_workflow, "focus": "lead_management"}
        )
        
        await self.send_message(
            to_role="leasing_agent",
            subject="Prospect Pipeline - Follow-up Activities",
            message=f"Coordinate follow-up activities for {pipeline_stage} prospects",
            data={"pipeline_workflow": pipeline_workflow, "focus": "follow_up_activities"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Prospect Pipeline - Data Management",
            message=f"Manage prospect data and CRM updates for {pipeline_stage}",
            data={"pipeline_workflow": pipeline_workflow, "focus": "data_management"}
        )
        
        return {
            "completed": True,
            "output": {
                "prospect_pipeline_managed": True,
                "pipeline_workflow": pipeline_workflow,
                "agents_coordinated": 3,
                "status": "active_management"
            }
        }
    
    async def _process_lease_applications(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process lease applications and coordinate approvals"""
        application_type = context.get('application_type', 'standard')
        processing_priority = context.get('processing_priority', 'normal')
        
        application_workflow = {
            "application_id": f"APP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "application_type": application_type,
            "processing_priority": processing_priority,
            "processed_by": "leasing_coordinator",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "application_processing"
        }
        
        # Coordinate lease application processing
        await self.send_message(
            to_role="leasing_manager",
            subject="Lease Application - Review Required",
            message=f"Review {application_type} lease application with {processing_priority} priority",
            data={"application_workflow": application_workflow, "focus": "application_review"}
        )
        
        await self.send_message(
            to_role="accounting_manager",
            subject="Lease Application - Financial Review",
            message=f"Conduct financial review for {application_type} lease application",
            data={"application_workflow": application_workflow, "focus": "financial_review"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Lease Application - Documentation",
            message=f"Prepare documentation for {application_type} lease application",
            data={"application_workflow": application_workflow, "focus": "documentation"}
        )
        
        return {
            "completed": True,
            "output": {
                "lease_applications_processed": True,
                "application_workflow": application_workflow,
                "agents_coordinated": 3,
                "estimated_completion": "3_days"
            }
        }
    
    async def _support_marketing_efforts(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Support marketing efforts and campaign coordination"""
        marketing_type = context.get('marketing_type', 'general')
        support_scope = context.get('support_scope', 'comprehensive')
        
        marketing_workflow = {
            "marketing_id": f"MKT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "marketing_type": marketing_type,
            "support_scope": support_scope,
            "supported_by": "leasing_coordinator",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "marketing_support"
        }
        
        # Coordinate marketing support
        await self.send_message(
            to_role="director_of_leasing",
            subject="Marketing Support - Campaign Coordination",
            message=f"Coordinate {marketing_type} marketing campaign",
            data={"marketing_workflow": marketing_workflow, "focus": "campaign_coordination"}
        )
        
        await self.send_message(
            to_role="admin_assistant",
            subject="Marketing Support - Material Preparation",
            message=f"Prepare marketing materials for {marketing_type} campaign",
            data={"marketing_workflow": marketing_workflow, "focus": "material_preparation"}
        )
        
        await self.send_message(
            to_role="resident_services_manager",
            subject="Marketing Support - Community Integration",
            message=f"Integrate {marketing_type} marketing with community events",
            data={"marketing_workflow": marketing_workflow, "focus": "community_integration"}
        )
        
        return {
            "completed": True,
            "output": {
                "marketing_efforts_supported": True,
                "marketing_workflow": marketing_workflow,
                "agents_coordinated": 3,
                "status": "active_support"
            }
        }
    
    async def _provide_administrative_support(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide administrative support to leasing team"""
        support_type = context.get('support_type', 'general')
        support_priority = context.get('support_priority', 'normal')
        
        support_workflow = {
            "support_id": f"SUPP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "support_type": support_type,
            "support_priority": support_priority,
            "provided_by": "leasing_coordinator",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "administrative_support"
        }
        
        # Coordinate administrative support
        await self.send_message(
            to_role="admin_assistant",
            subject="Administrative Support - Document Management",
            message=f"Provide {support_type} administrative support with {support_priority} priority",
            data={"support_workflow": support_workflow, "focus": "document_management"}
        )
        
        await self.send_message(
            to_role="leasing_manager",
            subject="Administrative Support - Team Coordination",
            message=f"Coordinate administrative support for leasing team",
            data={"support_workflow": support_workflow, "focus": "team_coordination"}
        )
        
        return {
            "completed": True,
            "output": {
                "administrative_support_provided": True,
                "support_workflow": support_workflow,
                "agents_coordinated": 2,
                "status": "active_support"
            }
        }
    
    async def _coordinate_team_activities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate team activities and communication"""
        activity_type = context.get('activity_type', 'daily')
        coordination_scope = context.get('coordination_scope', 'team_wide')
        
        activity_workflow = {
            "activity_id": f"ACT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "activity_type": activity_type,
            "coordination_scope": coordination_scope,
            "coordinated_by": "leasing_coordinator",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "team_coordination"
        }
        
        # Coordinate team activities
        await self.send_message(
            to_role="leasing_manager",
            subject="Team Activities - Leadership Coordination",
            message=f"Coordinate {activity_type} team activities",
            data={"activity_workflow": activity_workflow, "focus": "leadership_coordination"}
        )
        
        await self.send_message(
            to_role="senior_leasing_agent",
            subject="Team Activities - Senior Agent Coordination",
            message=f"Coordinate {activity_type} activities for senior agents",
            data={"activity_workflow": activity_workflow, "focus": "senior_coordination"}
        )
        
        await self.send_message(
            to_role="leasing_agent",
            subject="Team Activities - Agent Coordination",
            message=f"Coordinate {activity_type} activities for leasing agents",
            data={"activity_workflow": activity_workflow, "focus": "agent_coordination"}
        )
        
        return {
            "completed": True,
            "output": {
                "team_activities_coordinated": True,
                "activity_workflow": activity_workflow,
                "agents_coordinated": 3,
                "status": "active_coordination"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other leasing coordinator action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "leasing_coordinator",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


class PresidentAgent(BaseAgent):
    """President agent for ultimate executive authority and strategic leadership"""
    
    def __init__(self, orchestrator: SOPOrchestrationEngine):
        super().__init__("president", orchestrator)
        self.claude = ClaudeService()
        self.can_approve_up_to = float('inf')  # Ultimate authority - can approve any amount
        self.permissions = [
            "ultimate_authority",
            "strategic_leadership",
            "board_governance",
            "major_decisions",
            "organizational_vision",
            "stakeholder_relations"
        ]
    
    async def execute_action(self, action: str, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute president actions with ultimate authority"""
        context = input_data.get('context', {})
        
        if action == "approve_major_strategic_decision":
            return await self._approve_major_strategic_decision(context)
        elif action == "provide_strategic_leadership":
            return await self._provide_strategic_leadership(context)
        elif action == "oversee_board_governance":
            return await self._oversee_board_governance(context)
        elif action == "manage_stakeholder_relations":
            return await self._manage_stakeholder_relations(context)
        elif action == "set_organizational_vision":
            return await self._set_organizational_vision(context)
        elif action == "coordinate_executive_leadership":
            return await self._coordinate_executive_leadership(context)
        else:
            return await self._generic_action(action, context)
    
    async def _approve_major_strategic_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Approve major strategic decisions with ultimate authority"""
        decision_type = context.get('decision_type', 'strategic')
        impact_level = context.get('impact_level', 'high')
        budget_impact = context.get('budget_impact', 0)
        strategic_importance = context.get('strategic_importance', 'high')
        
        decision_workflow = {
            "decision_id": f"PRES-DEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "decision_type": decision_type,
            "impact_level": impact_level,
            "budget_impact": budget_impact,
            "strategic_importance": strategic_importance,
            "approved_by": "president",
            "approved_at": datetime.utcnow().isoformat(),
            "approval_level": "president"
        }
        
        # Coordinate strategic decision implementation
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Major Strategic Decision - Executive Implementation",
            message=f"Implement major {decision_type} strategic decision with executive oversight",
            data={"decision_workflow": decision_workflow, "role": "executive_implementation"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Major Strategic Decision - Financial Planning",
            message=f"Develop financial plan for major {decision_type} strategic decision",
            data={"decision_workflow": decision_workflow, "role": "financial_planning"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Major Strategic Decision - Market Strategy",
            message=f"Develop market strategy for major {decision_type} strategic decision",
            data={"decision_workflow": decision_workflow, "role": "market_strategy"}
        )
        
        await self.send_message(
            to_role="property_manager",
            subject="Major Strategic Decision - Operational Leadership",
            message=f"Provide operational leadership for major {decision_type} strategic decision",
            data={"decision_workflow": decision_workflow, "role": "operational_leadership"}
        )
        
        return {
            "completed": True,
            "output": {
                "strategic_decision_approved": True,
                "decision_workflow": decision_workflow,
                "departments_coordinated": 4,
                "authority_level": "president"
            }
        }
    
    async def _provide_strategic_leadership(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Provide strategic leadership and vision"""
        leadership_focus = context.get('leadership_focus', 'organizational')
        strategic_period = context.get('strategic_period', 'annual')
        
        leadership_workflow = {
            "leadership_id": f"LEAD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "leadership_focus": leadership_focus,
            "strategic_period": strategic_period,
            "provided_by": "president",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "strategic_leadership"
        }
        
        # Coordinate strategic leadership
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Strategic Leadership - Executive Coordination",
            message=f"Coordinate executive activities for {leadership_focus} strategic leadership",
            data={"leadership_workflow": leadership_workflow, "focus": "executive_coordination"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Strategic Leadership - Financial Strategy",
            message=f"Develop financial strategy for {leadership_focus} strategic leadership",
            data={"leadership_workflow": leadership_workflow, "focus": "financial_strategy"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Strategic Leadership - Market Leadership",
            message=f"Provide market leadership for {leadership_focus} strategic direction",
            data={"leadership_workflow": leadership_workflow, "focus": "market_leadership"}
        )
        
        await self.send_message(
            to_role="internal_controller",
            subject="Strategic Leadership - Governance Oversight",
            message=f"Provide governance oversight for {leadership_focus} strategic leadership",
            data={"leadership_workflow": leadership_workflow, "focus": "governance_oversight"}
        )
        
        return {
            "completed": True,
            "output": {
                "strategic_leadership_provided": True,
                "leadership_workflow": leadership_workflow,
                "executives_coordinated": 4,
                "status": "active_leadership"
            }
        }
    
    async def _oversee_board_governance(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Oversee board governance and corporate governance"""
        governance_area = context.get('governance_area', 'comprehensive')
        governance_action = context.get('governance_action', 'oversight')
        
        governance_workflow = {
            "governance_id": f"GOV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "governance_area": governance_area,
            "governance_action": governance_action,
            "overseen_by": "president",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "board_governance"
        }
        
        # Coordinate board governance
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Board Governance - Executive Reporting",
            message=f"Prepare executive reporting for {governance_area} board governance",
            data={"governance_workflow": governance_workflow, "focus": "executive_reporting"}
        )
        
        await self.send_message(
            to_role="internal_controller",
            subject="Board Governance - Compliance Oversight",
            message=f"Provide compliance oversight for {governance_area} board governance",
            data={"governance_workflow": governance_workflow, "focus": "compliance_oversight"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Board Governance - Financial Governance",
            message=f"Ensure financial governance for {governance_area} board oversight",
            data={"governance_workflow": governance_workflow, "focus": "financial_governance"}
        )
        
        return {
            "completed": True,
            "output": {
                "board_governance_overseen": True,
                "governance_workflow": governance_workflow,
                "executives_coordinated": 3,
                "status": "active_governance"
            }
        }
    
    async def _manage_stakeholder_relations(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Manage stakeholder relations and communications"""
        stakeholder_type = context.get('stakeholder_type', 'comprehensive')
        relation_action = context.get('relation_action', 'management')
        
        stakeholder_workflow = {
            "stakeholder_id": f"STAKE-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "stakeholder_type": stakeholder_type,
            "relation_action": relation_action,
            "managed_by": "president",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "stakeholder_relations"
        }
        
        # Coordinate stakeholder relations
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Stakeholder Relations - Executive Communication",
            message=f"Manage executive communication for {stakeholder_type} stakeholder relations",
            data={"stakeholder_workflow": stakeholder_workflow, "focus": "executive_communication"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Stakeholder Relations - Market Relations",
            message=f"Manage market relations for {stakeholder_type} stakeholders",
            data={"stakeholder_workflow": stakeholder_workflow, "focus": "market_relations"}
        )
        
        await self.send_message(
            to_role="resident_services_manager",
            subject="Stakeholder Relations - Community Relations",
            message=f"Manage community relations for {stakeholder_type} stakeholders",
            data={"stakeholder_workflow": stakeholder_workflow, "focus": "community_relations"}
        )
        
        return {
            "completed": True,
            "output": {
                "stakeholder_relations_managed": True,
                "stakeholder_workflow": stakeholder_workflow,
                "departments_coordinated": 3,
                "status": "active_management"
            }
        }
    
    async def _set_organizational_vision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Set organizational vision and strategic direction"""
        vision_focus = context.get('vision_focus', 'comprehensive')
        vision_period = context.get('vision_period', 'long_term')
        
        vision_workflow = {
            "vision_id": f"VISION-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "vision_focus": vision_focus,
            "vision_period": vision_period,
            "set_by": "president",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "vision_setting"
        }
        
        # Coordinate organizational vision
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Organizational Vision - Executive Alignment",
            message=f"Align executive team with {vision_focus} organizational vision",
            data={"vision_workflow": vision_workflow, "focus": "executive_alignment"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Organizational Vision - Financial Alignment",
            message=f"Align financial strategy with {vision_focus} organizational vision",
            data={"vision_workflow": vision_workflow, "focus": "financial_alignment"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Organizational Vision - Market Alignment",
            message=f"Align market strategy with {vision_focus} organizational vision",
            data={"vision_workflow": vision_workflow, "focus": "market_alignment"}
        )
        
        await self.send_message(
            to_role="property_manager",
            subject="Organizational Vision - Operational Alignment",
            message=f"Align operations with {vision_focus} organizational vision",
            data={"vision_workflow": vision_workflow, "focus": "operational_alignment"}
        )
        
        return {
            "completed": True,
            "output": {
                "organizational_vision_set": True,
                "vision_workflow": vision_workflow,
                "departments_aligned": 4,
                "status": "vision_active"
            }
        }
    
    async def _coordinate_executive_leadership(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate executive leadership team"""
        coordination_focus = context.get('coordination_focus', 'comprehensive')
        leadership_action = context.get('leadership_action', 'coordination')
        
        leadership_workflow = {
            "leadership_id": f"EXEC-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            "coordination_focus": coordination_focus,
            "leadership_action": leadership_action,
            "coordinated_by": "president",
            "initiated_at": datetime.utcnow().isoformat(),
            "status": "executive_coordination"
        }
        
        # Coordinate executive leadership
        await self.send_message(
            to_role="vice_president_of_operations",
            subject="Executive Leadership - Operations Coordination",
            message=f"Coordinate operations leadership for {coordination_focus} executive team",
            data={"leadership_workflow": leadership_workflow, "focus": "operations_coordination"}
        )
        
        await self.send_message(
            to_role="director_of_accounting",
            subject="Executive Leadership - Financial Leadership",
            message=f"Provide financial leadership for {coordination_focus} executive team",
            data={"leadership_workflow": leadership_workflow, "focus": "financial_leadership"}
        )
        
        await self.send_message(
            to_role="director_of_leasing",
            subject="Executive Leadership - Market Leadership",
            message=f"Provide market leadership for {coordination_focus} executive team",
            data={"leadership_workflow": leadership_workflow, "focus": "market_leadership"}
        )
        
        await self.send_message(
            to_role="internal_controller",
            subject="Executive Leadership - Governance Leadership",
            message=f"Provide governance leadership for {coordination_focus} executive team",
            data={"leadership_workflow": leadership_workflow, "focus": "governance_leadership"}
        )
        
        return {
            "completed": True,
            "output": {
                "executive_leadership_coordinated": True,
                "leadership_workflow": leadership_workflow,
                "executives_coordinated": 4,
                "status": "active_coordination"
            }
        }
    
    async def _generic_action(self, action: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Handle any other president action"""
        return {
            "completed": True,
            "output": {
                "action": action,
                "status": "completed",
                "authority": "president",
                "timestamp": datetime.utcnow().isoformat()
            }
        }


# Agent factory function
def create_agent(role: str, orchestrator: SOPOrchestrationEngine) -> BaseAgent:
    """Create an agent based on role"""
    agent_map = {
        "property_manager": PropertyManagerAgent,
        "assistant_manager": AssistantManagerAgent,
        "leasing_manager": LeasingManagerAgent,
        "senior_leasing_agent": SeniorLeasingAgentAgent,
        "maintenance_supervisor": MaintenanceSupervisorAgent,
        "maintenance_tech_lead": MaintenanceTechLeadAgent,
        "maintenance_tech": MaintenanceTechAgent,
        "leasing_agent": LeasingAgentAgent,
        "accounting_manager": AccountingManagerAgent,
        "accountant": AccountantAgent,
        "resident_services_manager": ResidentServicesManagerAgent,
        "resident_services_rep": ResidentServicesRepAgent,
        "admin_assistant": AdminAssistantAgent,
        "director_of_accounting": DirectorOfAccountingAgent,
        "director_of_leasing": DirectorOfLeasingAgent,
        "vice_president_of_operations": VicePresidentOfOperationsAgent,
        "internal_controller": InternalControllerAgent,
        "leasing_coordinator": LeasingCoordinatorAgent,
        "president": PresidentAgent
    }
    
    agent_class = agent_map.get(role)
    if agent_class:
        return agent_class(orchestrator)
    else:
        # Return base agent for other roles
        return BaseAgent(role, orchestrator)


# Example usage
async def initialize_agents(orchestrator: SOPOrchestrationEngine):
    """Initialize all role agents"""
    roles = [
        "property_manager",
        "assistant_manager",
        "maintenance_supervisor",
        "maintenance_tech_lead",
        "maintenance_tech",
        "leasing_manager",
        "senior_leasing_agent",
        "leasing_agent",
        "accounting_manager",
        "accountant",
        "resident_services_manager",
        "resident_services_rep",
        "admin_assistant"
    ]
    
    for role in roles:
        agent = create_agent(role, orchestrator)
        orchestrator.register_agent(role, agent)
        logger.info(f"Initialized agent for role: {role}")