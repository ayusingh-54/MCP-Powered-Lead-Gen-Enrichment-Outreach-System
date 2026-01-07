# Complete n8n Setup & Configuration Guide

> **Step-by-step guide to connect n8n with the MCP Lead Generation System**

---

## 📋 Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Installing n8n](#2-installing-n8n)
3. [Starting the MCP Server](#3-starting-the-mcp-server)
4. [Importing the Workflow](#4-importing-the-workflow)
5. [Configuring Environment Variables](#5-configuring-environment-variables)
6. [Understanding the Workflow](#6-understanding-the-workflow)
7. [Running the Pipeline](#7-running-the-pipeline)
8. [Monitoring & Debugging](#8-monitoring--debugging)
9. [Customizing the Workflow](#9-customizing-the-workflow)
10. [Production Deployment](#10-production-deployment)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Prerequisites

Before setting up n8n, ensure you have:

- ✅ **Docker** installed (recommended) OR Node.js 18+
- ✅ **MCP Server** running (see [Quick Start](../README.md))
- ✅ **Network access** between n8n and MCP Server
- ✅ **Browser** for n8n web interface

### System Requirements

| Component | Minimum | Recommended |
| --------- | ------- | ----------- |
| RAM       | 2 GB    | 4 GB        |
| CPU       | 2 cores | 4 cores     |
| Storage   | 5 GB    | 10 GB       |

---

## 2. Installing n8n

### Option A: Docker (Recommended)

```bash
# Using docker-compose (all services together)
docker-compose up -d n8n

# Or standalone n8n
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -v n8n_data:/home/node/.n8n \
  -e N8N_BASIC_AUTH_ACTIVE=false \
  n8nio/n8n
```

### Option B: npm (Global Installation)

```bash
# Install n8n globally
npm install -g n8n

# Start n8n
n8n start
```

### Option C: npx (No Installation)

```bash
# Run directly without installing
npx n8n
```

### Verify Installation

Open your browser and navigate to:

```
http://localhost:5678
```

You should see the n8n workflow editor.

---

## 3. Starting the MCP Server

Before configuring n8n, ensure the MCP server is running:

### Using Docker Compose

```bash
cd /path/to/project
docker-compose up -d mcp-server

# Verify it's running
curl http://localhost:8000/health
# Expected: {"status": "healthy", "timestamp": "..."}
```

### Manual Start

```bash
cd backend
python -m uvicorn mcp_server.server:app --host 0.0.0.0 --port 8000 --reload

# Verify it's running
curl http://localhost:8000/health
```

### Important URLs

| Service    | URL                        | Description     |
| ---------- | -------------------------- | --------------- |
| MCP Server | http://localhost:8000      | API endpoints   |
| API Docs   | http://localhost:8000/docs | Swagger UI      |
| n8n        | http://localhost:5678      | Workflow editor |

---

## 4. Importing the Workflow

### Step 4.1: Access n8n Editor

1. Open `http://localhost:5678` in your browser
2. If first time, you'll see a welcome screen - click "Get Started"

### Step 4.2: Import Workflow

**Method 1: Via UI**

1. Click the **hamburger menu** (☰) in the top left
2. Select **"Import from File"**
3. Browse to `n8n/workflow.json` in your project
4. Click **"Import"**

**Method 2: Via API**

```bash
curl -X POST http://localhost:5678/api/v1/workflows \
  -H "Content-Type: application/json" \
  -d @n8n/workflow.json
```

**Method 3: Copy-Paste**

1. Open `n8n/workflow.json` in a text editor
2. Copy the entire content
3. In n8n, press `Ctrl+V` or right-click and "Paste"

### Step 4.3: Verify Import

After importing, you should see:

```
[Start] → [Generate Leads] → [Check Success] → [Enrich Leads] → ...
```

The workflow should have these nodes:

- ✅ Start (Manual Trigger)
- ✅ Generate Leads (HTTP Request)
- ✅ Check Generate Success (IF)
- ✅ Enrich Leads (HTTP Request)
- ✅ Check Enrich Success (IF)
- ✅ Generate Messages (HTTP Request)
- ✅ Check Messages Success (IF)
- ✅ Send Outreach (HTTP Request)
- ✅ Pipeline Complete (Set)
- ✅ Error Handler (Code)

---

## 5. Configuring Environment Variables

### Step 5.1: Set n8n Environment Variables

n8n needs to know where the MCP server is:

**Option A: Docker Compose (Recommended)**

Edit `docker-compose.yml`:

```yaml
n8n:
  environment:
    - MCP_SERVER_URL=http://mcp-server:8000 # Uses Docker network
```

**Option B: Docker Standalone**

```bash
docker run -d \
  --name n8n \
  -p 5678:5678 \
  -e MCP_SERVER_URL=http://host.docker.internal:8000 \
  n8nio/n8n
```

**Option C: npm/npx**

```bash
# Linux/Mac
export MCP_SERVER_URL=http://localhost:8000
n8n start

# Windows (PowerShell)
$env:MCP_SERVER_URL = "http://localhost:8000"
n8n start
```

### Step 5.2: Verify Environment

In n8n, create a test workflow with Code node:

```javascript
// Test environment variable
return [
  {
    json: {
      mcp_url: $env.MCP_SERVER_URL || "not set",
    },
  },
];
```

### Step 5.3: Configure Workflow Variables

If environment variables don't work, update the HTTP nodes directly:

1. Click on **"Generate Leads"** node
2. In the URL field, change:
   ```
   FROM: ={{ $env.MCP_SERVER_URL || 'http://localhost:8000' }}/mcp/invoke/generate_leads
   TO: http://localhost:8000/mcp/invoke/generate_leads
   ```
3. Repeat for all HTTP nodes

---

## 6. Understanding the Workflow

### Workflow Architecture

```
┌─────────┐     ┌──────────────┐     ┌───────────┐
│  Start  │────▶│Generate Leads│────▶│Check Pass │
└─────────┘     └──────────────┘     └─────┬─────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    │ SUCCESS              │                       │ FAIL
                    ▼                      │                       ▼
             ┌──────────────┐              │               ┌───────────────┐
             │ Enrich Leads │              │               │ Error Handler │
             └──────┬───────┘              │               └───────────────┘
                    │                      │
                    ▼                      │
             ┌───────────┐                 │
             │Check Pass │                 │
             └─────┬─────┘                 │
                   │                       │
    ┌──────────────┼───────────────────────┤
    │ SUCCESS      │                       │
    ▼              │                       │
┌──────────────────┐                       │
│Generate Messages │                       │
└────────┬─────────┘                       │
         │                                 │
         ▼                                 │
  ┌───────────┐                            │
  │Check Pass │                            │
  └─────┬─────┘                            │
        │                                  │
   ┌────┼─────────────────────────────────┤
   │    │ SUCCESS                         │
   ▼    │                                 │
┌──────────────┐                          │
│Send Outreach │                          │
└──────┬───────┘                          │
       │                                  │
       ▼                                  │
┌─────────────────┐                       │
│Pipeline Complete│◀──────────────────────┘
└─────────────────┘
```

### Node Details

#### 1. Start Node (Manual Trigger)

- **Type**: `n8n-nodes-base.manualTrigger`
- **Purpose**: Initiates the workflow manually
- **Configuration**: None required

#### 2. Generate Leads Node

- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://localhost:8000/mcp/invoke/generate_leads`
- **Body**:
  ```json
  {
    "count": 200,
    "seed": 42
  }
  ```

#### 3. Enrich Leads Node

- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://localhost:8000/mcp/invoke/enrich_leads`
- **Body**:
  ```json
  {
    "mode": "offline",
    "batch_size": 50
  }
  ```

#### 4. Generate Messages Node

- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://localhost:8000/mcp/invoke/generate_messages`
- **Body**:
  ```json
  {
    "channels": ["email", "linkedin"],
    "generate_ab_variants": true
  }
  ```

#### 5. Send Outreach Node

- **Type**: HTTP Request
- **Method**: POST
- **URL**: `http://localhost:8000/mcp/invoke/send_outreach`
- **Body**:
  ```json
  {
    "mode": "dry_run",
    "rate_limit": 10,
    "batch_size": 50
  }
  ```

---

## 7. Running the Pipeline

### Step 7.1: Test Connection First

Before running the full workflow, test the MCP server connection:

1. Create a new workflow
2. Add an HTTP Request node
3. Configure:
   - **Method**: GET
   - **URL**: `http://localhost:8000/health`
4. Click **"Test step"**
5. Expected response: `{"status": "healthy"}`

### Step 7.2: Run Full Workflow

1. Open the imported workflow
2. Click **"Execute Workflow"** (play button)
3. Watch the execution progress through each node

### Step 7.3: Monitor Execution

During execution, you'll see:

- 🟢 Green = Success
- 🔴 Red = Error
- 🟡 Yellow = Running

Click on any node to see:

- Input data
- Output data
- Execution time
- Error messages (if any)

### Step 7.4: Verify Results

After successful execution:

```bash
# Check pipeline status
curl http://localhost:8000/mcp/invoke/get_status

# Expected output:
{
  "success": true,
  "metrics": {
    "total_leads": 200,
    "enriched_leads": 200,
    "messaged_leads": 200,
    "sent_leads": 200,
    "failed_leads": 0
  }
}
```

---

## 8. Monitoring & Debugging

### View Execution History

1. Click **"Executions"** in the sidebar
2. View all past executions
3. Click any execution to see details

### Enable Debug Logging

In n8n settings, enable verbose logging:

```bash
# Environment variable
export N8N_LOG_LEVEL=debug
export N8N_LOG_OUTPUT=console,file
```

### Common Log Locations

| Platform | Location              |
| -------- | --------------------- |
| Docker   | `docker logs n8n`     |
| npm      | Terminal output       |
| File     | `~/.n8n/logs/n8n.log` |

### Debugging Tips

1. **Check node output**: Click each node after execution
2. **Use Code node for debugging**:
   ```javascript
   console.log(JSON.stringify($input.all(), null, 2));
   return $input.all();
   ```
3. **Test nodes individually**: Use "Test step" button
4. **Check MCP server logs**: `docker logs mcp-server`

---

## 9. Customizing the Workflow

### Adding Webhooks (Auto-Trigger)

Replace Manual Trigger with Webhook:

1. Delete the Start node
2. Add **"Webhook"** node
3. Configure:
   - **HTTP Method**: POST
   - **Path**: `/trigger-pipeline`
4. Note the webhook URL

Trigger externally:

```bash
curl -X POST http://localhost:5678/webhook/trigger-pipeline \
  -H "Content-Type: application/json" \
  -d '{"lead_count": 100}'
```

### Adding Scheduled Trigger

For daily/weekly runs:

1. Add **"Cron"** node
2. Configure:
   - **Trigger Times**: Add your schedule
   - Example: Every day at 9 AM: `0 9 * * *`

### Adding Error Notifications

1. After Error Handler node, add:
   - **Slack** node for team alerts
   - **Email** node for notifications
   - **HTTP Request** to your monitoring system

Example Slack notification:

```javascript
// In Code node before Slack
return [
  {
    json: {
      text:
        `🚨 Pipeline Error!\n` +
        `Step: ${$json.failed_step}\n` +
        `Error: ${$json.error_message}\n` +
        `Time: ${new Date().toISOString()}`,
    },
  },
];
```

### Conditional Branching

Add different paths based on lead count:

```javascript
// In Code node
const leadCount = $input.first().json.leads_generated;

if (leadCount > 100) {
  return [{ json: { path: "high_volume" } }];
} else {
  return [{ json: { path: "normal" } }];
}
```

---

## 10. Production Deployment

### Security Considerations

1. **Enable Basic Auth**:

   ```yaml
   environment:
     - N8N_BASIC_AUTH_ACTIVE=true
     - N8N_BASIC_AUTH_USER=admin
     - N8N_BASIC_AUTH_PASSWORD=secure_password_here
   ```

2. **Use HTTPS** with reverse proxy (nginx/traefik)

3. **Restrict network access**:
   ```yaml
   n8n:
     networks:
       - internal # Only internal network
   ```

### Scaling

For high-volume pipelines:

1. **Use queue mode**:

   ```yaml
   environment:
     - EXECUTIONS_MODE=queue
     - QUEUE_BULL_REDIS_HOST=redis
   ```

2. **Add Redis**:
   ```yaml
   redis:
     image: redis:alpine
     networks:
       - leadgen-network
   ```

### Backup & Recovery

```bash
# Backup n8n data
docker cp n8n:/home/node/.n8n ./n8n-backup

# Backup workflows only
curl http://localhost:5678/api/v1/workflows > workflows-backup.json
```

---

## 11. Troubleshooting

### Issue: "Connection Refused" Error

**Symptoms**: HTTP nodes fail with ECONNREFUSED

**Solutions**:

1. **Docker networking issue**:

   ```bash
   # If n8n in Docker, MCP server on host
   # Use host.docker.internal instead of localhost
   http://host.docker.internal:8000/mcp/invoke/...
   ```

2. **MCP server not running**:

   ```bash
   curl http://localhost:8000/health
   # If fails, start the server
   ```

3. **Wrong port**:
   - Verify MCP_SERVER_URL environment variable

### Issue: "Timeout" Error

**Symptoms**: Requests timeout after 120 seconds

**Solutions**:

1. **Increase timeout in HTTP nodes**:

   - Options → Timeout → Set to 300000 (5 min)

2. **Reduce batch size**:

   ```json
   { "batch_size": 20 }
   ```

3. **Check MCP server performance**:
   ```bash
   docker stats mcp-server
   ```

### Issue: "Invalid JSON" Error

**Symptoms**: Parse errors in response

**Solutions**:

1. Check MCP server logs:

   ```bash
   docker logs mcp-server --tail 100
   ```

2. Test endpoint directly:
   ```bash
   curl -X POST http://localhost:8000/mcp/invoke/generate_leads \
     -H "Content-Type: application/json" \
     -d '{"count": 5}'
   ```

### Issue: Workflow Not Saving

**Symptoms**: Changes lost after refresh

**Solutions**:

1. **Check permissions**:

   ```bash
   chmod 755 ~/.n8n
   ```

2. **Verify volume mount**:
   ```bash
   docker inspect n8n | grep Mounts -A 10
   ```

### Issue: Environment Variables Not Working

**Symptoms**: `$env.MCP_SERVER_URL` returns undefined

**Solutions**:

1. **Restart n8n** after setting env vars

2. **Use process.env in Code node**:

   ```javascript
   const url = process.env.MCP_SERVER_URL || "http://localhost:8000";
   ```

3. **Hardcode URLs** as fallback

---

## Quick Reference Card

### Essential Commands

```bash
# Start all services
docker-compose up -d

# View n8n logs
docker logs -f n8n

# Check MCP server health
curl http://localhost:8000/health

# Trigger workflow via webhook
curl -X POST http://localhost:5678/webhook/trigger-pipeline

# Export workflow
curl http://localhost:5678/api/v1/workflows > backup.json
```

### Important URLs

| Service    | URL                        |
| ---------- | -------------------------- |
| n8n Editor | http://localhost:5678      |
| MCP Server | http://localhost:8000      |
| API Docs   | http://localhost:8000/docs |
| Mailhog    | http://localhost:8025      |
| Dashboard  | http://localhost:8501      |

### Environment Variables Reference

| Variable                | Default               | Description           |
| ----------------------- | --------------------- | --------------------- |
| `MCP_SERVER_URL`        | http://localhost:8000 | MCP server address    |
| `N8N_BASIC_AUTH_ACTIVE` | false                 | Enable authentication |
| `N8N_LOG_LEVEL`         | info                  | Logging level         |
| `EXECUTIONS_MODE`       | regular               | Execution mode        |

---

_For more help, visit:_

- [n8n Documentation](https://docs.n8n.io)
- [n8n Community Forum](https://community.n8n.io)
- [Project Issues](https://github.com/yourusername/mcp-lead-gen/issues)
