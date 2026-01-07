# 🚀 MCP-Powered Lead Generation + Enrichment + Outreach System

> A production-quality, fully automated lead generation pipeline using Model Context Protocol (MCP), FastAPI, n8n, and Streamlit.

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Usage](#-usage)
- [MCP Tools Reference](#-mcp-tools-reference)
- [n8n Integration](#-n8n-integration)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [API Documentation](#-api-documentation)
- [Troubleshooting](#-troubleshooting)
- [Project Structure](#-project-structure)

---

## 🎯 Overview

This system demonstrates a complete, production-ready lead generation and outreach automation pipeline. It showcases:

- **MCP (Model Context Protocol)** server exposing AI-callable tools
- **Agent-driven orchestration** that decides which tool to call next
- **Workflow automation** via n8n for visual orchestration
- **Real-time dashboard** for monitoring and control

### What It Does

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Lead Generation Pipeline                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  📊 Generate    →    🔍 Enrich    →    ✉️ Message    →    📤 Send   │
│     Leads             Leads            Generate           Outreach │
│                                                                     │
│  200+ synthetic     Pain points       Email (≤120        Dry-run   │
│  B2B leads with     Persona           words) & LinkedIn   or Live  │
│  valid data         Buying triggers   DM (≤60 words)     mode      │
│                     Company size      A/B variants                  │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Features

### Core Capabilities

| Feature                | Description                                                 |
| ---------------------- | ----------------------------------------------------------- |
| **Lead Generation**    | Generate 200+ synthetic B2B leads with Faker                |
| **Data Enrichment**    | Offline rule-based or mock AI enrichment                    |
| **Message Generation** | Personalized emails (≤120 words) & LinkedIn DMs (≤60 words) |
| **A/B Testing**        | Automatic variant generation for message optimization       |
| **Smart Sending**      | Dry-run preview or live sending with rate limiting          |
| **Pipeline State**     | Track leads through NEW → ENRICHED → MESSAGED → SENT/FAILED |

### Technical Features

- ✅ **No Paid APIs** - All features work locally/offline
- ✅ **SQLite Persistence** - Data survives restarts
- ✅ **Rate Limiting** - 10 messages/min default, configurable
- ✅ **Retry Logic** - 2 retries with exponential backoff
- ✅ **Full Validation** - All fields syntactically validated
- ✅ **Docker Ready** - Single command deployment
- ✅ **Well Documented** - Comments everywhere

### Free Tools Used

| Tool          | Purpose             | Why Free          |
| ------------- | ------------------- | ----------------- |
| **FastAPI**   | MCP Server          | Open source       |
| **Faker**     | Lead generation     | Open source       |
| **SQLite**    | Data persistence    | Built-in Python   |
| **Mailhog**   | Email testing       | Open source       |
| **n8n**       | Workflow automation | Community edition |
| **Streamlit** | Dashboard           | Open source       |

---

## 🏗 Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend Layer                          │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              Streamlit Dashboard (:8501)                 │   │
│  │    • Metrics Overview    • Lead Table    • Controls     │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Orchestration Layer                        │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │   n8n Workflows     │    │    Pipeline Agent           │    │
│  │      (:5678)        │    │   (Python Orchestrator)     │    │
│  └─────────────────────┘    └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        MCP Server Layer                         │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │            FastAPI MCP Server (:8000)                   │   │
│  │                                                          │   │
│  │  Tools:                                                  │   │
│  │  • generate_leads    • enrich_leads                      │   │
│  │  • generate_messages • send_outreach    • get_status    │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Data Layer                              │
│  ┌─────────────────────┐    ┌─────────────────────────────┐    │
│  │   SQLite Database   │    │    Mailhog (SMTP Test)      │    │
│  │   storage/leads.db  │    │    (:1025 SMTP / :8025 UI)  │    │
│  └─────────────────────┘    └─────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### Data Flow

```
1. GENERATE  →  Create synthetic leads (Faker)
                └─→ Save to leads table (status: NEW)

2. ENRICH    →  Analyze each lead
                ├─→ Add pain_points, persona, triggers
                └─→ Update status to ENRICHED

3. MESSAGE   →  Generate personalized content
                ├─→ Email (≤120 words) + LinkedIn (≤60 words)
                ├─→ Optional A/B variants
                └─→ Update status to MESSAGED

4. SEND      →  Deliver messages
                ├─→ Dry-run: Preview only
                └─→ Live: SMTP/LinkedIn API
                    └─→ Update status to SENT or FAILED
```

---

## 🚀 Quick Start

### Option 1: Docker (Recommended)

```bash
# Clone and enter directory
git clone <your-repo-url>
cd mcp-lead-gen

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

Services will be available at:

- **MCP Server**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Dashboard**: http://localhost:8501
- **n8n**: http://localhost:5678
- **Mailhog**: http://localhost:8025

### Option 2: Python (Development)

```bash
# Clone and enter directory
git clone <your-repo-url>
cd mcp-lead-gen

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Start the system
python start.py
```

### Option 3: Manual Start

```bash
# Terminal 1: MCP Server
cd backend
uvicorn mcp_server.server:app --reload --port 8000

# Terminal 2: Streamlit Dashboard
streamlit run frontend/app.py --server.port 8501

# Terminal 3: n8n (optional)
npx n8n
```

---

## 📦 Installation

### Prerequisites

- Python 3.9+
- pip (Python package manager)
- Docker & Docker Compose (optional, for containerized deployment)
- Node.js 18+ (optional, for n8n without Docker)

### Step-by-Step Installation

```bash
# 1. Clone repository
git clone <your-repo-url>
cd mcp-lead-gen

# 2. Create virtual environment
python -m venv venv

# 3. Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt

# 5. Copy environment file
cp .env.example .env

# 6. (Optional) Edit .env for custom configuration
# nano .env

# 7. Create storage directory
mkdir -p storage

# 8. Run tests to verify installation
pytest tests/ -v
```

---

## 📖 Usage

### Running the Full Pipeline

#### Via Dashboard (Recommended)

1. Open http://localhost:8501
2. Configure options in sidebar:
   - Lead Count: 200
   - Enrichment Mode: offline
   - Channels: email, linkedin
   - Send Mode: dry_run
3. Click **"🚀 Run Full Pipeline"**
4. Monitor progress in real-time

#### Via Command Line

```bash
# Run with defaults
python run_pipeline.py

# Custom configuration
python run_pipeline.py \
  --count 100 \
  --enrichment-mode ai \
  --channels email linkedin \
  --mode dry_run \
  --rate-limit 10 \
  --seed 42

# Save results to file
python run_pipeline.py --output results.json
```

#### Via API

```bash
# Generate 50 leads
curl -X POST http://localhost:8000/mcp/invoke/generate_leads \
  -H "Content-Type: application/json" \
  -d '{"count": 50, "seed": 42}'

# Enrich leads
curl -X POST http://localhost:8000/mcp/invoke/enrich_leads \
  -H "Content-Type: application/json" \
  -d '{"mode": "offline", "batch_size": 50}'

# Generate messages
curl -X POST http://localhost:8000/mcp/invoke/generate_messages \
  -H "Content-Type: application/json" \
  -d '{"channels": ["email", "linkedin"], "generate_ab_variants": true}'

# Send in dry-run mode
curl -X POST http://localhost:8000/mcp/invoke/send_outreach \
  -H "Content-Type: application/json" \
  -d '{"mode": "dry_run", "rate_limit": 10}'

# Check status
curl http://localhost:8000/mcp/invoke/get_status
```

#### Via n8n Workflow

1. Open http://localhost:5678
2. Import workflow from `n8n/workflow_production.json`
3. Click **"Execute Workflow"**

See [n8n Integration](#-n8n-integration) for detailed setup.

---

## 🔧 MCP Tools Reference

### Tool 1: generate_leads

**Purpose**: Create synthetic B2B leads

**Endpoint**: `POST /mcp/invoke/generate_leads`

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `count` | int | 200 | Number of leads to generate |
| `seed` | int | null | Random seed for reproducibility |

**Example Request**:

```json
{
  "count": 100,
  "seed": 42
}
```

**Example Response**:

```json
{
  "success": true,
  "leads_generated": 100,
  "message": "Generated 100 leads"
}
```

**Generated Lead Fields**:

- `full_name`: Valid human name
- `company_name`: Realistic company name
- `role`: Job title (VP Sales, CTO, etc.)
- `industry`: Business sector
- `website`: Valid URL format
- `email`: Valid email format
- `linkedin_url`: Valid LinkedIn profile URL
- `country`: Geographic region

---

### Tool 2: enrich_leads

**Purpose**: Add business intelligence to leads

**Endpoint**: `POST /mcp/invoke/enrich_leads`

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | string | "offline" | "offline" or "ai" |
| `batch_size` | int | 50 | Leads per batch |

**Enrichment Fields**:

- `company_size`: small/medium/enterprise
- `persona`: Role-based classification
- `pain_points`: 2-3 relevant challenges
- `buying_triggers`: 1-2 purchase indicators
- `confidence_score`: 0-100 accuracy estimate

**Example Response**:

```json
{
  "success": true,
  "enriched_count": 100,
  "mode": "offline",
  "message": "Enriched 100 leads using offline mode"
}
```

---

### Tool 3: generate_messages

**Purpose**: Create personalized outreach messages

**Endpoint**: `POST /mcp/invoke/generate_messages`

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channels` | array | ["email", "linkedin"] | Message types |
| `generate_ab_variants` | bool | true | Create A/B variants |
| `batch_size` | int | 50 | Leads per batch |

**Message Constraints**:

- **Email**: ≤120 words, includes subject line
- **LinkedIn DM**: ≤60 words, no subject

**Example Response**:

```json
{
  "success": true,
  "messages_generated": 200,
  "channels": ["email", "linkedin"],
  "variants_generated": 400,
  "message": "Generated 400 messages (with variants)"
}
```

---

### Tool 4: send_outreach

**Purpose**: Send generated messages

**Endpoint**: `POST /mcp/invoke/send_outreach`

**Parameters**:
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mode` | string | "dry_run" | "dry_run" or "live" |
| `rate_limit` | int | 10 | Messages per minute |
| `max_retries` | int | 2 | Retry attempts |
| `batch_size` | int | 50 | Messages per batch |

**Modes**:

- **dry_run**: Preview messages, no actual sending
- **live**: Send via SMTP (email) / simulate (LinkedIn)

**Example Response**:

```json
{
  "success": true,
  "sent_count": 100,
  "failed_count": 0,
  "mode": "dry_run",
  "message": "Sent 100 messages (dry-run)"
}
```

---

### Tool 5: get_status

**Purpose**: Get pipeline metrics and status

**Endpoint**: `GET /mcp/invoke/get_status`

**Example Response**:

```json
{
  "success": true,
  "metrics": {
    "total_leads": 200,
    "status_counts": {
      "NEW": 0,
      "ENRICHED": 0,
      "MESSAGED": 0,
      "SENT": 195,
      "FAILED": 5
    },
    "enrichment_count": 200,
    "message_count": 400,
    "sent_count": 195,
    "failed_count": 5,
    "success_rate": 97.5
  }
}
```

---

## 🔄 n8n Integration

### Quick Setup

1. **Start n8n**:

   ```bash
   docker-compose up -d n8n
   # OR
   npx n8n
   ```

2. **Access n8n**: Open http://localhost:5678

3. **Import Workflow**:

   - Click hamburger menu (☰) → Import from File
   - Select `n8n/workflow_production.json`
   - Click Import

4. **Configure Environment**:

   - Ensure MCP server is running
   - Update URLs if needed (default: localhost:8000)

5. **Run Workflow**:
   - Click "Execute Workflow"
   - Monitor progress through each node

### Workflow Features

The production workflow includes:

- ✅ **Multiple Triggers**: Manual, Webhook, Scheduled
- ✅ **Health Check**: Validates MCP server before running
- ✅ **Error Handling**: Captures and reports failures
- ✅ **Validation**: Validates each step's output
- ✅ **Summary**: Compiles comprehensive results

### Detailed n8n Guide

See [docs/N8N_SETUP_GUIDE.md](docs/N8N_SETUP_GUIDE.md) for:

- Complete installation instructions
- Node-by-node configuration
- Troubleshooting guide
- Advanced customization

---

## ⚙️ Configuration

### Environment Variables

Create `.env` from `.env.example`:

```bash
cp .env.example .env
```

Key variables:

| Variable          | Default               | Description          |
| ----------------- | --------------------- | -------------------- |
| `MCP_SERVER_URL`  | http://localhost:8000 | MCP server address   |
| `DATABASE_PATH`   | storage/leads.db      | SQLite database path |
| `LOG_LEVEL`       | INFO                  | Logging verbosity    |
| `LEAD_COUNT`      | 200                   | Default lead count   |
| `ENRICHMENT_MODE` | offline               | Default enrichment   |
| `SEND_MODE`       | dry_run               | Default send mode    |
| `RATE_LIMIT`      | 10                    | Messages per minute  |
| `SMTP_HOST`       | localhost             | SMTP server          |
| `SMTP_PORT`       | 1025                  | SMTP port (Mailhog)  |

### SMTP Configuration

**For Testing (Mailhog)**:

```env
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USE_TLS=false
```

**For Production (Gmail)**:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
```

---

## 🧪 Testing

### Run All Tests

```bash
pytest tests/ -v
```

### Run Specific Tests

```bash
# Lead generator tests
pytest tests/test_lead_generator.py -v

# Enrichment tests
pytest tests/test_enrichment.py -v

# Message generator tests
pytest tests/test_message_generator.py -v

# API integration tests
pytest tests/test_api.py -v
```

### Test Coverage

```bash
pytest tests/ --cov=backend --cov-report=html
open htmlcov/index.html
```

---

## 📚 API Documentation

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### API Endpoints

| Method | Endpoint                        | Description          |
| ------ | ------------------------------- | -------------------- |
| GET    | `/health`                       | Health check         |
| GET    | `/mcp/tools`                    | List available tools |
| POST   | `/mcp/invoke/generate_leads`    | Generate leads       |
| POST   | `/mcp/invoke/enrich_leads`      | Enrich leads         |
| POST   | `/mcp/invoke/generate_messages` | Generate messages    |
| POST   | `/mcp/invoke/send_outreach`     | Send messages        |
| GET    | `/mcp/invoke/get_status`        | Get pipeline status  |
| GET    | `/api/leads`                    | List all leads       |
| GET    | `/api/metrics`                  | Get metrics          |

---

## 🔍 Troubleshooting

### Common Issues

#### "Connection Refused" to MCP Server

```bash
# Check if server is running
curl http://localhost:8000/health

# Start the server
python -m uvicorn backend.mcp_server.server:app --port 8000
```

#### "Module Not Found" Errors

```bash
# Ensure you're in virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

#### Database Locked

```bash
# Reset database
python scripts/db_manager.py reset --yes
```

#### n8n Cannot Connect to MCP Server

If running n8n in Docker:

```
# Use host.docker.internal instead of localhost
http://host.docker.internal:8000/mcp/invoke/...
```

### Health Check

```bash
python scripts/health_check.py --all
```

### View Logs

```bash
# Docker logs
docker-compose logs -f mcp-server

# Python logs
tail -f logs/mcp_server.log
```

---

## 📁 Project Structure

```
mcp-lead-gen/
├── backend/                    # Python backend
│   ├── mcp_server/            # MCP server implementation
│   │   ├── __init__.py
│   │   ├── models.py          # Pydantic data models
│   │   ├── server.py          # FastAPI MCP server
│   │   ├── lead_generator.py  # Lead generation
│   │   ├── enrichment.py      # Lead enrichment
│   │   ├── message_generator.py # Message creation
│   │   └── outreach_sender.py # Message sending
│   ├── agent/                 # Orchestration agent
│   │   └── pipeline_agent.py
│   ├── storage/               # Data persistence
│   │   └── database.py        # SQLite manager
│   └── utils/                 # Utilities
│       ├── logging_config.py
│       ├── rate_limiter.py
│       └── validators.py
├── frontend/                  # Streamlit dashboard
│   └── app.py
├── n8n/                       # n8n workflows
│   ├── workflow.json          # Basic workflow
│   └── workflow_production.json # Production workflow
├── tests/                     # Test suite
│   ├── conftest.py
│   ├── test_lead_generator.py
│   ├── test_enrichment.py
│   ├── test_message_generator.py
│   └── test_api.py
├── scripts/                   # Utility scripts
│   ├── health_check.py
│   ├── db_manager.py
│   └── import_n8n_workflow.py
├── docs/                      # Documentation
│   └── N8N_SETUP_GUIDE.md
├── storage/                   # Data directory
├── docker-compose.yml         # Docker services
├── Dockerfile                 # MCP server image
├── Dockerfile.frontend        # Streamlit image
├── requirements.txt           # Python dependencies
├── .env.example              # Environment template
├── .gitignore
├── pytest.ini
├── start.py                   # Quick start script
├── run_pipeline.py           # CLI runner
├── LICENSE
└── README.md
```

---

## 📊 Example Outputs

### Generated Lead

```json
{
  "id": "lead_a1b2c3d4",
  "full_name": "Sarah Johnson",
  "company_name": "TechCorp Solutions",
  "role": "VP of Engineering",
  "industry": "Technology",
  "website": "https://techcorp.com",
  "email": "sarah.johnson@techcorp.com",
  "linkedin_url": "https://linkedin.com/in/sarahjohnson",
  "country": "United States",
  "status": "NEW"
}
```

### Enrichment Data

```json
{
  "lead_id": "lead_a1b2c3d4",
  "company_size": "medium",
  "persona": "Technical Leader",
  "pain_points": [
    "Scaling engineering teams efficiently",
    "Managing technical debt"
  ],
  "buying_triggers": ["Recent Series B funding", "Expanding engineering team"],
  "confidence_score": 85,
  "enrichment_mode": "offline"
}
```

### Generated Email

```
Subject: Quick idea for TechCorp's engineering scale

Hi Sarah,

I noticed TechCorp is expanding rapidly. Scaling engineering teams
while managing technical debt is a common challenge at your stage.

We've helped similar companies reduce deployment time by 40% while
maintaining code quality.

Would you be open to a 15-minute call next week to explore if this
could work for TechCorp?

Best,
[Your Name]
```

### Generated LinkedIn DM

```
Hi Sarah! Congrats on TechCorp's growth. I've helped VPs of Engineering
at similar companies tackle scaling challenges. Would love to share
some insights - open to connecting?
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

---

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [Faker](https://faker.readthedocs.io/) - Fake data generation
- [Streamlit](https://streamlit.io/) - Data app framework
- [n8n](https://n8n.io/) - Workflow automation
- [Mailhog](https://github.com/mailhog/MailHog) - Email testing

---

<div align="center">

**Built with ❤️ for the MCP ecosystem**

[Report Bug](https://github.com/yourusername/mcp-lead-gen/issues) · [Request Feature](https://github.com/yourusername/mcp-lead-gen/issues)

</div>
