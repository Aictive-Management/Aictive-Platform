#!/usr/bin/env python3
"""
Convert System Manuals to YAML for Agent Knowledge Base
Processes the property management system documentation and creates structured YAML
"""

import os
import yaml
from typing import Dict, List, Any
from pathlib import Path
import re

# Define the comprehensive role structure based on System Manuals
SYSTEM_ROLES = {
    "01. Property Manager": {
        "agent_id": "property_manager",
        "title": "Property Manager",
        "level": "Operational Management",
        "reports_to": "vp_operations",
        "responsibilities": {
            "resident_management": [
                "Lease violations and compliance",
                "Non-renewal procedures",
                "Tenant notifications",
                "Resident satisfaction"
            ],
            "owner_relations": [
                "Owner communications",
                "Financial reporting",
                "Property performance updates",
                "Contract terminations"
            ],
            "vacancy_management": [
                "Advertising coordination",
                "Make-ready oversight",
                "Pricing strategy",
                "Showing coordination"
            ],
            "maintenance_coordination": [
                "Work order approval",
                "Vendor management",
                "Emergency response",
                "Preventive maintenance"
            ],
            "financial_oversight": [
                "Budget management",
                "Expense approval",
                "Revenue optimization",
                "Collection oversight"
            ]
        },
        "procedures": {
            "non_renewal": {
                "description": "Handle tenant non-renewal process",
                "steps": [
                    "Review lease expiration dates",
                    "Determine renewal/non-renewal decision",
                    "Send non-renewal notice (60 days)",
                    "Document in system",
                    "Coordinate with leasing for replacement"
                ],
                "forms": ["Non-Renewal Notice", "Notice to Quit"],
                "timeline": "60 days before lease expiration"
            },
            "owner_termination": {
                "description": "Process owner management termination",
                "steps": [
                    "Receive termination notice",
                    "Complete termination checklist",
                    "Transfer security deposits",
                    "Final financial reconciliation",
                    "Property handover"
                ],
                "forms": ["Termination Checklist", "Security Deposit Transfer"],
                "timeline": "30 days"
            }
        }
    },
    
    "02. Director of Leasing": {
        "agent_id": "director_leasing",
        "title": "Director of Leasing",
        "level": "Senior Management",
        "reports_to": "vp_operations",
        "responsibilities": {
            "leasing_operations": [
                "Oversee leasing team",
                "Approve lease terms and concessions",
                "Market analysis and pricing",
                "Occupancy optimization"
            ],
            "application_processing": [
                "Application criteria management",
                "Fair housing compliance",
                "Approval workflow oversight",
                "Adverse action procedures"
            ],
            "marketing_strategy": [
                "Marketing campaign development",
                "Online listing management",
                "Lead generation optimization",
                "Conversion rate improvement"
            ],
            "team_development": [
                "Leasing agent training",
                "Performance management",
                "Process improvement",
                "Quality assurance"
            ]
        },
        "procedures": {
            "application_approval": {
                "description": "Review and approve rental applications",
                "steps": [
                    "Review application completeness",
                    "Verify income and employment",
                    "Check rental history",
                    "Run credit and background checks",
                    "Apply scoring matrix",
                    "Make approval decision",
                    "Document decision rationale"
                ],
                "forms": ["Rental Application", "Scoring Matrix", "Adverse Action Notice"],
                "timeline": "24-48 hours"
            },
            "fair_housing_compliance": {
                "description": "Ensure fair housing law compliance",
                "steps": [
                    "Review advertising language",
                    "Monitor showing practices",
                    "Audit application decisions",
                    "Conduct team training",
                    "Document compliance efforts"
                ],
                "forms": ["Fair Housing Checklist"],
                "timeline": "Ongoing"
            }
        }
    },
    
    "03. Director of Accounting": {
        "agent_id": "director_accounting",
        "title": "Director of Accounting",
        "level": "Senior Management",
        "reports_to": "vp_operations",
        "responsibilities": {
            "financial_management": [
                "Financial reporting oversight",
                "Budget preparation and monitoring",
                "Cash flow management",
                "Financial controls implementation"
            ],
            "owner_accounting": [
                "Owner statement preparation",
                "Distribution processing",
                "Reserve management",
                "Year-end reporting"
            ],
            "compliance": [
                "Tax compliance",
                "Regulatory reporting",
                "Audit coordination",
                "Internal controls"
            ],
            "team_oversight": [
                "Accounting team management",
                "Process standardization",
                "System optimization",
                "Training and development"
            ]
        },
        "procedures": {
            "month_end_close": {
                "description": "Complete monthly financial close",
                "steps": [
                    "Reconcile all bank accounts",
                    "Review and post accruals",
                    "Process owner distributions",
                    "Generate financial statements",
                    "Review variance reports",
                    "Approve and distribute reports"
                ],
                "forms": ["Month-End Checklist", "Variance Report"],
                "timeline": "5 business days"
            },
            "eviction_financial": {
                "description": "Handle financial aspects of evictions",
                "steps": [
                    "Calculate total amount owed",
                    "Prepare eviction packet",
                    "Coordinate with legal",
                    "Track eviction costs",
                    "Process judgments",
                    "Set up payment plans if applicable"
                ],
                "forms": ["Eviction Cost Sheet", "Payment Plan Agreement"],
                "timeline": "As needed"
            }
        }
    },
    
    "04. Leasing Consultant": {
        "agent_id": "leasing_agent",
        "title": "Leasing Consultant",
        "level": "Operational Staff",
        "reports_to": "leasing_manager",
        "responsibilities": {
            "lead_management": [
                "Respond to inquiries",
                "Schedule showings",
                "Conduct property tours",
                "Follow up with prospects"
            ],
            "application_processing": [
                "Collect applications",
                "Verify documentation",
                "Process application fees",
                "Communicate decisions"
            ],
            "customer_service": [
                "Answer prospect questions",
                "Provide property information",
                "Handle objections",
                "Build rapport"
            ],
            "administrative": [
                "Update availability",
                "Maintain prospect database",
                "Prepare lease documents",
                "Coordinate move-ins"
            ]
        },
        "procedures": {
            "showing_process": {
                "description": "Conduct property showings",
                "steps": [
                    "Pre-qualify prospect",
                    "Schedule showing appointment",
                    "Prepare unit for showing",
                    "Conduct professional tour",
                    "Highlight property features",
                    "Address questions and objections",
                    "Collect application if interested",
                    "Follow up within 24 hours"
                ],
                "forms": ["Showing Checklist", "Guest Card"],
                "timeline": "30-45 minutes per showing"
            }
        }
    },
    
    "05. Resident Services Coordinator": {
        "agent_id": "resident_services_rep",
        "title": "Resident Services Coordinator",
        "level": "Operational Staff",
        "reports_to": "resident_services_manager",
        "responsibilities": {
            "move_in_coordination": [
                "Process new resident paperwork",
                "Conduct move-in inspections",
                "Provide welcome orientation",
                "Set up resident accounts"
            ],
            "lease_renewals": [
                "Generate renewal offers",
                "Negotiate renewal terms",
                "Process renewal documentation",
                "Update lease agreements"
            ],
            "move_out_processing": [
                "Schedule move-out inspections",
                "Process notices to vacate",
                "Coordinate unit turns",
                "Handle security deposits"
            ],
            "resident_relations": [
                "Address resident concerns",
                "Process service requests",
                "Maintain resident files",
                "Coordinate resident events"
            ]
        },
        "procedures": {
            "lease_renewal": {
                "description": "Process lease renewals",
                "steps": [
                    "Generate renewal notices (90 days out)",
                    "Calculate renewal rent increase",
                    "Send renewal offer to resident",
                    "Negotiate terms if needed",
                    "Prepare renewal documentation",
                    "Obtain signatures",
                    "Update system with new lease terms",
                    "Notify owner of renewal"
                ],
                "forms": ["Lease Renewal Form", "Renewal Notice"],
                "timeline": "90-60 days before expiration"
            },
            "move_out_process": {
                "description": "Handle resident move-outs",
                "steps": [
                    "Receive notice to vacate",
                    "Acknowledge receipt to resident",
                    "Schedule move-out inspection",
                    "Conduct final walkthrough",
                    "Document property condition",
                    "Calculate security deposit disposition",
                    "Process deposit return/charges",
                    "Close resident account"
                ],
                "forms": ["Notice to Vacate", "Move-Out Inspection Form", "Security Deposit Disposition"],
                "timeline": "30 days"
            }
        }
    },
    
    "11. VP Property Management": {
        "agent_id": "vp_operations",
        "title": "Vice President of Operations",
        "level": "Executive",
        "reports_to": "president",
        "responsibilities": {
            "strategic_leadership": [
                "Develop operational strategies",
                "Set performance goals",
                "Drive growth initiatives",
                "Ensure profitability"
            ],
            "team_management": [
                "Oversee all operational departments",
                "Develop leadership team",
                "Performance management",
                "Succession planning"
            ],
            "process_improvement": [
                "Optimize workflows",
                "Implement best practices",
                "Technology adoption",
                "Quality assurance"
            ],
            "stakeholder_relations": [
                "Major client relationships",
                "Vendor negotiations",
                "Industry partnerships",
                "Board reporting"
            ]
        },
        "procedures": {
            "strategic_planning": {
                "description": "Annual strategic planning process",
                "steps": [
                    "Analyze market conditions",
                    "Review previous year performance",
                    "Set growth targets",
                    "Develop operational strategies",
                    "Create implementation roadmap",
                    "Assign departmental goals",
                    "Establish KPIs",
                    "Monitor and adjust quarterly"
                ],
                "forms": ["Strategic Plan Template", "KPI Dashboard"],
                "timeline": "Annual with quarterly reviews"
            }
        }
    },
    
    "13. President": {
        "agent_id": "president",
        "title": "President",
        "level": "Executive",
        "reports_to": "board_of_directors",
        "responsibilities": {
            "company_leadership": [
                "Set company vision and direction",
                "Drive strategic initiatives",
                "Ensure financial performance",
                "Represent company externally"
            ],
            "business_development": [
                "Major acquisition decisions",
                "Strategic partnerships",
                "Market expansion",
                "Innovation initiatives"
            ],
            "governance": [
                "Board relations",
                "Regulatory compliance",
                "Risk management",
                "Corporate policies"
            ],
            "culture_development": [
                "Company culture",
                "Core values enforcement",
                "Leadership development",
                "Employee engagement"
            ]
        },
        "procedures": {
            "major_decisions": {
                "description": "Major business decision process",
                "steps": [
                    "Identify strategic opportunity",
                    "Conduct due diligence",
                    "Financial analysis",
                    "Risk assessment",
                    "Leadership team consultation",
                    "Board presentation if required",
                    "Make final decision",
                    "Communicate and implement"
                ],
                "forms": ["Decision Matrix", "Board Presentation Template"],
                "timeline": "Varies by decision magnitude"
            }
        }
    }
}

def create_comprehensive_yaml():
    """Create comprehensive YAML knowledge base from system manuals"""
    
    knowledge_base = {
        "metadata": {
            "version": "2.0",
            "created": "2025-01-12",
            "source": "System Manuals Conversion",
            "description": "Comprehensive agent knowledge base derived from property management system manuals"
        },
        
        "agents": {},
        "workflows": {},
        "procedures": {},
        "forms": {},
        "approval_hierarchies": {},
        "communication_templates": {}
    }
    
    # Process each role
    for folder_name, role_data in SYSTEM_ROLES.items():
        agent_id = role_data["agent_id"]
        
        # Create agent entry
        knowledge_base["agents"][agent_id] = {
            "title": role_data["title"],
            "level": role_data["level"],
            "reports_to": role_data["reports_to"],
            "folder_reference": folder_name,
            "responsibilities": role_data["responsibilities"],
            "authority": {
                "approval_limit": get_approval_limit(role_data["level"]),
                "can_terminate_leases": role_data["level"] in ["Operational Management", "Senior Management", "Executive"],
                "can_approve_vendors": role_data["level"] in ["Senior Management", "Executive"],
                "can_modify_procedures": role_data["level"] == "Executive"
            }
        }
        
        # Add procedures
        for proc_id, procedure in role_data.get("procedures", {}).items():
            full_proc_id = f"{agent_id}_{proc_id}"
            knowledge_base["procedures"][full_proc_id] = {
                "name": procedure["description"],
                "owner": agent_id,
                "category": determine_category(procedure["description"]),
                "steps": procedure["steps"],
                "forms_required": procedure.get("forms", []),
                "timeline": procedure.get("timeline", "As needed"),
                "approval_required": check_approval_needed(procedure["steps"])
            }
            
            # Create workflow
            knowledge_base["workflows"][full_proc_id] = create_workflow_from_procedure(
                agent_id, procedure
            )
    
    # Add approval hierarchies
    knowledge_base["approval_hierarchies"] = {
        "standard": [
            "operational_staff",
            "operational_management", 
            "senior_management",
            "executive"
        ],
        "financial": [
            "accountant",
            "accounting_manager",
            "director_accounting",
            "vp_operations",
            "president"
        ],
        "leasing": [
            "leasing_agent",
            "leasing_manager",
            "director_leasing",
            "vp_operations"
        ],
        "maintenance": [
            "maintenance_tech",
            "maintenance_supervisor",
            "property_manager",
            "vp_operations"
        ]
    }
    
    # Add communication templates
    knowledge_base["communication_templates"] = {
        "owner_notices": {
            "vacancy_update": {
                "subject": "Vacancy Update - {property_address}",
                "template": "Dear {owner_name}, This is to update you on the vacancy status..."
            },
            "maintenance_approval": {
                "subject": "Maintenance Approval Required - {property_address}",
                "template": "Dear {owner_name}, We need your approval for the following repair..."
            }
        },
        "resident_notices": {
            "lease_renewal": {
                "subject": "Lease Renewal Offer - {unit_number}",
                "template": "Dear {resident_name}, Your lease expires on {expiration_date}..."
            },
            "maintenance_update": {
                "subject": "Maintenance Request Update",
                "template": "Dear {resident_name}, Your maintenance request #{request_id} has been..."
            }
        }
    }
    
    # Add forms catalog
    knowledge_base["forms"] = {
        "LEASE-001": {
            "name": "Residential Lease Agreement",
            "category": "leasing",
            "required_signatures": ["tenant", "landlord", "guarantor_if_applicable"],
            "retention_period": "7 years"
        },
        "MAINT-001": {
            "name": "Maintenance Request Form",
            "category": "maintenance",
            "required_fields": ["unit", "issue_description", "urgency", "contact_info"],
            "processing_time": "24-48 hours"
        },
        "FIN-001": {
            "name": "Security Deposit Disposition",
            "category": "financial",
            "legal_requirement": True,
            "timeline": "30 days from move-out"
        }
    }
    
    return knowledge_base

def get_approval_limit(level: str) -> float:
    """Get approval limit based on role level"""
    limits = {
        "Operational Staff": 0,
        "Operational Management": 500,
        "Senior Management": 5000,
        "Executive": 50000
    }
    return limits.get(level, 0)

def determine_category(description: str) -> str:
    """Determine category from description"""
    desc_lower = description.lower()
    if any(word in desc_lower for word in ["lease", "rental", "application"]):
        return "leasing"
    elif any(word in desc_lower for word in ["maintenance", "repair", "work order"]):
        return "maintenance"
    elif any(word in desc_lower for word in ["financial", "accounting", "payment"]):
        return "financial"
    elif any(word in desc_lower for word in ["owner", "property management"]):
        return "property_management"
    else:
        return "general"

def check_approval_needed(steps: List[str]) -> bool:
    """Check if any steps require approval"""
    approval_keywords = ["approve", "approval", "authorize", "permission"]
    return any(keyword in step.lower() for step in steps for keyword in approval_keywords)

def create_workflow_from_procedure(agent_id: str, procedure: Dict[str, Any]) -> Dict[str, Any]:
    """Create workflow configuration from procedure"""
    workflow = {
        "name": procedure["description"],
        "owner": agent_id,
        "trigger": "manual",  # Can be enhanced based on procedure
        "steps": []
    }
    
    for i, step in enumerate(procedure["steps"]):
        step_config = {
            "id": f"step_{i+1}",
            "name": step[:50] + "..." if len(step) > 50 else step,
            "description": step,
            "assigned_to": agent_id,
            "timeout": "24 hours",
            "dependencies": [f"step_{i}"] if i > 0 else [],
            "outputs": ["completion_status", "notes"]
        }
        
        # Check if step needs special handling
        if "approval" in step.lower():
            step_config["requires_approval"] = True
            step_config["approval_from"] = "next_level_manager"
        
        workflow["steps"].append(step_config)
    
    return workflow

def save_enhanced_knowledge_base():
    """Save the enhanced knowledge base to YAML"""
    knowledge_base = create_comprehensive_yaml()
    
    # Save to file
    output_path = "enhanced_agent_knowledge_base.yaml"
    with open(output_path, 'w') as f:
        yaml.dump(knowledge_base, f, default_flow_style=False, sort_keys=False, width=120)
    
    print(f"✅ Enhanced knowledge base saved to {output_path}")
    
    # Print summary
    print(f"\n📊 Knowledge Base Summary:")
    print(f"   Agents: {len(knowledge_base['agents'])}")
    print(f"   Procedures: {len(knowledge_base['procedures'])}")
    print(f"   Workflows: {len(knowledge_base['workflows'])}")
    print(f"   Forms: {len(knowledge_base['forms'])}")
    print(f"   Approval Hierarchies: {len(knowledge_base['approval_hierarchies'])}")
    
    # Show sample agent
    print(f"\n👤 Sample Agent (Property Manager):")
    pm = knowledge_base['agents']['property_manager']
    print(f"   Title: {pm['title']}")
    print(f"   Level: {pm['level']}")
    print(f"   Reports to: {pm['reports_to']}")
    print(f"   Approval Limit: ${pm['authority']['approval_limit']}")
    print(f"   Responsibilities: {len(pm['responsibilities'])} categories")
    
    return knowledge_base

if __name__ == "__main__":
    print("🚀 Converting System Manuals to YAML Knowledge Base")
    print("=" * 60)
    
    # Create and save the knowledge base
    kb = save_enhanced_knowledge_base()
    
    print("\n💡 Next Steps:")
    print("1. Review enhanced_agent_knowledge_base.yaml")
    print("2. Import into the swarm system for intelligent processing")
    print("3. Use for workflow generation and agent training")
    print("4. Continue adding procedures from actual documents")
    
    print("\n✨ Conversion complete! The YAML knowledge base is ready for use.")