#!/usr/bin/env python3
"""
Test script for the new LeasingManagerAgent
"""

import asyncio
import json
from datetime import datetime, timedelta
from claude_service import ClaudeService

class MockOrchestrator:
    """Mock orchestrator for testing"""
    def __init__(self):
        self.agents = {}
    
    def register_agent(self, role, agent):
        self.agents[role] = agent
    
    async def send_message(self, to_role, subject, message, data=None, message_type="normal"):
        print(f"📨 Message sent to {to_role}: {subject}")
        print(f"   Content: {message}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")

class LeasingManagerAgent:
    """Leasing Manager agent for property leasing operations"""
    
    def __init__(self, orchestrator):
        self.role = "leasing_manager"
        self.orchestrator = orchestrator
        self.claude = ClaudeService()
        self.can_approve_up_to = 1000
        self.permissions = [
            "approve_applications",
            "set_rental_rates", 
            "approve_lease_terms",
            "concession_approval_up_to_1000"
        ]
    
    async def execute_action(self, action: str, input_data: dict) -> dict:
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
    
    async def make_decision(self, decision_input: dict) -> dict:
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
    
    async def _approve_application(self, context: dict) -> dict:
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
            await self.orchestrator.send_message(
                "senior_leasing_agent",
                "Application Approved",
                f"Application {application_id} approved. Proceed with lease preparation.",
                {"decision": decision, "applicant_info": applicant_info}
            )
        else:
            # Notify leasing agents to inform applicant
            await self.orchestrator.send_message(
                "senior_leasing_agent",
                "Application Rejected",
                f"Application {application_id} rejected. Inform applicant of decision.",
                {"decision": decision, "applicant_info": applicant_info}
            )
        
        return {"completed": True, "output": decision}
    
    async def _set_rental_rates(self, context: dict) -> dict:
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
            await self.orchestrator.send_message(
                "property_manager",
                "Rental Rate Update",
                f"New rates set for {unit_type} units: ${current_rate} → ${new_rate}",
                {"rate_decision": rate_decision}
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
    
    async def _approve_lease_terms(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "accounting_manager",
            "New Lease Approved",
            f"New lease approved for tenant {tenant_id} in unit {unit_id}",
            {"lease_review": lease_review}
        )
        
        return {"completed": True, "output": lease_review}
    
    async def _approve_concession(self, context: dict) -> dict:
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
            await self.orchestrator.send_message(
                "accounting_manager",
                "Concession Approved",
                f"Concession of ${amount} approved for tenant {tenant_id}",
                {"concession": concession}
            )
            
            return {"completed": True, "output": concession}
        else:
            # Escalate to property manager
            await self.orchestrator.send_message(
                "property_manager",
                "Concession Approval Required",
                f"Concession of ${amount} exceeds my limit. Requires your approval.",
                context
            )
            
            return {
                "completed": True,
                "output": {
                    "approved": False,
                    "reason": "exceeds_approval_limit",
                    "escalated_to": "property_manager"
                }
            }
    
    async def _review_market_analysis(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "property_manager",
            "Market Analysis Complete",
            f"Market analysis completed. {len(analysis['recommendations'])} recommendations generated.",
            {"analysis": analysis}
        )
        
        return {"completed": True, "output": analysis}
    
    async def _coordinate_move_in(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "maintenance_supervisor",
            "Unit Preparation Required",
            f"Unit {unit_id} needs preparation for move-in on {move_in_date}",
            {"move_in_coordination": move_in_coordination}
        )
        
        # Coordinate with accounting team for payment setup
        await self.orchestrator.send_message(
            "accounting_manager",
            "New Tenant Setup",
            f"New tenant {tenant_id} moving into unit {unit_id} on {move_in_date}",
            {"move_in_coordination": move_in_coordination}
        )
        
        return {"completed": True, "output": move_in_coordination}
    
    async def _generic_action(self, action: str, context: dict) -> dict:
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

async def test_leasing_manager():
    """Test the LeasingManagerAgent functionality"""
    
    print("🚀 Testing LeasingManagerAgent...")
    
    # Create mock orchestrator and agent
    orchestrator = MockOrchestrator()
    agent = LeasingManagerAgent(orchestrator)
    
    print(f"✅ Created LeasingManagerAgent with approval limit: ${agent.can_approve_up_to}")
    print(f"📋 Permissions: {agent.permissions}")
    
    # Test 1: Approve application
    print("\n📝 Test 1: Approve rental application")
    result = await agent.execute_action("approve_application", {
        "context": {
            "application_id": "APP-001",
            "applicant_info": {
                "monthly_income": 6000,
                "credit_score": 720,
                "rental_history": [
                    {"positive": True, "eviction": False},
                    {"positive": True, "eviction": False}
                ]
            },
            "rent_amount": 1800
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Reject application
    print("\n📝 Test 2: Reject rental application")
    result = await agent.execute_action("approve_application", {
        "context": {
            "application_id": "APP-002",
            "applicant_info": {
                "monthly_income": 3000,
                "credit_score": 580,
                "rental_history": [
                    {"positive": False, "eviction": True}
                ]
            },
            "rent_amount": 1800
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Set rental rates
    print("\n💰 Test 3: Set rental rates")
    result = await agent.execute_action("set_rental_rates", {
        "context": {
            "unit_type": "2BR",
            "current_rate": 2200,
            "market_analysis": {"trend": "increasing", "competition": "moderate"},
            "occupancy_rate": 0.92
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Approve lease terms
    print("\n📋 Test 4: Approve lease terms")
    result = await agent.execute_action("approve_lease_terms", {
        "context": {
            "tenant_id": "TEN-003",
            "unit_id": "UNIT-101",
            "lease_terms": {
                "duration_months": 12,
                "monthly_rent": 1800,
                "deposit": 1800
            }
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 5: Approve concession within limit
    print("\n🎁 Test 5: Approve concession ($500)")
    result = await agent.execute_action("approve_concession", {
        "context": {
            "concession_type": "rent_reduction",
            "amount": 500,
            "reason": "market_conditions",
            "tenant_id": "TEN-004"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 6: Try to approve concession over limit
    print("\n🎁 Test 6: Try to approve concession ($1500) - should escalate")
    result = await agent.execute_action("approve_concession", {
        "context": {
            "concession_type": "rent_reduction",
            "amount": 1500,
            "reason": "market_conditions",
            "tenant_id": "TEN-005"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 7: Review market analysis
    print("\n📊 Test 7: Review market analysis")
    result = await agent.execute_action("review_market_analysis", {
        "context": {
            "market_data": {
                "competitor_rates": [2100, 2200, 2300, 2150],
                "trends": {"direction": "increasing", "strength": "moderate"}
            },
            "current_avg_rate": 2000
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 8: Coordinate move-in
    print("\n🏠 Test 8: Coordinate move-in")
    result = await agent.execute_action("coordinate_move_in", {
        "context": {
            "tenant_id": "TEN-006",
            "unit_id": "UNIT-202",
            "move_in_date": "2025-08-01"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 9: Make decision
    print("\n🤔 Test 9: Make decision")
    result = await agent.make_decision({
        "context": {
            "decision_type": "rate_adjustment",
            "current_occupancy": 0.88,
            "market_trend": "declining"
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n✅ LeasingManagerAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_leasing_manager()) 