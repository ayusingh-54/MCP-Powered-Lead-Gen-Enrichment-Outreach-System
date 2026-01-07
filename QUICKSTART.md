# 🚀 Quick Start Guide - Windows (No Docker)

## ✅ Prerequisites

1. **Python 3.9+** - Already installed ✓
2. **Virtual Environment** - Already set up in `.venv` ✓
3. **Node.js 18+** - Required for n8n
   - Download from: https://nodejs.org
   - Or install: `winget install OpenJS.NodeJS.LTS`

## 📦 Step 1: Install Dependencies

```powershell
# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install Python packages (if not already done)
pip install -r requirements.txt
```

## 🎯 Step 2: Start the MCP Server & Dashboard

### Option A: Use PowerShell Script (Recommended)

```powershell
# Start everything
.\run_server.ps1

# Or start only the MCP server
.\run_server.ps1 -ServerOnly

# Or start only the dashboard
.\run_server.ps1 -FrontendOnly
```

### Option B: Start Manually

```powershell
# Activate venv
.\.venv\Scripts\Activate.ps1

# Terminal 1: Start MCP Server
python -m uvicorn backend.mcp_server.server:app --host 127.0.0.1 --port 8000

# Terminal 2: Start Streamlit Dashboard
python -m streamlit run frontend/app.py --server.port 8501
```

## 🔧 Step 3: Start n8n (Optional)

```powershell
# Run the n8n setup script
.\run_n8n.ps1
```

This will:

1. Check if Node.js is installed
2. Start n8n using npx
3. Open n8n at http://localhost:5678

### Import Workflow to n8n

1. Go to http://localhost:5678
2. Create an account (first time only)
3. Click **Workflows** → **Import from File**
4. Select: `n8n/workflow_production.json`
5. Set environment variable: `MCP_SERVER_URL = http://localhost:8000`

## 🌐 Access Your Services

| Service               | URL                        | Description         |
| --------------------- | -------------------------- | ------------------- |
| **MCP Server API**    | http://localhost:8000      | Main API            |
| **API Documentation** | http://localhost:8000/docs | Swagger UI          |
| **Dashboard**         | http://localhost:8501      | Streamlit UI        |
| **n8n**               | http://localhost:5678      | Workflow automation |

## 🧪 Test the Pipeline

### Via Dashboard (Easiest)

1. Go to http://localhost:8501
2. Click **"Run Full Pipeline"**
3. Watch the metrics update

### Via API

```powershell
# 1. Generate leads
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/generate_leads" `
  -Method POST -ContentType "application/json" -Body '{"count": 10}'

# 2. Enrich leads
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/enrich_leads" `
  -Method POST -ContentType "application/json" -Body '{"mode": "offline"}'

# 3. Generate messages
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/generate_messages" `
  -Method POST -ContentType "application/json" -Body '{"channels": ["email"]}'

# 4. Send outreach (dry run)
Invoke-RestMethod -Uri "http://localhost:8000/mcp/invoke/send_outreach" `
  -Method POST -ContentType "application/json" -Body '{"mode": "dry_run"}'

# 5. Check metrics
Invoke-RestMethod -Uri "http://localhost:8000/api/metrics"
```

### Via n8n Workflow

1. Open the imported workflow in n8n
2. Click **"Execute Workflow"**
3. Monitor the execution

## 🔧 Configuration

Edit `.env` file to customize:

```env
# Server
PORT=8000
HOST=127.0.0.1

# Database
DATABASE_PATH=storage/leads.db

# Pipeline defaults
LEAD_COUNT=200
ENRICHMENT_MODE=offline
SEND_MODE=dry_run

# SMTP (for real email sending)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

## 🛑 Stop Services

Simply close the PowerShell windows that were opened, or press `Ctrl+C` in each terminal.

## 🐛 Troubleshooting

### "Port already in use"

```powershell
# Find and kill process on port 8000
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process

# Or for port 8501
Get-Process -Id (Get-NetTCPConnection -LocalPort 8501).OwningProcess | Stop-Process
```

### "Module not found"

```powershell
# Reinstall dependencies
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt --force-reinstall
```

### "Cannot connect to MCP Server"

1. Check if server is running: http://localhost:8000/health
2. Check firewall settings
3. Try restarting the server

### "n8n won't start"

1. Ensure Node.js is installed: `node --version`
2. Try running manually: `npx n8n`
3. Check port 5678 isn't in use

## 📚 Next Steps

1. **Explore the API**: http://localhost:8000/docs
2. **Monitor the Dashboard**: http://localhost:8501
3. **Create Workflows in n8n**: http://localhost:5678
4. **Read Full Documentation**: See `README.md`

## 🆘 Need Help?

- Check the full `README.md` for detailed documentation
- View API docs at http://localhost:8000/docs
- Check logs in the terminal windows
- Review `docs/N8N_SETUP_GUIDE.md` for n8n integration details
