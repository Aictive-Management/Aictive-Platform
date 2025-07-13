"""
Document to YAML Converter
Converts unstructured property management documents into structured YAML for agents
"""

import os
import re
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path
import json


@dataclass
class DocumentSection:
    """Represents a section of a document"""
    title: str
    content: str
    subsections: List['DocumentSection'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractedProcedure:
    """Extracted procedure from document"""
    name: str
    category: str
    steps: List[str]
    requirements: List[str] = field(default_factory=list)
    approvals: List[str] = field(default_factory=list)
    forms: List[str] = field(default_factory=list)
    timeline: Optional[str] = None


class DocumentParser:
    """Parse various document formats"""
    
    def __init__(self):
        self.patterns = {
            'procedure_header': r'^(?:procedure|process|workflow)[:：]\s*(.+)$',
            'step_number': r'^(?:\d+[\.\)]\s*|step\s+\d+[:：]\s*)',
            'approval_required': r'(?:approval|authorize|permission)\s+(?:required|needed|from)',
            'timeline': r'(?:within|complete\s+in|timeline[:：])\s*(\d+\s*(?:hours?|days?|weeks?))',
            'form_reference': r'(?:form|document|template)[:：]?\s*([A-Z0-9\-]+)',
            'dollar_amount': r'\$[\d,]+(?:\.\d{2})?',
        }
    
    def parse_document(self, content: str) -> List[DocumentSection]:
        """Parse document into sections"""
        lines = content.split('\n')
        sections = []
        current_section = None
        current_content = []
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if this is a section header
            if self._is_section_header(line):
                # Save previous section
                if current_section:
                    current_section.content = '\n'.join(current_content)
                    sections.append(current_section)
                
                # Start new section
                current_section = DocumentSection(title=line, content="")
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            current_section.content = '\n'.join(current_content)
            sections.append(current_section)
        
        return sections
    
    def _is_section_header(self, line: str) -> bool:
        """Determine if line is a section header"""
        # All caps or title case with colon
        if re.match(r'^[A-Z][A-Z\s]+[:：]?$', line):
            return True
        
        # Numbered sections
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True
        
        # Common headers
        headers = ['OVERVIEW', 'PROCEDURE', 'REQUIREMENTS', 'RESPONSIBILITIES',
                  'FORMS', 'APPROVALS', 'TIMELINE', 'STEPS']
        return any(line.upper().startswith(h) for h in headers)
    
    def extract_procedures(self, sections: List[DocumentSection]) -> List[ExtractedProcedure]:
        """Extract procedures from sections"""
        procedures = []
        
        for section in sections:
            # Look for procedure patterns
            if re.search(self.patterns['procedure_header'], section.title, re.I):
                procedure = self._extract_procedure_from_section(section)
                if procedure:
                    procedures.append(procedure)
        
        return procedures
    
    def _extract_procedure_from_section(self, section: DocumentSection) -> Optional[ExtractedProcedure]:
        """Extract procedure details from a section"""
        name = section.title
        content = section.content
        
        # Extract steps
        steps = self._extract_steps(content)
        
        # Extract requirements
        requirements = self._extract_requirements(content)
        
        # Extract approvals
        approvals = self._extract_approvals(content)
        
        # Extract forms
        forms = self._extract_forms(content)
        
        # Extract timeline
        timeline = self._extract_timeline(content)
        
        # Determine category
        category = self._determine_category(name, content)
        
        if steps:
            return ExtractedProcedure(
                name=name,
                category=category,
                steps=steps,
                requirements=requirements,
                approvals=approvals,
                forms=forms,
                timeline=timeline
            )
        
        return None
    
    def _extract_steps(self, content: str) -> List[str]:
        """Extract numbered steps from content"""
        steps = []
        lines = content.split('\n')
        
        for line in lines:
            if re.match(self.patterns['step_number'], line):
                # Remove step number and clean
                step = re.sub(self.patterns['step_number'], '', line).strip()
                if step:
                    steps.append(step)
        
        return steps
    
    def _extract_requirements(self, content: str) -> List[str]:
        """Extract requirements from content"""
        requirements = []
        
        # Look for requirement sections
        req_section = re.search(r'requirements?[:：](.*?)(?=\n[A-Z]|\n\d+\.|\Z)', 
                               content, re.I | re.S)
        if req_section:
            req_text = req_section.group(1)
            # Split by bullets or newlines
            reqs = re.split(r'[•·\-\*]\s*|\n\s*', req_text)
            requirements = [r.strip() for r in reqs if r.strip()]
        
        return requirements
    
    def _extract_approvals(self, content: str) -> List[str]:
        """Extract approval requirements"""
        approvals = []
        
        # Find approval mentions
        approval_matches = re.finditer(self.patterns['approval_required'], content, re.I)
        for match in approval_matches:
            # Get context around approval mention
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            context = content[start:end]
            
            # Extract who needs to approve
            if 'manager' in context.lower():
                approvals.append('property_manager')
            if 'supervisor' in context.lower():
                approvals.append('maintenance_supervisor')
            if 'director' in context.lower():
                approvals.append('director_level')
        
        return list(set(approvals))
    
    def _extract_forms(self, content: str) -> List[str]:
        """Extract form references"""
        forms = []
        
        form_matches = re.finditer(self.patterns['form_reference'], content, re.I)
        for match in form_matches:
            form_id = match.group(1)
            if form_id:
                forms.append(form_id)
        
        return list(set(forms))
    
    def _extract_timeline(self, content: str) -> Optional[str]:
        """Extract timeline information"""
        timeline_match = re.search(self.patterns['timeline'], content, re.I)
        if timeline_match:
            return timeline_match.group(1)
        return None
    
    def _determine_category(self, name: str, content: str) -> str:
        """Determine procedure category"""
        text = (name + ' ' + content).lower()
        
        if any(word in text for word in ['maintenance', 'repair', 'work order']):
            return 'maintenance'
        elif any(word in text for word in ['lease', 'rental', 'tenant application']):
            return 'leasing'
        elif any(word in text for word in ['payment', 'financial', 'accounting']):
            return 'financial'
        elif any(word in text for word in ['compliance', 'regulatory', 'legal']):
            return 'compliance'
        else:
            return 'general'


class YAMLGenerator:
    """Generate structured YAML from extracted data"""
    
    def __init__(self):
        self.agent_mapping = {
            'maintenance': ['maintenance_tech', 'maintenance_supervisor'],
            'leasing': ['leasing_agent', 'leasing_manager'],
            'financial': ['accountant', 'accounting_manager'],
            'property': ['property_manager', 'assistant_manager']
        }
    
    def generate_procedure_yaml(self, procedures: List[ExtractedProcedure]) -> Dict[str, Any]:
        """Generate YAML structure for procedures"""
        yaml_data = {
            'procedures': {},
            'workflows': {},
            'forms': {},
            'approval_chains': {}
        }
        
        for proc in procedures:
            proc_id = self._generate_id(proc.name)
            
            # Create procedure entry
            yaml_data['procedures'][proc_id] = {
                'name': proc.name,
                'category': proc.category,
                'description': f"Procedure for {proc.name}",
                'steps': proc.steps,
                'requirements': proc.requirements,
                'timeline': proc.timeline,
                'forms_required': proc.forms
            }
            
            # Create workflow entry
            workflow = self._generate_workflow(proc)
            yaml_data['workflows'][proc_id] = workflow
            
            # Add forms
            for form in proc.forms:
                if form not in yaml_data['forms']:
                    yaml_data['forms'][form] = {
                        'name': form,
                        'description': f"Form {form}",
                        'required_fields': [],
                        'used_in_procedures': []
                    }
                yaml_data['forms'][form]['used_in_procedures'].append(proc_id)
            
            # Add approval chain
            if proc.approvals:
                yaml_data['approval_chains'][proc_id] = {
                    'name': f"{proc.name} Approval Chain",
                    'levels': proc.approvals,
                    'escalation_time': '24 hours'
                }
        
        return yaml_data
    
    def _generate_id(self, name: str) -> str:
        """Generate ID from name"""
        # Convert to lowercase, replace spaces with underscores
        id_str = name.lower().replace(' ', '_')
        # Remove special characters
        id_str = re.sub(r'[^a-z0-9_]', '', id_str)
        return id_str
    
    def _generate_workflow(self, procedure: ExtractedProcedure) -> Dict[str, Any]:
        """Generate workflow from procedure"""
        workflow = {
            'name': procedure.name,
            'trigger': f"{procedure.category}_request",
            'priority': 'normal',
            'steps': []
        }
        
        # Map steps to agents
        agents = self.agent_mapping.get(procedure.category, ['property_manager'])
        
        for i, step in enumerate(procedure.steps):
            # Assign agent based on step content
            agent = self._assign_agent_to_step(step, agents)
            
            step_config = {
                'id': f"step_{i+1}",
                'name': step[:50],  # Truncate for name
                'description': step,
                'agent': agent,
                'timeout': '30 minutes',
                'dependencies': [f"step_{i}"] if i > 0 else []
            }
            
            # Check if approval needed
            if any(approval_word in step.lower() 
                   for approval_word in ['approve', 'authorization', 'permission']):
                step_config['requires_approval'] = True
            
            workflow['steps'].append(step_config)
        
        return workflow
    
    def _assign_agent_to_step(self, step: str, available_agents: List[str]) -> str:
        """Assign appropriate agent to step"""
        step_lower = step.lower()
        
        # Check for specific keywords
        if 'inspect' in step_lower or 'assess' in step_lower:
            return available_agents[0] if available_agents else 'property_manager'
        elif 'approve' in step_lower or 'review' in step_lower:
            return available_agents[-1] if available_agents else 'property_manager'
        else:
            return available_agents[0] if available_agents else 'property_manager'


class DocumentToYAMLConverter:
    """Main converter class"""
    
    def __init__(self):
        self.parser = DocumentParser()
        self.generator = YAMLGenerator()
    
    def convert_file(self, file_path: str) -> Dict[str, Any]:
        """Convert a single file to YAML"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse document
        sections = self.parser.parse_document(content)
        
        # Extract procedures
        procedures = self.parser.extract_procedures(sections)
        
        # Generate YAML
        yaml_data = self.generator.generate_procedure_yaml(procedures)
        
        return yaml_data
    
    def convert_directory(self, directory_path: str) -> Dict[str, Any]:
        """Convert all documents in directory to YAML"""
        all_procedures = []
        
        for file_path in Path(directory_path).glob('**/*.txt'):
            try:
                sections = self.parser.parse_document(file_path.read_text())
                procedures = self.parser.extract_procedures(sections)
                all_procedures.extend(procedures)
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
        
        return self.generator.generate_procedure_yaml(all_procedures)
    
    def save_yaml(self, data: Dict[str, Any], output_path: str):
        """Save data as YAML file"""
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)


# Demo function
def demo_converter():
    """Demonstrate document to YAML conversion"""
    print("📄 Document to YAML Converter Demo")
    print("=" * 50)
    
    # Sample document content
    sample_doc = """
MAINTENANCE REQUEST PROCEDURE:

OVERVIEW:
This procedure outlines the steps for handling maintenance requests from tenants.

REQUIREMENTS:
- Valid tenant complaint or request
- Property management system access
- Maintenance tracking form (MAINT-001)

PROCEDURE:
1. Receive and log maintenance request in system
2. Assess urgency and priority of request
3. If emergency (water leak, no heat, electrical), dispatch immediately
4. For routine requests, schedule within 48 hours
5. Assign appropriate maintenance technician
6. Obtain approval from Property Manager for repairs over $500
7. Complete work order and document completion
8. Follow up with tenant to ensure satisfaction
9. Close work order in system

TIMELINE: Complete within 24-48 hours for routine, 2 hours for emergency

FORMS REQUIRED:
- MAINT-001: Maintenance Request Form
- MAINT-002: Work Order Completion

APPROVALS:
Property Manager approval required for expenses over $500
Maintenance Supervisor approval for vendor dispatch
"""
    
    converter = DocumentToYAMLConverter()
    
    # Parse the document
    sections = converter.parser.parse_document(sample_doc)
    print(f"\n📑 Found {len(sections)} sections")
    for section in sections:
        print(f"   - {section.title}")
    
    # Extract procedures
    procedures = converter.parser.extract_procedures(sections)
    print(f"\n🔍 Extracted {len(procedures)} procedures")
    
    for proc in procedures:
        print(f"\n📋 Procedure: {proc.name}")
        print(f"   Category: {proc.category}")
        print(f"   Steps: {len(proc.steps)}")
        print(f"   Requirements: {len(proc.requirements)}")
        print(f"   Forms: {proc.forms}")
        print(f"   Timeline: {proc.timeline}")
        print(f"   Approvals: {proc.approvals}")
    
    # Generate YAML
    yaml_data = converter.generator.generate_procedure_yaml(procedures)
    
    # Save to file
    output_path = "extracted_procedures.yaml"
    converter.save_yaml(yaml_data, output_path)
    
    print(f"\n✅ YAML saved to {output_path}")
    
    # Display sample
    print("\n📄 Sample YAML output:")
    print(yaml.dump(yaml_data, default_flow_style=False, sort_keys=False)[:500] + "...")


if __name__ == "__main__":
    demo_converter()