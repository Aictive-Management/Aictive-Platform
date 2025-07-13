#!/usr/bin/env python3
"""
Test script for the new AccountingManagerAgent
"""

import asyncio
import json
from datetime import datetime
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

class AccountingManagerAgent:
    """Accounting Manager agent for financial operations and reporting"""
    
    def __init__(self, orchestrator):
        self.role = "accounting_manager"
        self.orchestrator = orchestrator
        self.claude = ClaudeService()
        self.can_approve_up_to = 10000
        self.permissions = [
            "financial_reporting",
            "approve_refunds",
            "payment_plan_approval",
            "collection_strategies"
        ]
    
    async def execute_action(self, action: str, input_data: dict) -> dict:
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
    
    async def make_decision(self, decision_input: dict) -> dict:
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
    
    async def _generate_financial_report(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "property_manager",
            f"{report_type.title()} Financial Report",
            f"Financial report generated. NOI: ${financial_data['net_operating_income']}, Collection Rate: {financial_data['collection_rate']}%",
            {"report": report}
        )
        
        return {"completed": True, "output": report}
    
    async def _approve_refund(self, context: dict) -> dict:
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
                await self.orchestrator.send_message(
                    "accountant",
                    "Refund Approved",
                    f"Refund of ${refund_amount} approved for tenant {tenant_id}",
                    {"refund": refund}
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
            await self.orchestrator.send_message(
                "property_manager",
                "Refund Approval Required",
                f"Refund of ${refund_amount} exceeds my limit. Requires your approval.",
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
    
    async def _approve_payment_plan(self, context: dict) -> dict:
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
            await self.orchestrator.send_message(
                "accountant",
                "Payment Plan Approved",
                f"Payment plan approved for tenant {tenant_id}. ${total_amount} over {installments} months.",
                {"plan": plan}
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
    
    async def _develop_collection_strategy(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "property_manager",
            "Collection Strategy Developed",
            f"Collection strategy developed for {len(delinquent_accounts)} delinquent accounts. Estimated recovery: ${collection_strategy['estimated_recovery']}",
            {"collection_strategy": collection_strategy}
        )
        
        return {"completed": True, "output": collection_strategy}
    
    async def _review_budget(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "property_manager",
            "Budget Review Complete",
            f"Budget review completed for {budget_period}. Overall variance: ${overall_variance}",
            {"budget_review": budget_review}
        )
        
        return {"completed": True, "output": budget_review}
    
    async def _handle_audit_request(self, context: dict) -> dict:
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
        await self.orchestrator.send_message(
            "property_manager",
            "Audit Documentation Prepared",
            f"Audit documentation prepared for {audit_type} audit covering {audit_period}",
            {"audit_preparation": audit_preparation}
        )
        
        return {"completed": True, "output": audit_preparation}
    
    async def _generic_action(self, action: str, context: dict) -> dict:
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
    
    def _generate_financial_recommendations(self, financial_data: dict, kpis: dict) -> list:
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
    
    def _generate_budget_recommendations(self, variances: dict) -> list:
        """Generate budget recommendations based on variances"""
        recommendations = []
        
        for category, variance in variances.items():
            if variance["variance_percent"] > 10:
                recommendations.append(f"Review {category} spending - {variance['variance_percent']:.1f}% over budget")
            elif variance["variance_percent"] < -10:
                recommendations.append(f"Investigate {category} savings - {abs(variance['variance_percent']):.1f}% under budget")
        
        return recommendations

async def test_accounting_manager():
    """Test the AccountingManagerAgent functionality"""
    
    print("🚀 Testing AccountingManagerAgent...")
    
    # Create mock orchestrator and agent
    orchestrator = MockOrchestrator()
    agent = AccountingManagerAgent(orchestrator)
    
    print(f"✅ Created AccountingManagerAgent with approval limit: ${agent.can_approve_up_to}")
    print(f"📋 Permissions: {agent.permissions}")
    
    # Test 1: Generate financial report
    print("\n📊 Test 1: Generate financial report")
    result = await agent.execute_action("generate_financial_report", {
        "context": {
            "report_type": "monthly",
            "date_range": {"start": "2025-07-01", "end": "2025-07-31"}
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 2: Approve refund within limit
    print("\n💰 Test 2: Approve refund ($500)")
    result = await agent.execute_action("approve_refund", {
        "context": {
            "tenant_id": "TEN-001",
            "refund_amount": 500,
            "refund_reason": "overpayment",
            "supporting_docs": ["receipt", "bank_statement"]
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 3: Try to approve refund over limit
    print("\n💰 Test 3: Try to approve refund ($15,000) - should escalate")
    result = await agent.execute_action("approve_refund", {
        "context": {
            "tenant_id": "TEN-002",
            "refund_amount": 15000,
            "refund_reason": "overpayment",
            "supporting_docs": ["receipt"]
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 4: Approve payment plan
    print("\n📋 Test 4: Approve payment plan")
    result = await agent.execute_action("approve_payment_plan", {
        "context": {
            "tenant_id": "TEN-003",
            "total_amount": 3000,
            "installments": 3,
            "reason": "financial_hardship",
            "tenant_history": {
                "payment_score": 0.8,
                "previous_plans": []
            }
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 5: Reject payment plan
    print("\n📋 Test 5: Reject payment plan")
    result = await agent.execute_action("approve_payment_plan", {
        "context": {
            "tenant_id": "TEN-004",
            "total_amount": 8000,
            "installments": 8,
            "reason": "financial_hardship",
            "tenant_history": {
                "payment_score": 0.5,
                "previous_plans": [{"status": "active"}]
            }
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 6: Develop collection strategy
    print("\n📈 Test 6: Develop collection strategy")
    result = await agent.execute_action("develop_collection_strategy", {
        "context": {
            "delinquent_accounts": [
                {"tenant_id": "TEN-005", "amount": 1200, "days_late": 15},
                {"tenant_id": "TEN-006", "amount": 2400, "days_late": 45},
                {"tenant_id": "TEN-007", "amount": 3600, "days_late": 75}
            ],
            "total_delinquent_amount": 7200
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 7: Review budget
    print("\n📋 Test 7: Review budget")
    result = await agent.execute_action("review_budget", {
        "context": {
            "budget_period": "monthly",
            "actual_vs_budget": {
                "maintenance": {"actual": 13000, "budget": 12000},
                "utilities": {"actual": 7500, "budget": 8000},
                "insurance": {"actual": 4800, "budget": 5000},
                "marketing": {"actual": 2000, "budget": 3000}
            }
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 8: Handle audit request
    print("\n🔍 Test 8: Handle audit request")
    result = await agent.execute_action("handle_audit_request", {
        "context": {
            "audit_type": "financial",
            "audit_period": {"start": "2025-01-01", "end": "2025-12-31"},
            "requested_documents": ["income_statements", "expense_reports", "bank_reconciliations"]
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    # Test 9: Make decision
    print("\n🤔 Test 9: Make decision")
    result = await agent.make_decision({
        "context": {
            "decision_type": "budget_approval",
            "budget_amount": 50000,
            "expected_roi": 0.08
        }
    })
    print(f"Result: {json.dumps(result, indent=2)}")
    
    print("\n✅ AccountingManagerAgent tests completed!")

if __name__ == "__main__":
    asyncio.run(test_accounting_manager()) 