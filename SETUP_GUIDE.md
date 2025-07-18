# Aictive Platform V2 - Setup Guide

## Prerequisites

### 1. Create Required Accounts

#### Supabase (Database & Auth)
1. Go to https://supabase.com
2. Create a new project
3. Copy your project URL and anon key
4. Add to `.env`:
   ```
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_ANON_KEY=your-anon-key
   ```

#### Inngest (Background Jobs)
1. Go to https://inngest.com
2. Sign up and create an app
3. Get your signing key
4. Add to `.env`:
   ```
   INNGEST_SIGNING_KEY=your-signing-key
   INNGEST_EVENT_KEY=your-event-key
   ```

#### Meilisearch (Search)
1. For local development:
   ```bash
   docker run -p 7700:7700 getmeili/meilisearch:latest
   ```
2. For cloud: https://cloud.meilisearch.com
3. Add to `.env`:
   ```
   MEILISEARCH_HOST=http://localhost:7700
   MEILISEARCH_KEY=your-master-key
   ```

### 2. API Keys

#### Anthropic Claude
1. Go to https://console.anthropic.com
2. Create API key
3. Add to `.env`:
   ```
   ANTHROPIC_API_KEY=your-claude-key
   ```

#### OpenAI (Optional)
1. Go to https://platform.openai.com
2. Create API key
3. Add to `.env`:
   ```
   OPENAI_API_KEY=your-openai-key
   ```

## Quick Start

### Step 1: Install Dependencies
```bash
cd /Users/garymartin/Downloads/aictive-platform-v2
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 2: Set Up Database
```bash
python setup_database.py
```

### Step 3: Index Documents
```bash
python index_documents.py
```

### Step 4: Start Services
```bash
# Terminal 1: Background jobs
python run_inngest.py

# Terminal 2: API server
uvicorn main:app --reload --port 8000

# Terminal 3: Frontend (if needed)
cd aictive-command-center
npm install
npm run dev
```

## Testing the System

### 1. Test Basic Agent
```bash
python test_basic_agent.py
```

### 2. Test Property Manager
```bash
python test_property_manager.py
```

### 3. Test Maintenance Workflow
```bash
python test_maintenance_workflow.py
```

## Architecture Overview

```
                                                             
   Frontend          �   API Server        �   AI Agents     
  (React/Next)           (FastAPI)            (SuperClaude)  
                                                             
                                                         
                               �                          �
                                                               
                           Background            Search        
                           (Inngest)            (Meilisearch)  
                                                               
                                                         
                               �                          �
                                                         
                                Supabase                 
                           (Database + Storage)          
                                                         
```

## Security Best Practices

1. **Never commit API keys**
   - Use `.env` files
   - Add `.env` to `.gitignore`
   - Use environment variables in production

2. **Use Supabase Row Level Security**
   - Enable RLS on all tables
   - Create policies for each role

3. **Validate all inputs**
   - Use Pydantic models
   - Sanitize user input
   - Rate limit API endpoints

## Troubleshooting

### Common Issues

1. **ModuleNotFoundError**
   ```bash
   pip install -r requirements.txt
   ```

2. **API Key Issues**
   - Check `.env` file exists
   - Verify keys are correct
   - No quotes needed in `.env`

3. **Database Connection**
   - Check Supabase project is active
   - Verify URL and keys
   - Check network connectivity

## Next Steps

1. Complete API key setup
2. Create database schema
3. Deploy first agent
4. Test maintenance workflow
5. Add remaining 12 roles

## Support

- Documentation: `/docs`
- Issues: Create in project tracker
- SuperClaude: Consult CLAUDE.md