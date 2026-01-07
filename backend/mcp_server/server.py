"""
MCP Server - FastAPI Implementation
===================================
Model Context Protocol server that exposes tools for lead generation pipeline:
- generate_leads: Create synthetic leads
- enrich_leads: Add business intelligence
- generate_messages: Create personalized outreach
- send_outreach: Send messages (dry-run or live)
- get_status: Monitor pipeline metrics

This server follows MCP conventions for tool discovery and invocation.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

# Import modules
from mcp_server.models import (
    Lead, LeadEnrichment, GeneratedMessage, OutreachResult,
    LeadStatus, EnrichmentMode, SendMode,
    GenerateLeadsRequest, EnrichLeadsRequest, GenerateMessagesRequest,
    SendOutreachRequest, GetStatusRequest,
    ToolResponse, PipelineMetrics, MCPToolDefinition, MCPToolParameter, MCPServerInfo
)
from mcp_server.lead_generator import LeadGenerator
from mcp_server.enrichment import EnrichmentEngine
from mcp_server.message_generator import MessageGenerator
from mcp_server.outreach_sender import OutreachSender, SMTPConfig
from storage.database import get_database_manager, DatabaseManager
from utils.logging_config import setup_logging, get_logger


# =============================================================================
# CONFIGURATION
# =============================================================================

# Set up logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))
logger = get_logger("mcp_server")

# Database path
DB_PATH = os.getenv("DATABASE_PATH", "storage/leads.db")


# =============================================================================
# LIFESPAN MANAGEMENT
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan handler.
    Initializes database and other resources on startup.
    """
    logger.info("Starting MCP Lead Generation Server...")
    
    # Initialize database
    db = get_database_manager(DB_PATH)
    logger.info(f"Database initialized at: {DB_PATH}")
    
    yield
    
    # Cleanup on shutdown
    logger.info("Shutting down MCP server...")


# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="MCP Lead Generation Server",
    description="Model Context Protocol server for lead generation, enrichment, and outreach",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_db() -> DatabaseManager:
    """Get database manager instance."""
    return get_database_manager(DB_PATH)


def create_success_response(
    tool_name: str,
    message: str,
    data: Optional[Dict] = None,
    include_metrics: bool = True
) -> ToolResponse:
    """Create a successful tool response."""
    db = get_db()
    metrics = db.get_pipeline_metrics() if include_metrics else None
    
    return ToolResponse(
        success=True,
        tool_name=tool_name,
        message=message,
        data=data,
        metrics=metrics,
        timestamp=datetime.utcnow()
    )


def create_error_response(
    tool_name: str,
    error: str,
    include_metrics: bool = True
) -> ToolResponse:
    """Create an error tool response."""
    db = get_db()
    metrics = db.get_pipeline_metrics() if include_metrics else None
    
    return ToolResponse(
        success=False,
        tool_name=tool_name,
        message="Operation failed",
        error=error,
        metrics=metrics,
        timestamp=datetime.utcnow()
    )


# =============================================================================
# MCP TOOL DEFINITIONS
# =============================================================================

MCP_TOOLS = [
    MCPToolDefinition(
        name="generate_leads",
        description="Generate synthetic but realistic leads with valid contact information",
        parameters=[
            MCPToolParameter(name="count", type="integer", description="Number of leads to generate (1-1000)", required=False, default="200"),
            MCPToolParameter(name="seed", type="integer", description="Random seed for reproducibility", required=False),
            MCPToolParameter(name="industries", type="array", description="Filter by specific industries", required=False)
        ],
        returns="List of generated leads with status NEW"
    ),
    MCPToolDefinition(
        name="enrich_leads",
        description="Enrich leads with company size, persona, pain points, and buying triggers",
        parameters=[
            MCPToolParameter(name="lead_ids", type="array", description="Specific lead IDs to enrich (None = all NEW)", required=False),
            MCPToolParameter(name="mode", type="string", description="Enrichment mode: 'offline' or 'ai'", required=False, default="offline"),
            MCPToolParameter(name="batch_size", type="integer", description="Batch size for processing", required=False, default="50")
        ],
        returns="List of enriched leads with status ENRICHED"
    ),
    MCPToolDefinition(
        name="generate_messages",
        description="Generate personalized email and LinkedIn messages for leads",
        parameters=[
            MCPToolParameter(name="lead_ids", type="array", description="Specific lead IDs (None = all ENRICHED)", required=False),
            MCPToolParameter(name="channels", type="array", description="Channels: ['email', 'linkedin']", required=False, default="['email', 'linkedin']"),
            MCPToolParameter(name="generate_ab_variants", type="boolean", description="Generate A/B variants", required=False, default="true")
        ],
        returns="List of generated messages with status MESSAGED"
    ),
    MCPToolDefinition(
        name="send_outreach",
        description="Send outreach messages via email or LinkedIn (supports dry-run mode)",
        parameters=[
            MCPToolParameter(name="lead_ids", type="array", description="Specific lead IDs (None = all MESSAGED)", required=False),
            MCPToolParameter(name="mode", type="string", description="Send mode: 'dry_run' or 'live'", required=False, default="dry_run"),
            MCPToolParameter(name="channel", type="string", description="Specific channel or None for both", required=False),
            MCPToolParameter(name="variant", type="string", description="Message variant: 'A' or 'B'", required=False, default="A"),
            MCPToolParameter(name="rate_limit", type="integer", description="Messages per minute", required=False, default="10"),
            MCPToolParameter(name="max_retries", type="integer", description="Max retry attempts", required=False, default="2")
        ],
        returns="List of send results with status SENT or FAILED"
    ),
    MCPToolDefinition(
        name="get_status",
        description="Get pipeline status and metrics",
        parameters=[
            MCPToolParameter(name="include_leads", type="boolean", description="Include lead details", required=False, default="false"),
            MCPToolParameter(name="include_messages", type="boolean", description="Include message details", required=False, default="false"),
            MCPToolParameter(name="lead_ids", type="array", description="Filter by specific lead IDs", required=False)
        ],
        returns="Pipeline metrics and optionally lead/message details"
    )
]


# =============================================================================
# API ENDPOINTS - MCP DISCOVERY
# =============================================================================

@app.get("/", tags=["Discovery"])
async def root():
    """Root endpoint with server info."""
    return {
        "name": "MCP Lead Generation Server",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "tools": "/mcp/tools",
            "invoke": "/mcp/invoke/{tool_name}"
        }
    }


@app.get("/mcp/info", response_model=MCPServerInfo, tags=["MCP"])
async def get_mcp_info():
    """Get MCP server information and available tools."""
    return MCPServerInfo(tools=MCP_TOOLS)


@app.get("/mcp/tools", tags=["MCP"])
async def list_tools():
    """List all available MCP tools."""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": [p.dict() for p in tool.parameters]
            }
            for tool in MCP_TOOLS
        ]
    }


# =============================================================================
# API ENDPOINTS - MCP TOOLS
# =============================================================================

@app.post("/mcp/invoke/generate_leads", response_model=ToolResponse, tags=["MCP Tools"])
async def generate_leads(request: GenerateLeadsRequest):
    """
    MCP Tool: Generate synthetic leads.
    
    Generates realistic-looking leads with valid:
    - Email addresses
    - Website URLs
    - LinkedIn URLs
    - Role/industry consistency
    """
    try:
        logger.info(f"generate_leads called: count={request.count}, seed={request.seed}")
        
        # Generate leads
        generator = LeadGenerator(seed=request.seed)
        leads = generator.generate_leads(
            count=request.count,
            industries=request.industries
        )
        
        # Store in database
        db = get_db()
        inserted_count = db.insert_leads(leads)
        
        logger.info(f"Generated and stored {inserted_count} leads")
        
        return create_success_response(
            tool_name="generate_leads",
            message=f"Successfully generated {inserted_count} leads",
            data={
                "leads_generated": inserted_count,
                "seed_used": request.seed,
                "industries": request.industries or generator.get_available_industries(),
                "sample_lead": leads[0].dict() if leads else None
            }
        )
        
    except Exception as e:
        logger.error(f"generate_leads failed: {str(e)}")
        return create_error_response("generate_leads", str(e))


@app.post("/mcp/invoke/enrich_leads", response_model=ToolResponse, tags=["MCP Tools"])
async def enrich_leads(request: EnrichLeadsRequest):
    """
    MCP Tool: Enrich leads with business intelligence.
    
    Adds:
    - Company size estimation
    - Persona classification
    - Pain points (2-3)
    - Buying triggers (1-2)
    - Confidence score
    """
    try:
        logger.info(f"enrich_leads called: mode={request.mode}, batch_size={request.batch_size}")
        
        db = get_db()
        
        # Get leads to enrich
        if request.lead_ids:
            leads = db.get_leads_by_ids(request.lead_ids)
        else:
            leads = db.get_leads_by_status(LeadStatus.NEW, limit=request.batch_size)
        
        if not leads:
            return create_success_response(
                tool_name="enrich_leads",
                message="No leads found to enrich",
                data={"leads_enriched": 0}
            )
        
        # Enrich leads
        engine = EnrichmentEngine(mode=request.mode)
        enriched_count = 0
        
        for lead in leads:
            enrichment = engine.enrich_lead(lead)
            db.insert_enrichment(enrichment)
            db.update_lead_status(lead["id"], LeadStatus.ENRICHED)
            enriched_count += 1
        
        logger.info(f"Enriched {enriched_count} leads using {request.mode.value} mode")
        
        return create_success_response(
            tool_name="enrich_leads",
            message=f"Successfully enriched {enriched_count} leads",
            data={
                "leads_enriched": enriched_count,
                "enrichment_mode": request.mode.value,
                "sample_enrichment": enrichment.dict() if enriched_count > 0 else None
            }
        )
        
    except Exception as e:
        logger.error(f"enrich_leads failed: {str(e)}")
        return create_error_response("enrich_leads", str(e))


@app.post("/mcp/invoke/generate_messages", response_model=ToolResponse, tags=["MCP Tools"])
async def generate_messages(request: GenerateMessagesRequest):
    """
    MCP Tool: Generate personalized outreach messages.
    
    Creates:
    - Cold emails (≤120 words)
    - LinkedIn DMs (≤60 words)
    - A/B variants for testing
    - References enrichment insights
    """
    try:
        logger.info(f"generate_messages called: channels={request.channels}, ab={request.generate_ab_variants}")
        
        db = get_db()
        
        # Get leads to generate messages for
        if request.lead_ids:
            leads = db.get_leads_by_ids(request.lead_ids)
            # Filter to only ENRICHED leads
            lead_ids = [l["id"] for l in leads if l["status"] == "ENRICHED"]
            leads = [l for l in leads if l["id"] in lead_ids]
        else:
            leads = db.get_leads_by_status(LeadStatus.ENRICHED, limit=100)
        
        if not leads:
            return create_success_response(
                tool_name="generate_messages",
                message="No enriched leads found for message generation",
                data={"messages_generated": 0}
            )
        
        # Generate messages
        generator = MessageGenerator()
        messages_count = 0
        
        for lead in leads:
            # Get enrichment
            enrichment = db.get_enrichment_by_lead_id(lead["id"])
            if not enrichment:
                continue
            
            # Generate messages
            messages = generator.generate_messages_for_lead(
                lead, enrichment,
                channels=request.channels,
                generate_ab=request.generate_ab_variants
            )
            
            # Store messages
            for message in messages:
                message.id = str(uuid.uuid4())
                db.insert_message(message)
                messages_count += 1
            
            # Update lead status
            db.update_lead_status(lead["id"], LeadStatus.MESSAGED)
        
        logger.info(f"Generated {messages_count} messages for {len(leads)} leads")
        
        return create_success_response(
            tool_name="generate_messages",
            message=f"Successfully generated {messages_count} messages",
            data={
                "messages_generated": messages_count,
                "leads_processed": len(leads),
                "channels": request.channels,
                "ab_variants": request.generate_ab_variants
            }
        )
        
    except Exception as e:
        logger.error(f"generate_messages failed: {str(e)}")
        return create_error_response("generate_messages", str(e))


@app.post("/mcp/invoke/send_outreach", response_model=ToolResponse, tags=["MCP Tools"])
async def send_outreach(request: SendOutreachRequest, background_tasks: BackgroundTasks):
    """
    MCP Tool: Send outreach messages.
    
    Features:
    - Dry-run mode (preview only)
    - Live mode (actual sending)
    - Rate limiting
    - Retry logic
    """
    logger.info(f"send_outreach called: mode={request.mode}, channel={request.channel}, variant={request.variant}")

    try:
        db = get_db()

        # Get messages to send (determine candidate leads/messages)
        if request.lead_ids:
            leads = db.get_leads_by_ids(request.lead_ids)
            lead_ids = [l["id"] for l in leads if l["status"] == "MESSAGED"]
        else:
            leads = db.get_leads_by_status(LeadStatus.MESSAGED, limit=100)
            lead_ids = [l["id"] for l in leads]

        if not lead_ids:
            return create_success_response(
                tool_name="send_outreach",
                message="No messaged leads found for outreach",
                data={"messages_sent": 0}
            )

        messages = db.get_messages_by_status(
            LeadStatus.MESSAGED,
            channel=request.channel,
            variant=request.variant
        )

        messages = [m for m in messages if m["lead_id"] in lead_ids]

        if not messages:
            return create_success_response(
                tool_name="send_outreach",
                message="No messages found to send",
                data={"messages_sent": 0}
            )

        # Schedule background task to perform sending to avoid client timeouts
        def run_send_outreach_background(msgs, lead_list, send_mode, rate_limit, max_retries):
            try:
                # Local imports to avoid blocking startup
                sender = OutreachSender(mode=send_mode, rate_limit=rate_limit, max_retries=max_retries)
                leads_map = {l["id"]: l for l in lead_list}

                sent_count = 0
                failed_count = 0

                for msg_data in msgs:
                    msg = GeneratedMessage(
                        id=msg_data["id"],
                        lead_id=msg_data["lead_id"],
                        channel=msg_data["channel"],
                        variant=msg_data["variant"],
                        subject=msg_data.get("subject"),
                        body=msg_data["body"],
                        word_count=msg_data.get("word_count", 0),
                        cta=msg_data.get("cta"),
                        referenced_insight=msg_data.get("referenced_insight")
                    )

                    lead = leads_map.get(msg.lead_id)
                    if not lead:
                        continue

                    result = sender.send_message(msg, lead)
                    db.insert_outreach_result(result)

                    if result.status in ["sent", "dry_run"]:
                        sent_count += 1
                        db.update_lead_status(msg.lead_id, LeadStatus.SENT)
                    else:
                        failed_count += 1
                        db.update_lead_status(msg.lead_id, LeadStatus.FAILED)

                summary = sender.get_summary()
                logger.info(f"Background send_outreach complete: sent={sent_count}, failed={failed_count}")
                # Optionally, store summary in DB or a status cache
                return True
            except Exception as ex:
                logger.error(f"Background send_outreach failed: {ex}")
                return False

        # Add to background tasks and return immediate response
        background_tasks.add_task(
            run_send_outreach_background,
            messages,
            leads,
            request.mode,
            request.rate_limit,
            request.max_retries
        )

        logger.info("send_outreach scheduled as background task")
        return create_success_response(
            tool_name="send_outreach",
            message="Outreach scheduled (running in background)",
            data={
                "messages_scheduled": len(messages),
                "mode": request.mode.value
            }
        )

    except Exception as e:
        logger.error(f"send_outreach scheduling failed: {str(e)}")
        return create_error_response("send_outreach", str(e))


@app.post("/mcp/invoke/get_status", response_model=ToolResponse, tags=["MCP Tools"])
async def get_status(request: GetStatusRequest):
    """
    MCP Tool: Get pipeline status and metrics.
    
    Returns:
    - Pipeline metrics (lead counts by status)
    - Message statistics
    - Optionally: detailed lead/message data
    """
    try:
        logger.info(f"get_status called: include_leads={request.include_leads}, include_messages={request.include_messages}")
        
        db = get_db()
        metrics = db.get_pipeline_metrics()
        
        data = {
            "pipeline_status": "active",
            "metrics": metrics.dict()
        }
        
        # Include leads if requested
        if request.include_leads:
            if request.lead_ids:
                leads = db.get_leads_by_ids(request.lead_ids)
            else:
                leads = db.get_all_leads(limit=100)
            data["leads"] = leads
        
        # Include messages if requested
        if request.include_messages:
            if request.lead_ids:
                messages = []
                for lead_id in request.lead_ids:
                    messages.extend(db.get_messages_by_lead_id(lead_id))
            else:
                # Get recent messages
                messages = []
                leads = db.get_all_leads(limit=50)
                for lead in leads:
                    messages.extend(db.get_messages_by_lead_id(lead["id"]))
            data["messages"] = messages[:100]  # Limit to 100
        
        return create_success_response(
            tool_name="get_status",
            message="Pipeline status retrieved successfully",
            data=data
        )
        
    except Exception as e:
        logger.error(f"get_status failed: {str(e)}")
        return create_error_response("get_status", str(e))


# =============================================================================
# API ENDPOINTS - ADDITIONAL UTILITIES
# =============================================================================

@app.get("/api/metrics", tags=["Utilities"])
async def get_metrics():
    """Get current pipeline metrics (for frontend dashboard)."""
    db = get_db()
    metrics = db.get_pipeline_metrics()
    return metrics.dict()


@app.get("/api/leads", tags=["Utilities"])
async def get_leads(
    status: Optional[str] = None,
    limit: int = 100
):
    """Get leads with optional status filter."""
    db = get_db()
    
    if status:
        try:
            lead_status = LeadStatus(status)
            leads = db.get_leads_by_status(lead_status, limit=limit)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    else:
        leads = db.get_all_leads(limit=limit)
    
    return {"leads": leads, "count": len(leads)}


@app.get("/api/leads/{lead_id}", tags=["Utilities"])
async def get_lead_detail(lead_id: str):
    """Get detailed information for a specific lead."""
    db = get_db()
    
    leads = db.get_leads_by_ids([lead_id])
    if not leads:
        raise HTTPException(status_code=404, detail="Lead not found")
    
    lead = leads[0]
    enrichment = db.get_enrichment_by_lead_id(lead_id)
    messages = db.get_messages_by_lead_id(lead_id)
    
    return {
        "lead": lead,
        "enrichment": enrichment,
        "messages": messages
    }


@app.post("/api/reset", tags=["Utilities"])
async def reset_pipeline():
    """Reset all pipeline data (for testing)."""
    db = get_db()
    db.clear_all_data()
    
    return {
        "success": True,
        "message": "Pipeline data has been reset"
    }


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    
    uvicorn.run(
        "server:app",
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )
