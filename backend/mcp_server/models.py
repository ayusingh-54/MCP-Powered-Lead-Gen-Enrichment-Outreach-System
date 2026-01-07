"""
Pydantic Models for MCP Server
==============================
Defines all data structures used throughout the system:
- Lead models
- Enrichment models
- Message models
- API request/response models
"""

from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional, List, Literal
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class LeadStatus(str, Enum):
    """Pipeline status for tracking lead progress through the system."""
    NEW = "NEW"
    ENRICHED = "ENRICHED"
    MESSAGED = "MESSAGED"
    SENT = "SENT"
    FAILED = "FAILED"


class CompanySize(str, Enum):
    """Company size classification for enrichment."""
    SMALL = "small"          # 1-50 employees
    MEDIUM = "medium"        # 51-500 employees
    ENTERPRISE = "enterprise" # 500+ employees


class EnrichmentMode(str, Enum):
    """Enrichment processing mode."""
    OFFLINE = "offline"  # Rule-based heuristics
    AI = "ai"            # AI/LLM-powered (mock or local)


class SendMode(str, Enum):
    """Message sending mode."""
    DRY_RUN = "dry_run"  # Preview only, no actual sending
    LIVE = "live"        # Actually send messages


# =============================================================================
# LEAD MODELS
# =============================================================================

class Lead(BaseModel):
    """
    Core lead model representing a potential customer.
    All fields are validated to ensure syntactic correctness.
    """
    id: Optional[str] = Field(None, description="Unique lead identifier")
    full_name: str = Field(..., min_length=2, max_length=100, description="Full name of the lead")
    company_name: str = Field(..., min_length=1, max_length=200, description="Company name")
    role: str = Field(..., min_length=2, max_length=100, description="Job title/role")
    industry: str = Field(..., min_length=2, max_length=100, description="Industry sector")
    website: str = Field(..., description="Company website URL")
    email: str = Field(..., description="Contact email address")
    linkedin_url: str = Field(..., description="LinkedIn profile URL")
    country: str = Field(..., min_length=2, max_length=100, description="Country/region")
    status: LeadStatus = Field(default=LeadStatus.NEW, description="Pipeline status")
    created_at: Optional[datetime] = Field(None, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        use_enum_values = True


class LeadEnrichment(BaseModel):
    """
    Enrichment data added to a lead after processing.
    Contains company insights, persona classification, and buying signals.
    """
    lead_id: str = Field(..., description="Reference to the lead")
    company_size: CompanySize = Field(..., description="Estimated company size")
    persona: str = Field(..., description="Persona tag (e.g., 'VP Ops', 'Data Leader')")
    pain_points: List[str] = Field(..., min_items=2, max_items=3, description="2-3 pain points")
    buying_triggers: List[str] = Field(..., min_items=1, max_items=2, description="1-2 buying triggers")
    confidence_score: int = Field(..., ge=0, le=100, description="Confidence score 0-100")
    enrichment_mode: EnrichmentMode = Field(..., description="Mode used for enrichment")
    enriched_at: Optional[datetime] = Field(None, description="Enrichment timestamp")

    class Config:
        use_enum_values = True


# =============================================================================
# MESSAGE MODELS
# =============================================================================

class GeneratedMessage(BaseModel):
    """
    Generated outreach message for a lead.
    Supports both email and LinkedIn DM with A/B variants.
    """
    id: Optional[str] = Field(None, description="Unique message identifier")
    lead_id: str = Field(..., description="Reference to the lead")
    channel: Literal["email", "linkedin"] = Field(..., description="Communication channel")
    variant: Literal["A", "B"] = Field(..., description="A/B test variant")
    subject: Optional[str] = Field(None, description="Email subject (email only)")
    body: str = Field(..., description="Message body")
    word_count: int = Field(..., description="Word count of the body")
    cta: str = Field(..., description="Call-to-action included")
    referenced_insight: str = Field(..., description="Enrichment insight referenced")
    generated_at: Optional[datetime] = Field(None, description="Generation timestamp")


class OutreachResult(BaseModel):
    """
    Result of an outreach attempt.
    Tracks success/failure and retry information.
    """
    message_id: str = Field(..., description="Reference to the message")
    lead_id: str = Field(..., description="Reference to the lead")
    channel: str = Field(..., description="Communication channel used")
    status: Literal["sent", "failed", "dry_run"] = Field(..., description="Send status")
    attempt_count: int = Field(default=1, description="Number of attempts made")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    sent_at: Optional[datetime] = Field(None, description="Send timestamp")


# =============================================================================
# API REQUEST MODELS
# =============================================================================

class GenerateLeadsRequest(BaseModel):
    """Request model for generate_leads MCP tool."""
    count: int = Field(default=200, ge=1, le=1000, description="Number of leads to generate")
    seed: Optional[int] = Field(None, description="Random seed for reproducibility")
    industries: Optional[List[str]] = Field(None, description="Filter by specific industries")


class EnrichLeadsRequest(BaseModel):
    """Request model for enrich_leads MCP tool."""
    lead_ids: Optional[List[str]] = Field(None, description="Specific lead IDs to enrich (None = all NEW)")
    mode: EnrichmentMode = Field(default=EnrichmentMode.OFFLINE, description="Enrichment mode")
    batch_size: int = Field(default=50, ge=1, le=200, description="Batch size for processing")


class GenerateMessagesRequest(BaseModel):
    """Request model for generate_messages MCP tool."""
    lead_ids: Optional[List[str]] = Field(None, description="Specific lead IDs (None = all ENRICHED)")
    channels: List[Literal["email", "linkedin"]] = Field(
        default=["email", "linkedin"],
        description="Channels to generate messages for"
    )
    generate_ab_variants: bool = Field(default=True, description="Generate A/B variants")


class SendOutreachRequest(BaseModel):
    """Request model for send_outreach MCP tool."""
    lead_ids: Optional[List[str]] = Field(None, description="Specific lead IDs (None = all MESSAGED)")
    mode: SendMode = Field(default=SendMode.DRY_RUN, description="Send mode")
    channel: Optional[Literal["email", "linkedin"]] = Field(None, description="Specific channel (None = both)")
    variant: Literal["A", "B"] = Field(default="A", description="Which variant to send")
    rate_limit: int = Field(default=10, ge=1, le=60, description="Messages per minute")
    max_retries: int = Field(default=2, ge=0, le=5, description="Max retry attempts")


class GetStatusRequest(BaseModel):
    """Request model for get_status MCP tool."""
    include_leads: bool = Field(default=False, description="Include lead details in response")
    include_messages: bool = Field(default=False, description="Include message details")
    lead_ids: Optional[List[str]] = Field(None, description="Filter by specific lead IDs")


# =============================================================================
# API RESPONSE MODELS
# =============================================================================

class PipelineMetrics(BaseModel):
    """Aggregated metrics for the pipeline."""
    total_leads: int = Field(..., description="Total leads in system")
    new_leads: int = Field(..., description="Leads in NEW status")
    enriched_leads: int = Field(..., description="Leads in ENRICHED status")
    messaged_leads: int = Field(..., description="Leads in MESSAGED status")
    sent_leads: int = Field(..., description="Leads in SENT status")
    failed_leads: int = Field(..., description="Leads in FAILED status")
    total_messages: int = Field(..., description="Total messages generated")
    messages_sent: int = Field(..., description="Messages successfully sent")
    messages_failed: int = Field(..., description="Messages that failed to send")
    last_updated: datetime = Field(..., description="Last metrics update time")


class ToolResponse(BaseModel):
    """Standard response wrapper for all MCP tool calls."""
    success: bool = Field(..., description="Whether the operation succeeded")
    tool_name: str = Field(..., description="Name of the tool that was called")
    message: str = Field(..., description="Human-readable status message")
    data: Optional[dict] = Field(None, description="Tool-specific response data")
    metrics: Optional[PipelineMetrics] = Field(None, description="Current pipeline metrics")
    error: Optional[str] = Field(None, description="Error message if failed")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Response timestamp")


# =============================================================================
# MCP TOOL DEFINITION MODELS
# =============================================================================

class MCPToolParameter(BaseModel):
    """Parameter definition for an MCP tool."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    required: bool = Field(default=False, description="Whether parameter is required")
    default: Optional[str] = Field(None, description="Default value")


class MCPToolDefinition(BaseModel):
    """Full definition of an MCP tool for discovery."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: List[MCPToolParameter] = Field(..., description="Tool parameters")
    returns: str = Field(..., description="Return type description")


class MCPServerInfo(BaseModel):
    """MCP server information for client discovery."""
    name: str = Field(default="lead-gen-mcp-server", description="Server name")
    version: str = Field(default="1.0.0", description="Server version")
    description: str = Field(
        default="MCP server for lead generation, enrichment, and outreach",
        description="Server description"
    )
    tools: List[MCPToolDefinition] = Field(..., description="Available tools")
