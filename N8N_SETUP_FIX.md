# n8n Setup Fix for Node.js v22 Compatibility Issue

## Problem

n8n v2.2.4 has a module loading error with Node.js v22.5.1:

```
Error: Failed to load module "community-packages": Cannot find module
```

## Solution Options

### Option 1: Use Node.js v20 LTS (Recommended)

n8n works best with Node.js v20 LTS. You can:

1. **Download Node.js v20 LTS**

   - Visit: https://nodejs.org/en/download/
   - Download the Windows installer for v20.x LTS
   - Install it

2. **Or use NVM (Node Version Manager) for Windows**

   ```powershell
   # Install NVM for Windows from: https://github.com/coreybutler/nvm-windows/releases
   # Then install and use Node.js v20
   nvm install 20
   nvm use 20
   ```

3. **After installing Node.js v20, run:**
   ```powershell
   npx n8n
   ```

### Option 2: Use Docker (If Available)

If you can install Docker Desktop for Windows:

1. **Install Docker Desktop**
   - Download from: https://www.docker.com/products/docker-desktop/
2. **Run n8n with Docker:**
   ```powershell
   docker run -it --rm --name n8n -p 5678:5678 n8nio/n8n
   ```

### Option 3: Skip n8n for Now

The MCP Lead Generation System works perfectly without n8n:

**Using the Dashboard:**

- Open: http://localhost:8501
- Click "Run Full Pipeline" to execute all steps

**Using the API directly:**

```powershell
# 1. Generate leads
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/generate_leads" `
  -Method POST -ContentType "application/json" `
  -Body '{"count": 50}'

# 2. Enrich leads
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/enrich_leads" `
  -Method POST -ContentType "application/json" `
  -Body '{"mode": "offline"}'

# 3. Generate messages
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/generate_messages" `
  -Method POST -ContentType "application/json" `
  -Body '{"channels": ["email", "linkedin"]}'

# 4. Send outreach (dry run)
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/send_outreach" `
  -Method POST -ContentType "application/json" `
  -Body '{"mode": "dry_run"}'
```

## What is n8n Used For?

n8n provides:

- Visual workflow automation
- Scheduled pipeline execution
- Webhook triggers
- Integration with external services

**But it's optional** - the core MCP system has all the functionality built-in via:

- REST API endpoints
- Streamlit dashboard UI
- Python pipeline scripts

## Recommendation

For now, use the **Streamlit Dashboard** (http://localhost:8501) which provides:

- ✅ Visual pipeline execution
- ✅ Real-time metrics
- ✅ Lead management
- ✅ No Node.js dependency issues

When you need workflow automation later, install Node.js v20 LTS for n8n compatibility.

## Current Services Running

| Service        | URL                        | Status                         |
| -------------- | -------------------------- | ------------------------------ |
| **MCP Server** | http://localhost:8000      | ✅ Running                     |
| **API Docs**   | http://localhost:8000/docs | ✅ Available                   |
| **Dashboard**  | http://localhost:8501      | ✅ Running                     |
| **n8n**        | http://localhost:5678      | ❌ Node.js compatibility issue |

## Next Steps

1. **Use the Dashboard now:** http://localhost:8501
2. **Test the full pipeline** with the "Run Pipeline" button
3. **When needed:** Install Node.js v20 LTS for n8n support
