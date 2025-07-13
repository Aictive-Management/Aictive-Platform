# MCP Troubleshooting Guide

## Current Status

Your MCP configuration includes:
- ✅ **n8n-mcp**: Docker-based, should work if Docker is running
- ⚠️ **supabase**: Package exists but might need different arguments

## Troubleshooting Steps

### 1. Check Claude Desktop Logs

On macOS, you can view logs:
```bash
# View Claude logs
tail -f ~/Library/Logs/Claude/main.log

# Or check console app
open /System/Applications/Utilities/Console.app
# Then filter for "Claude"
```

### 2. Test Supabase MCP Manually

Try running the Supabase MCP server directly to see error messages:
```bash
npx -y @supabase/mcp-server-supabase https://jbdhyidbempvajjkicnm.supabase.co YOUR_SERVICE_ROLE_KEY
```

### 3. Check Docker for n8n-mcp

Make sure Docker is running:
```bash
docker --version
docker ps
```

### 4. Alternative Approach - Use Vercel AI SDK

Since direct MCP servers aren't working, you can use Vercel's approach:

1. **Deploy MCP endpoints to Vercel**:
```javascript
// api/mcp/supabase/route.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!
)

export async function POST(request: Request) {
  const { query, table } = await request.json()
  
  const { data, error } = await supabase
    .from(table)
    .select(query)
  
  return Response.json({ data, error })
}
```

2. **Use in your app**:
```javascript
// Use Vercel AI SDK with MCP tools
import { generateText } from 'ai'

const result = await generateText({
  model: 'claude-3-5-sonnet',
  tools: {
    querySupabase: {
      description: 'Query Supabase database',
      parameters: z.object({
        table: z.string(),
        query: z.string()
      }),
      execute: async ({ table, query }) => {
        const response = await fetch('/api/mcp/supabase', {
          method: 'POST',
          body: JSON.stringify({ table, query })
        })
        return response.json()
      }
    }
  }
})
```

### 5. Manual Vercel Deployment

For now, you can deploy manually:
```bash
cd /Users/garymartin/Downloads/aictive-platform-v2/aictive-command-center
vercel --prod
```

### 6. Check MCP Server Registry

Visit the official MCP server registry to see available servers:
https://github.com/modelcontextprotocol/servers

### 7. Community MCP Servers

Some working MCP servers from the community:
- `sqlite-mcp-server` - For SQLite databases
- `github-mcp-server` - For GitHub operations
- `google-drive-mcp` - For Google Drive

### 8. Wait for Official Releases

The MCP ecosystem is still new. Official Vercel and filesystem MCP servers might be released soon.

## Workaround - Use What Works

For now, you can:
1. Use n8n-mcp for workflow automation (if Docker is running)
2. Deploy to Vercel manually with `vercel` CLI
3. Access Supabase through your Next.js API routes
4. Use Claude Code (this CLI) for file operations

## Next Steps

1. Check if Docker is running for n8n-mcp
2. Monitor MCP server releases at https://modelcontextprotocol.io
3. Use Vercel AI SDK as an alternative approach
4. Deploy your app manually for now