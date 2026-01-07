# MCP-Powered Lead Generation + Enrichment + Outreach System

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

A **production-quality demo** of a complete lead generation system powered by the Model Context Protocol (MCP). This system generates synthetic leads, enriches them with contextual data, creates personalized outreach messages, and sends them via email or LinkedIn—all orchestrated by an intelligent agent.

![Architecture Diagram](docs/architecture.png)

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [MCP Tools Reference](#-mcp-tools-reference)
- [Configuration](#-configuration)
- [Free Tools Used](#-free-tools-used)
- [Example Outputs](#-example-outputs)
- [Testing](#-testing)
- [Troubleshooting](#-troubleshooting)

---

## ✨ Features

| Feature                    | Description                                                                     |
| -------------------------- | ------------------------------------------------------------------------------- |
| 🎯 **Lead Generation**     | Generate 200+ realistic leads using Faker with industry-role consistency        |
| 🔍 **Smart Enrichment**    | Rule-based + mock AI enrichment for pain points and talking points              |
| ✉️ **Message Generation**  | Personalized emails (≤120 words) and LinkedIn DMs (≤60 words) with A/B variants |
| 📤 **Outreach Sending**    | Dry-run and live modes with retry logic and rate limiting (10 msg/min)          |
| 🤖 **Agent Orchestration** | State-machine agent that decides which MCP tool to call next                    |
| 📊 **Real-time Dashboard** | Streamlit UI with metrics, lead tables, and pipeline controls                   |
| 🔄 **n8n Integration**     | Pre-built workflow for visual orchestration                                     |
| 🐳 **Docker Ready**        | One-command deployment with Docker Compose                                      |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                    │
│                         Streamlit Dashboard                              │
│                           (Port 8501)                                    │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │ HTTP
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                           MCP SERVER (FastAPI)                           │
│                              Port 8000                                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐       │
│  │ generate_   │ │  enrich_    │ │ generate_   │ │   send_     │       │
│  │   leads     │ │   leads     │ │  messages   │ │  outreach   │       │
│  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘ └──────┬──────┘       │
│         │               │               │               │               │
│         ▼               ▼               ▼               ▼               │
│  ┌─────────────────────────────────────────────────────────────┐       │
│  │                    SQLite Database                          │       │
│  │           leads | enrichments | messages | results          │       │
│  └─────────────────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          ▼                       ▼                       ▼
    ┌───────────┐          ┌───────────┐          ┌───────────┐
    │   Agent   │          │    n8n    │          │  Mailhog  │
    │  Service  │          │ Workflow  │          │   SMTP    │
    └───────────┘          └───────────┘          └───────────┘
```

### Pipeline States

```
NEW → ENRICHED → MESSAGED → SENT/FAILED
```

---

## 🚀 Quick Start

### Using Docker (Recommended)

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-lead-gen.git
cd mcp-lead-gen

# Start all services
docker-compose up -d

# Access the services:
# - Dashboard: http://localhost:8501
# - MCP Server: http://localhost:8000/docs
# - n8n: http://localhost:5678
# - Mailhog: http://localhost:8025
```

### Manual Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start MCP Server
cd backend
python -m uvicorn mcp_server.server:app --reload --port 8000

# In another terminal, start Frontend
streamlit run frontend/app.py

# (Optional) Start Mailhog for email testing
docker run -d -p 1025:1025 -p 8025:8025 mailhog/mailhog
```

---

## 📦 Installation

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (optional, for containerized deployment)
- n8n (optional, for workflow orchestration)

### Step-by-Step Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/yourusername/mcp-lead-gen.git
   cd mcp-lead-gen
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate     # Windows
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**

   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

5. **Initialize the database**
   ```bash
   # Database is auto-created on first run
   python -c "from backend.storage.database import DatabaseManager; DatabaseManager()"
   ```

---

## 📖 Usage

### Running the Full Pipeline

#### Option 1: Using the Streamlit Dashboard

1. Start the MCP server and frontend
2. Navigate to `http://localhost:8501`
3. Toggle between **Dry Run** and **Live Mode**
4. Click **Run Full Pipeline**
5. Monitor progress in real-time

#### Option 2: Using the Python Agent

```python
from backend.agent.pipeline_agent import PipelineAgent
import asyncio

async def main():
    agent = PipelineAgent(
        mcp_server_url="http://localhost:8000",
        dry_run=True  # Set to False for live mode
    )
    results = await agent.run_pipeline(
        lead_count=200,
        enrichment_mode="offline",
        seed=42
    )
    print(f"Pipeline completed: {results}")

asyncio.run(main())
```

#### Option 3: Using n8n Workflow

1. Open n8n at `http://localhost:5678`
2. Import the workflow from `n8n/workflow.json`
3. Configure the HTTP nodes to point to your MCP server
4. Click **Execute Workflow**

#### Option 4: Direct API Calls

```bash
# Generate leads
curl -X POST http://localhost:8000/mcp/invoke/generate_leads \
  -H "Content-Type: application/json" \
  -d '{"count": 50, "seed": 42}'

# Enrich leads
curl -X POST http://localhost:8000/mcp/invoke/enrich_leads \
  -H "Content-Type: application/json" \
  -d '{"mode": "offline", "batch_size": 10}'

# Generate messages
curl -X POST http://localhost:8000/mcp/invoke/generate_messages \
  -H "Content-Type: application/json" \
  -d '{"channel": "email", "generate_variants": true}'

# Send outreach
curl -X POST http://localhost:8000/mcp/invoke/send_outreach \
  -H "Content-Type: application/json" \
  -d '{"mode": "dry_run", "rate_limit": 10}'

# Get status
curl http://localhost:8000/mcp/invoke/get_status
```

---

## 🛠 MCP Tools Reference

### 1. `generate_leads`

Generate synthetic B2B leads with realistic data.

| Parameter | Type | Default | Description                     |
| --------- | ---- | ------- | ------------------------------- |
| `count`   | int  | 200     | Number of leads to generate     |
| `seed`    | int  | None    | Random seed for reproducibility |

**Response:**

```json
{
  "success": true,
  "leads_generated": 200,
  "message": "Successfully generated 200 leads"
}
```

### 2. `enrich_leads`

Enrich leads with pain points and talking points.

| Parameter    | Type | Default   | Description                        |
| ------------ | ---- | --------- | ---------------------------------- |
| `mode`       | str  | "offline" | Enrichment mode: "offline" or "ai" |
| `batch_size` | int  | 50        | Leads to process per batch         |

**Response:**

```json
{
  "success": true,
  "enriched_count": 200,
  "mode": "offline",
  "message": "Successfully enriched 200 leads"
}
```

### 3. `generate_messages`

Create personalized outreach messages.

| Parameter           | Type | Default | Description                    |
| ------------------- | ---- | ------- | ------------------------------ |
| `channel`           | str  | "email" | Channel: "email" or "linkedin" |
| `generate_variants` | bool | true    | Generate A/B variants          |
| `batch_size`        | int  | 50      | Leads to process per batch     |

**Response:**

```json
{
  "success": true,
  "messages_generated": 400,
  "channel": "email",
  "variants_generated": true,
  "message": "Generated 400 messages (with A/B variants)"
}
```

### 4. `send_outreach`

Send outreach messages to leads.

| Parameter     | Type | Default   | Description                 |
| ------------- | ---- | --------- | --------------------------- |
| `mode`        | str  | "dry_run" | Mode: "dry_run" or "live"   |
| `rate_limit`  | int  | 10        | Messages per minute         |
| `max_retries` | int  | 2         | Retry attempts for failures |
| `batch_size`  | int  | 50        | Messages per batch          |

**Response:**

```json
{
  "success": true,
  "sent_count": 200,
  "failed_count": 0,
  "mode": "dry_run",
  "message": "Successfully sent 200 messages"
}
```

### 5. `get_status`

Get current pipeline status and metrics.

**Response:**

```json
{
  "success": true,
  "metrics": {
    "total_leads": 200,
    "enriched_leads": 200,
    "messaged_leads": 200,
    "sent_leads": 200,
    "failed_leads": 0
  },
  "pipeline_health": "healthy"
}
```

---

## ⚙️ Configuration

### Environment Variables

| Variable            | Default                 | Description          |
| ------------------- | ----------------------- | -------------------- |
| `MCP_SERVER_URL`    | `http://localhost:8000` | MCP server URL       |
| `DATABASE_PATH`     | `storage/leads.db`      | SQLite database path |
| `LOG_LEVEL`         | `INFO`                  | Logging level        |
| `SMTP_HOST`         | `localhost`             | SMTP server host     |
| `SMTP_PORT`         | `1025`                  | SMTP server port     |
| `SMTP_SENDER_EMAIL` | `outreach@leadgen.demo` | Sender email         |
| `RATE_LIMIT`        | `10`                    | Messages per minute  |
| `MAX_RETRIES`       | `2`                     | Retry attempts       |

### Rate Limiting

The system enforces a configurable rate limit (default: 10 messages/minute) with exponential backoff retry logic:

```
Attempt 1: Immediate
Attempt 2: Wait 1 second
Attempt 3: Wait 2 seconds
```

---

## 🆓 Free Tools Used

This project uses **NO paid APIs**. All components are free and open-source:

| Tool          | Purpose                   | Website                                                  |
| ------------- | ------------------------- | -------------------------------------------------------- |
| **FastAPI**   | REST API framework        | [fastapi.tiangolo.com](https://fastapi.tiangolo.com)     |
| **Faker**     | Synthetic data generation | [faker.readthedocs.io](https://faker.readthedocs.io)     |
| **SQLite**    | Database storage          | [sqlite.org](https://sqlite.org)                         |
| **Streamlit** | Dashboard UI              | [streamlit.io](https://streamlit.io)                     |
| **n8n**       | Workflow automation       | [n8n.io](https://n8n.io)                                 |
| **Mailhog**   | SMTP testing              | [github.com/mailhog](https://github.com/mailhog/MailHog) |
| **Docker**    | Containerization          | [docker.com](https://docker.com)                         |

---

## 📊 Example Outputs

### Generated Lead

```json
{
  "id": "lead_001",
  "first_name": "Sarah",
  "last_name": "Johnson",
  "email": "sarah.johnson@techcorp.io",
  "company": "TechCorp Industries",
  "title": "VP of Engineering",
  "industry": "Technology",
  "company_size": "201-500",
  "linkedin_url": "https://linkedin.com/in/sarahjohnson",
  "status": "NEW"
}
```

### Enrichment Data

```json
{
  "lead_id": "lead_001",
  "pain_points": [
    "Scaling engineering team efficiently",
    "Reducing technical debt",
    "Improving deployment frequency"
  ],
  "talking_points": [
    "Ask about their current CI/CD pipeline",
    "Discuss engineering team growth challenges",
    "Mention recent tech industry trends"
  ],
  "company_insights": {
    "growth_stage": "scaling",
    "tech_stack_likely": ["Python", "AWS", "Kubernetes"],
    "hiring_velocity": "high"
  }
}
```

### Generated Email (≤120 words)

```
Subject: Quick question about TechCorp's engineering scaling

Hi Sarah,

I noticed TechCorp is growing rapidly—congrats on the momentum!

Many VPs of Engineering I speak with are grappling with scaling their teams
while maintaining code quality. Technical debt becomes a real bottleneck at
your stage.

We've helped similar companies reduce deployment friction by 40% while
actually improving team velocity.

Would you be open to a 15-minute call to explore if this could work for
TechCorp? I promise to make it worth your time.

Best,
[Your Name]

P.S. - I saw your team's recent open-source contribution. Impressive work!
```

### Generated LinkedIn DM (≤60 words)

```
Hi Sarah—saw TechCorp is scaling fast. Many engineering leaders I work with
face similar growing pains around technical debt and deployment speed.

We've helped teams like yours ship 40% faster. Open to connecting and
sharing what's worked?
```

### Pipeline Metrics

```json
{
  "total_leads": 200,
  "status_breakdown": {
    "NEW": 0,
    "ENRICHED": 0,
    "MESSAGED": 0,
    "SENT": 195,
    "FAILED": 5
  },
  "success_rate": 97.5,
  "avg_enrichment_time_ms": 45,
  "avg_message_generation_time_ms": 120,
  "messages_by_channel": {
    "email": 200,
    "linkedin": 200
  }
}
```

---

## 🧪 Testing

### Run Unit Tests

```bash
pytest tests/ -v
```

### Run Integration Tests

```bash
pytest tests/integration/ -v --cov=backend
```

### Test Individual Components

```bash
# Test lead generation
python -c "
from backend.mcp_server.lead_generator import LeadGenerator
gen = LeadGenerator()
leads = gen.generate(count=5, seed=42)
for lead in leads:
    print(f'{lead.first_name} {lead.last_name} - {lead.title} at {lead.company}')
"

# Test enrichment
python -c "
from backend.mcp_server.enrichment import EnrichmentEngine
engine = EnrichmentEngine()
# ... test with sample lead
"
```

---

## 🔧 Troubleshooting

### Common Issues

**1. Database locked error**

```bash
# Solution: Ensure only one process accesses the database
fuser -k storage/leads.db  # Linux
# Or restart the MCP server
```

**2. Port already in use**

```bash
# Find and kill the process
netstat -ano | findstr :8000  # Windows
lsof -i :8000                 # Linux/Mac
```

**3. Mailhog not receiving emails**

- Ensure Mailhog is running: `docker ps | grep mailhog`
- Check SMTP settings in `.env`
- Verify you're running in `live` mode, not `dry_run`

**4. n8n workflow fails**

- Ensure MCP server is running
- Check HTTP node URLs point to correct endpoints
- Review n8n execution logs

### Logs

```bash
# View MCP server logs
docker-compose logs -f mcp-server

# View all logs
docker-compose logs -f
```

---

## 📁 Project Structure

```
mcp-lead-gen/
├── backend/
│   ├── __init__.py
│   ├── mcp_server/
│   │   ├── __init__.py
│   │   ├── models.py           # Pydantic data models
│   │   ├── server.py           # FastAPI MCP server
│   │   ├── lead_generator.py   # Faker-based lead generation
│   │   ├── enrichment.py       # Rule-based + AI enrichment
│   │   ├── message_generator.py # Email/LinkedIn message generation
│   │   └── outreach_sender.py  # SMTP/LinkedIn sending
│   ├── agent/
│   │   ├── __init__.py
│   │   └── pipeline_agent.py   # Orchestration agent
│   ├── storage/
│   │   ├── __init__.py
│   │   └── database.py         # SQLite database manager
│   └── utils/
│       ├── __init__.py
│       ├── logging_config.py   # Logging configuration
│       ├── rate_limiter.py     # Rate limiting utilities
│       └── validators.py       # Input validation
├── frontend/
│   └── app.py                  # Streamlit dashboard
├── n8n/
│   └── workflow.json           # n8n workflow export
├── storage/
│   └── leads.db                # SQLite database (auto-created)
├── tests/
│   ├── test_lead_generator.py
│   ├── test_enrichment.py
│   └── test_message_generator.py
├── docker-compose.yml          # Docker orchestration
├── Dockerfile                  # MCP server container
├── Dockerfile.frontend         # Frontend container
├── requirements.txt            # Python dependencies
├── .env.example               # Environment template
└── README.md                  # This file
```

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📬 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/mcp-lead-gen/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/mcp-lead-gen/discussions)

---

Built with ❤️ using the Model Context Protocol
