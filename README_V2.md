# Aictive Platform V2 - AI-Powered Property Management

## Overview

Aictive Platform V2 implements 13 specialized AI agents for property management, with intelligent coordination and decision-making capabilities. The platform was developed using SuperClaude's advanced development features.

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   13 AI Agents  │────▶│   SuperClaude   │────▶│  Agent Swarms   │
│  (Specialized)  │     │   (Personas)    │     │ (Coordination)  │
└─────────────────┘     └─────────────────┘     └─────────────────┘
         │                       │                        │
         └───────────────────────┴────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │   V2 Infrastructure    │
                    ├─────────────────────────┤
                    │ • Supabase (Database)  │
                    │ • Inngest (Background) │
                    │ • Meilisearch (Search) │
                    └─────────────────────────┘
```

## The 13 Property Management Agents

1. **Property Manager** - Overall operations, balanced decision-making
2. **Director of Leasing** - Lead management, occupancy optimization
3. **Leasing Agent** - Tenant interaction, customer service focus
4. **Assistant Property Manager** - Daily support, operational efficiency
5. **Regional Manager** - Multi-property oversight, strategic planning
6. **Bookkeeper** - Financial records, accuracy and detail
7. **Administrative Assistant** - Documentation, process management
8. **Property Accountant** - Advanced finance, analytical insights
9. **Marketing Manager** - Property marketing, creative campaigns
10. **Director of Client Experience** - Satisfaction, retention strategies
11. **Resident Services Manager** - Resident needs, issue resolution
12. **Manager (Unspecified)** - General management, team leadership
13. **Maintenance Coordinator** - Work orders, vendor management

## Quick Start

### 1. Set Up Environment

```bash
# Clone and enter directory
cd /Users/garymartin/Downloads/aictive-platform-v2

# Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Services

Edit `.env` file with your actual keys:
```env
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=eyJ...
INNGEST_SIGNING_KEY=signkey_...
MEILISEARCH_KEY=master_key_...
```

### 3. Set Up Database

```bash
# Run database setup
python setup_database.py

# Copy schema to Supabase SQL editor
cat database_schema.sql
```

### 4. Test the System

```bash
# Test basic functionality
python test_basic_agent.py

# Test Property Manager workflow
python test_property_manager.py
```

### 5. Start Services

```bash
# Terminal 1: Background jobs
python run_inngest.py

# Terminal 2: API server
python main_v2.py

# Terminal 3: Original frontend (if needed)
cd aictive-command-center
npm install
npm run dev
```

## API Endpoints

- `POST /api/maintenance/submit` - Submit maintenance request
- `POST /api/applications/submit` - Submit rental application
- `POST /api/knowledge/search` - Search knowledge base
- `POST /api/agents/ask` - Ask specific agent
- `GET /api/agents/{role}/dashboard` - Agent dashboard
- `GET /api/agents` - List all agents
- `POST /api/swarm/coordinate` - Coordinate agent swarm

## SuperClaude Integration

Each agent has:
- Specific persona (analyzer, frontend, designer, etc.)
- Primary commands (thinkdeep, magic, showme, etc.)
- MCP servers (calendar, filesystem, figma, etc.)

## Swarm Coordination

Agents work together for complex tasks:
- Emergency maintenance (Property Manager + Maintenance Coordinator + Assistant)
- Application screening (Director of Leasing + Leasing Agent)
- Financial reporting (Bookkeeper + Property Accountant)

## Claude Hooks

Decision points and compliance:
- Emergency detection
- Fair housing compliance
- Cost approval thresholds
- Vendor selection

## Files Structure

```
aictive-platform-v2/
├── main_v2.py              # V2 API server
├── setup_database.py       # Database setup
├── run_inngest.py          # Background jobs
├── test_property_manager.py # Agent testing
├── database_schema.sql     # SQL schema
├── requirements.txt        # Dependencies
├── .env                    # Configuration
├── .gitignore             # Git ignore
├── SETUP_GUIDE.md         # Setup instructions
├── README_V2.md           # This file
│
├── tests/                 # Test data
│   ├── sample_maintenance_request.json
│   └── sample_lease_application.json
│
├── AI Implementation/     # Core AI files
│   ├── ai_services.py
│   ├── superclaude_integration.py
│   ├── swarm_hooks_integration.py
│   └── v2_architecture_integration.py
│
└── aictive-command-center/ # Original frontend
    └── (Next.js app files)
```

## Next Steps

1. **Get API Keys**
   - Claude: https://console.anthropic.com
   - Supabase: https://supabase.com
   - Inngest: https://inngest.com
   - Meilisearch: https://cloud.meilisearch.com

2. **Deploy to Production**
   - Push to GitHub (already configured)
   - Deploy to Vercel (frontend)
   - Deploy API to Cloud Run/Railway
   - Set up production database

3. **Index Documents**
   - Convert 800+ property management documents
   - Index in Meilisearch for AI search
   - Train agents on domain knowledge

4. **Implement Figma MCP**
   - Generate UI components
   - Create property listings
   - Design marketing materials

## Support

- SuperClaude Config: See CLAUDE.md
- Implementation Guide: See MASTER_IMPLEMENTATION_GUIDE.md
- API Docs: http://localhost:8000/docs

## Status

✅ Architecture designed and implemented
✅ 13 agents configured with SuperClaude
✅ Swarm coordination ready
✅ Claude hooks integrated
✅ V2 infrastructure prepared
⏳ Awaiting API keys and deployment

---

🤖 Built with Claude Code and SuperClaude capabilities