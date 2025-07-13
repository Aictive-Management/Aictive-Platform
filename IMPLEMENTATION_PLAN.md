# 📋 Aictive Platform - Implementation Plan for Position-Based System

## 🎯 Overview

This plan outlines how to implement a complete position-based email response system with SOPs, forms, and department routing.

## 🏗️ Architecture Components

### 1. **Position & Permission System**
```python
# Core components already built:
- Department enum (Maintenance, Leasing, Accounting, etc.)
- Position enum with hierarchy
- Permission matrix for each position
- Approval workflows
```

### 2. **SOP Management System**
- Store SOPs in database
- Version control for SOPs
- Department-specific procedures
- Time limits and escalation paths

### 3. **Form Template Library**
- Dynamic form generation
- Position-based access control
- Auto-fill from email context
- Digital signature support

### 4. **Email Response Engine**
- Template system with variables
- Position-appropriate language
- Automatic form attachment
- Approval workflow integration

## 📁 Database Schema

### Tables Needed:

```sql
-- Departments
CREATE TABLE departments (
    id UUID PRIMARY KEY,
    name VARCHAR(100),
    description TEXT,
    manager_position VARCHAR(100)
);

-- Positions
CREATE TABLE positions (
    id UUID PRIMARY KEY,
    title VARCHAR(100),
    department_id UUID REFERENCES departments(id),
    permission_flags JSONB,
    max_approval_amount DECIMAL,
    requires_approval_from UUID REFERENCES positions(id)
);

-- Staff Members
CREATE TABLE staff (
    id UUID PRIMARY KEY,
    email VARCHAR(255) UNIQUE,
    name VARCHAR(255),
    position_id UUID REFERENCES positions(id),
    is_active BOOLEAN DEFAULT true
);

-- SOPs
CREATE TABLE sops (
    id UUID PRIMARY KEY,
    department_id UUID REFERENCES departments(id),
    scenario VARCHAR(255),
    steps JSONB,
    required_forms TEXT[],
    escalation_path UUID[],
    time_limit_hours INTEGER,
    version INTEGER,
    updated_at TIMESTAMP
);

-- Form Templates
CREATE TABLE form_templates (
    id UUID PRIMARY KEY,
    name VARCHAR(255),
    category VARCHAR(100),
    file_url TEXT,
    required_fields JSONB,
    positions_can_use UUID[]
);

-- Email Responses
CREATE TABLE email_responses (
    id UUID PRIMARY KEY,
    email_id UUID REFERENCES emails(id),
    staff_id UUID REFERENCES staff(id),
    position_id UUID REFERENCES positions(id),
    action_taken VARCHAR(255),
    response_text TEXT,
    forms_attached UUID[],
    requires_approval BOOLEAN,
    approved_by UUID REFERENCES staff(id),
    approved_at TIMESTAMP,
    sent_at TIMESTAMP
);

-- Approval Queue
CREATE TABLE approval_queue (
    id UUID PRIMARY KEY,
    response_id UUID REFERENCES email_responses(id),
    requested_by UUID REFERENCES staff(id),
    requested_from UUID REFERENCES staff(id),
    status VARCHAR(50), -- pending, approved, rejected
    notes TEXT,
    created_at TIMESTAMP,
    resolved_at TIMESTAMP
);
```

## 🔄 Workflow Implementation

### Email Processing Flow:

1. **Email Received** → AI Classification
2. **Department Assignment** → Based on category & urgency
3. **Staff Notification** → Based on position & availability
4. **Response Generation** → Using position permissions
5. **Form Selection** → Based on SOP requirements
6. **Approval Check** → If position requires approval
7. **Send Response** → With tracking & logging

### Code Structure:

```python
# main_with_positions.py
@app.post("/api/process-email-with-position")
async def process_email_with_position(
    email: EmailRequest,
    staff_id: str,
    selected_action: str,
    selected_forms: List[str],
    token_data: TokenData = Depends(get_current_token)
):
    # 1. Get staff position
    staff = await get_staff_member(staff_id)
    position = await get_position(staff.position_id)
    
    # 2. Classify email
    classification = await claude_service.classify_email(email)
    
    # 3. Check permissions
    can_handle = check_position_permissions(position, classification)
    
    # 4. Generate response
    response = await generate_position_based_response(
        position, classification, selected_action, email
    )
    
    # 5. Handle approval if needed
    if position.requires_approval_from:
        await queue_for_approval(response, staff, position)
    
    return response
```

## 🚀 Implementation Steps

### Phase 1: Core System (Week 1-2)
1. ✅ Create position and permission models
2. ✅ Build SOP structure
3. ✅ Design form template system
4. Set up database tables
5. Create API endpoints for position-based responses

### Phase 2: Integration (Week 3-4)
1. Integrate with existing email classification
2. Build form attachment system
3. Implement approval workflows
4. Create notification system
5. Add audit logging

### Phase 3: UI Development (Week 5-6)
1. Staff portal with position login
2. Email queue by department
3. Response interface with form selection
4. Approval dashboard
5. SOP reference panel

### Phase 4: Advanced Features (Week 7-8)
1. Auto-response suggestions based on history
2. Performance metrics by position
3. SOP compliance tracking
4. Training mode for new staff
5. Multi-language support

## 📊 Sample API Endpoints

```python
# Position Management
POST   /api/positions                 # Create position
GET    /api/positions/{id}/permissions # Get position permissions
PUT    /api/positions/{id}            # Update position

# SOP Management  
GET    /api/sops/department/{dept_id} # Get department SOPs
POST   /api/sops                      # Create/update SOP
GET    /api/sops/{id}/steps           # Get SOP steps

# Form Templates
GET    /api/forms/position/{position_id} # Get available forms
POST   /api/forms/generate            # Generate filled form
GET    /api/forms/{id}/download       # Download form

# Email Response
POST   /api/emails/respond            # Create response with position
GET    /api/emails/queue/{dept_id}    # Get department email queue
POST   /api/emails/approve/{response_id} # Approve response

# Staff Management
GET    /api/staff/current             # Get current staff info
PUT    /api/staff/{id}/position       # Update staff position
GET    /api/staff/department/{dept_id} # Get department staff
```

## 🔐 Security Considerations

1. **Position-Based Access Control**
   - Validate position permissions for every action
   - Audit trail for all responses
   - Secure form access

2. **Approval Workflows**
   - Digital signatures for approvals
   - Time-limited approval tokens
   - Escalation for timeout

3. **Data Protection**
   - Encrypt sensitive tenant data
   - Role-based data visibility
   - GDPR compliance

## 📈 Success Metrics

- Response time by position/department
- SOP compliance rate
- Approval turnaround time
- Customer satisfaction by response type
- Form completion accuracy

## 🎯 Next Steps

1. **Review and approve** this implementation plan
2. **Set up development environment** with new database schema
3. **Create test data** for positions, SOPs, and forms
4. **Build MVP** with core position-based features
5. **Test with sample scenarios** from each department
6. **Deploy to staging** for user acceptance testing
7. **Train staff** on their position-specific features
8. **Launch incrementally** by department

## 💡 Key Benefits

- **Consistency**: SOPs ensure uniform responses
- **Compliance**: Position permissions prevent errors
- **Efficiency**: Pre-approved forms and templates
- **Accountability**: Full audit trail
- **Scalability**: Easy to add positions/departments
- **Training**: New staff follow established SOPs

This system will transform how property management teams handle emails, ensuring the right person responds with the right information every time!