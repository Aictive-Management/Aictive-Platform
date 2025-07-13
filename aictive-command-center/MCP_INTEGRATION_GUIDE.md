# 🔌 MCP (Model Context Protocol) Integration Guide

## What is MCP?

MCP (Model Context Protocol) allows Claude Code to connect to external services and databases, giving it the ability to:
- Query databases directly
- Deploy and manage infrastructure
- Access external APIs
- Perform authenticated operations

## Setting Up MCP for Aictive

### 1. **Install Claude Code Desktop App**

First, ensure you have the Claude Code desktop app installed:
```bash
# macOS
brew install --cask claude-code

# Or download from:
# https://claude.ai/download
```

### 2. **Configure MCP Settings**

MCP configuration is stored in:
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/Claude/claude_desktop_config.json`

### 3. **Supabase MCP Setup**

#### Install Supabase MCP Server:
```bash
npm install -g @modelcontextprotocol/server-supabase
```

#### Add to MCP Configuration:
```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase",
        "--url", "YOUR_SUPABASE_PROJECT_URL",
        "--service-role-key", "YOUR_SUPABASE_SERVICE_ROLE_KEY"
      ]
    }
  }
}
```

#### Get Your Supabase Credentials:
1. Go to [app.supabase.com](https://app.supabase.com)
2. Select your project
3. Navigate to Settings → API
4. Copy:
   - Project URL
   - Service Role Key (keep this secret!)

### 4. **Vercel MCP Setup**

#### Install Vercel MCP Server:
```bash
npm install -g @modelcontextprotocol/server-vercel
```

#### Add to MCP Configuration:
```json
{
  "mcpServers": {
    "vercel": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-vercel",
        "--token", "YOUR_VERCEL_TOKEN"
      ]
    }
  }
}
```

#### Get Your Vercel Token:
1. Go to [vercel.com/account/tokens](https://vercel.com/account/tokens)
2. Create a new token
3. Name it "Claude Code MCP"
4. Copy the token (you'll only see it once!)

### 5. **Complete MCP Configuration Example**

Here's a complete configuration file for Aictive:

```json
{
  "mcpServers": {
    "supabase": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-supabase",
        "--url", "https://your-project.supabase.co",
        "--service-role-key", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
      ]
    },
    "vercel": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-vercel",
        "--token", "your_vercel_token_here"
      ]
    },
    "filesystem": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/server-filesystem",
        "--allowed-directories", "/Users/garymartin/Downloads/aictive-platform-v2"
      ]
    }
  }
}
```

### 6. **Restart Claude Code**

After updating the configuration:
1. Quit Claude Code completely
2. Restart the application
3. You should see MCP tools available in new conversations

### 7. **Using MCP in Claude Code**

Once configured, you can use commands like:

```
# Supabase examples:
"Query all properties from Supabase"
"Create a new tenant record in Supabase"
"Update work order status in database"

# Vercel examples:
"Deploy the latest changes to Vercel"
"Check deployment status"
"View recent deployments"
"Configure environment variables on Vercel"
```

### 8. **Aictive-Specific MCP Workflows**

#### Database Schema Setup:
```sql
-- Run this through Claude Code with MCP:
"Create Supabase tables for properties, tenants, work_orders, and payments"
```

#### Deployment Automation:
```
"Deploy aictive-command-center to Vercel with environment variables"
```

#### Data Sync:
```
"Sync RentVine webhook data to Supabase in real-time"
```

### 9. **Security Best Practices**

1. **Never commit MCP config** to version control
2. **Use environment-specific tokens** (dev/staging/prod)
3. **Rotate tokens regularly**
4. **Limit token permissions** to minimum required
5. **Monitor API usage** in both services

### 10. **Troubleshooting MCP**

#### MCP tools not appearing?
```bash
# Check config file location
ls ~/Library/Application\ Support/Claude/

# Validate JSON syntax
cat ~/Library/Application\ Support/Claude/claude_desktop_config.json | jq .
```

#### Permission errors?
- Ensure service role key for Supabase (not anon key)
- Check Vercel token has deployment permissions

#### Connection issues?
- Verify project URLs are correct
- Check firewall/proxy settings
- Try with a simple filesystem MCP first

### 11. **Advanced MCP Features**

#### Custom MCP Servers:
You can create custom MCP servers for RentVine:
```javascript
// rentvine-mcp-server.js
import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { RentVineClient } from './rentvine-client.js';

const server = new Server({
  name: 'rentvine',
  version: '1.0.0',
});

// Add your RentVine API methods
server.setRequestHandler('rentvine.getProperties', async () => {
  const client = new RentVineClient();
  return await client.getProperties();
});

server.start();
```

### 12. **Next Steps for Aictive**

1. **Set up Supabase MCP** for database operations
2. **Configure Vercel MCP** for deployments
3. **Test with simple queries** first
4. **Build automation workflows** combining both
5. **Create custom MCP** for RentVine integration

### 13. **Example Conversation with MCP**

```
You: "Create a Supabase table for work orders and deploy the schema"

Claude (with MCP): 
1. I'll create the work_orders table in Supabase
2. Add appropriate columns and indexes
3. Set up RLS policies
4. Deploy the migration

[Claude executes these operations directly through MCP]
```

### 14. **MCP Resources**

- [Official MCP Documentation](https://modelcontextprotocol.io)
- [MCP Server Registry](https://github.com/modelcontextprotocol/servers)
- [Creating Custom MCP Servers](https://modelcontextprotocol.io/docs/create-server)
- [MCP Security Guide](https://modelcontextprotocol.io/docs/security)

---

## Quick Start Checklist

- [ ] Install Claude Code desktop app
- [ ] Get Supabase project URL and service key
- [ ] Get Vercel authentication token
- [ ] Create MCP configuration file
- [ ] Add both servers to config
- [ ] Restart Claude Code
- [ ] Test with a simple query
- [ ] Start building with MCP!

Need help? The MCP tools will appear as special functions in Claude Code once properly configured. Just ask Claude to use them naturally in your conversations!