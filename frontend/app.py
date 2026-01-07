"""
Streamlit Frontend Dashboard
============================
Monitoring dashboard for the lead generation pipeline.

Features:
- Pipeline metrics overview
- Lead table with status
- Progress tracking
- Run pipeline button
- Dry-run / Live toggle
- Real-time updates
"""

import os
import time
import requests
import pandas as pd
import streamlit as st
from datetime import datetime
from typing import Dict, Optional

# =============================================================================
# CONFIGURATION
# =============================================================================

# Page configuration
st.set_page_config(
    page_title="Lead Gen Pipeline Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# MCP Server URL
MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8000")


# =============================================================================
# API CLIENT
# =============================================================================

class DashboardClient:
    """Client for communicating with the MCP server."""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.timeout = 120
    
    def get_metrics(self) -> Optional[Dict]:
        """Get pipeline metrics."""
        try:
            response = requests.get(
                f"{self.base_url}/api/metrics",
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to fetch metrics: {str(e)}")
            return None
    
    def get_leads(self, status: Optional[str] = None, limit: int = 100) -> Optional[Dict]:
        """Get leads with optional status filter."""
        try:
            params = {"limit": limit}
            if status:
                params["status"] = status
            
            response = requests.get(
                f"{self.base_url}/api/leads",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to fetch leads: {str(e)}")
            return None
    
    def invoke_tool(self, tool_name: str, params: Dict) -> Optional[Dict]:
        """Invoke an MCP tool."""
        try:
            response = requests.post(
                f"{self.base_url}/mcp/invoke/{tool_name}",
                json=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Tool invocation failed: {str(e)}")
            return None
    
    def health_check(self) -> bool:
        """Check server health."""
        try:
            response = requests.get(f"{self.base_url}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def reset_pipeline(self) -> bool:
        """Reset all pipeline data."""
        try:
            response = requests.post(f"{self.base_url}/api/reset", timeout=30)
            return response.status_code == 200
        except:
            return False


# Initialize client
client = DashboardClient(MCP_SERVER_URL)


# =============================================================================
# SESSION STATE
# =============================================================================

# Initialize session state
if "pipeline_running" not in st.session_state:
    st.session_state.pipeline_running = False

if "last_refresh" not in st.session_state:
    st.session_state.last_refresh = datetime.now()

if "current_step" not in st.session_state:
    st.session_state.current_step = "idle"


# =============================================================================
# UI COMPONENTS
# =============================================================================

def render_header():
    """Render the dashboard header."""
    st.title("📊 Lead Generation Pipeline Dashboard")
    st.markdown("Monitor and control your MCP-powered lead generation workflow")
    
    # Server status
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        if client.health_check():
            st.success(f"✅ Connected to MCP Server: {MCP_SERVER_URL}")
        else:
            st.error(f"❌ Cannot connect to MCP Server: {MCP_SERVER_URL}")
    
    with col2:
        st.info(f"Last refresh: {st.session_state.last_refresh.strftime('%H:%M:%S')}")
    
    with col3:
        if st.button("🔄 Refresh"):
            st.session_state.last_refresh = datetime.now()
            st.rerun()


def render_metrics(metrics: Dict):
    """Render pipeline metrics."""
    st.subheader("📈 Pipeline Metrics")
    
    # Main metrics row
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        st.metric(
            label="Total Leads",
            value=metrics.get("total_leads", 0),
            delta=None
        )
    
    with col2:
        st.metric(
            label="Enriched",
            value=metrics.get("enriched_leads", 0),
            delta=f"{metrics.get('new_leads', 0)} pending"
        )
    
    with col3:
        st.metric(
            label="Messages Generated",
            value=metrics.get("total_messages", 0),
            delta=None
        )
    
    with col4:
        st.metric(
            label="Sent",
            value=metrics.get("messages_sent", 0),
            delta=None
        )
    
    with col5:
        st.metric(
            label="Failed",
            value=metrics.get("messages_failed", 0),
            delta=None
        )
    
    # Progress bar
    total = metrics.get("total_leads", 0)
    if total > 0:
        sent = metrics.get("sent_leads", 0)
        progress = sent / total
        st.progress(progress, text=f"Pipeline Progress: {sent}/{total} leads completed ({progress*100:.1f}%)")
    
    # Status breakdown
    st.markdown("---")
    st.subheader("📊 Status Breakdown")
    
    status_data = {
        "Status": ["NEW", "ENRICHED", "MESSAGED", "SENT", "FAILED"],
        "Count": [
            metrics.get("new_leads", 0),
            metrics.get("enriched_leads", 0),
            metrics.get("messaged_leads", 0),
            metrics.get("sent_leads", 0),
            metrics.get("failed_leads", 0)
        ]
    }
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        df = pd.DataFrame(status_data)
        st.dataframe(df, use_container_width=True, hide_index=True)
    
    with col2:
        # Simple bar chart
        chart_df = pd.DataFrame(status_data).set_index("Status")
        st.bar_chart(chart_df)


def render_controls():
    """Render pipeline control panel."""
    st.sidebar.title("⚙️ Pipeline Controls")
    
    # Mode selection
    st.sidebar.markdown("### Execution Mode")
    send_mode = st.sidebar.radio(
        "Send Mode",
        options=["dry_run", "live"],
        index=0,
        help="Dry-run: Preview only, Live: Actually send messages"
    )
    
    enrichment_mode = st.sidebar.radio(
        "Enrichment Mode",
        options=["offline", "ai"],
        index=0,
        help="Offline: Rule-based, AI: Mock LLM enrichment"
    )
    
    # Parameters
    st.sidebar.markdown("### Parameters")
    lead_count = st.sidebar.number_input(
        "Number of Leads",
        min_value=10,
        max_value=1000,
        value=200,
        step=10
    )
    
    seed = st.sidebar.number_input(
        "Random Seed (optional)",
        min_value=0,
        max_value=999999,
        value=42,
        help="Set for reproducible results"
    )
    
    rate_limit = st.sidebar.slider(
        "Rate Limit (msgs/min)",
        min_value=1,
        max_value=60,
        value=10
    )
    
    st.sidebar.markdown("---")
    
    # Run button
    st.sidebar.markdown("### Execute Pipeline")
    
    if st.sidebar.button("🚀 Run Full Pipeline", type="primary", use_container_width=True):
        run_full_pipeline(
            lead_count=lead_count,
            seed=seed,
            send_mode=send_mode,
            enrichment_mode=enrichment_mode,
            rate_limit=rate_limit
        )
    
    # Individual step buttons
    st.sidebar.markdown("### Run Individual Steps")
    
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("Generate", use_container_width=True):
            run_step("generate_leads", {"count": lead_count, "seed": seed})
    
    with col2:
        if st.button("Enrich", use_container_width=True):
            run_step("enrich_leads", {"mode": enrichment_mode, "batch_size": 50})
    
    col3, col4 = st.sidebar.columns(2)
    
    with col3:
        if st.button("Messages", use_container_width=True):
            run_step("generate_messages", {"generate_ab_variants": True})
    
    with col4:
        if st.button("Send", use_container_width=True):
            run_step("send_outreach", {"mode": send_mode, "rate_limit": rate_limit})
    
    st.sidebar.markdown("---")
    
    # Reset button
    if st.sidebar.button("🗑️ Reset Pipeline", use_container_width=True):
        if client.reset_pipeline():
            st.sidebar.success("Pipeline reset successfully!")
            st.rerun()
        else:
            st.sidebar.error("Failed to reset pipeline")


def render_leads_table(leads_data: Dict):
    """Render the leads table."""
    st.subheader("📋 Leads Table")
    
    leads = leads_data.get("leads", [])
    
    if not leads:
        st.info("No leads found. Run the pipeline to generate leads.")
        return
    
    # Status filter
    status_filter = st.selectbox(
        "Filter by Status",
        options=["All", "NEW", "ENRICHED", "MESSAGED", "SENT", "FAILED"],
        index=0
    )
    
    # Convert to DataFrame
    df = pd.DataFrame(leads)
    
    # Apply filter
    if status_filter != "All":
        df = df[df["status"] == status_filter]
    
    # Select columns to display
    display_columns = ["full_name", "company_name", "role", "industry", "country", "status", "updated_at"]
    available_columns = [c for c in display_columns if c in df.columns]
    
    if available_columns:
        display_df = df[available_columns]
        
        # Format status with colors
        def status_color(val):
            colors = {
                "NEW": "background-color: #e3f2fd",
                "ENRICHED": "background-color: #e8f5e9",
                "MESSAGED": "background-color: #fff3e0",
                "SENT": "background-color: #c8e6c9",
                "FAILED": "background-color: #ffcdd2"
            }
            return colors.get(val, "")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            height=400
        )
        
        st.caption(f"Showing {len(display_df)} of {len(leads)} leads")
    else:
        st.warning("Unable to display leads table - missing expected columns")


def run_step(tool_name: str, params: Dict):
    """Run a single pipeline step."""
    with st.spinner(f"Running {tool_name}..."):
        result = client.invoke_tool(tool_name, params)
        
        if result:
            if result.get("success"):
                st.success(f"✅ {result.get('message', 'Step completed')}")
            else:
                st.error(f"❌ {result.get('error', 'Step failed')}")
        
        st.session_state.last_refresh = datetime.now()
        time.sleep(1)
        st.rerun()


def run_full_pipeline(lead_count: int, seed: int, send_mode: str, enrichment_mode: str, rate_limit: int):
    """Run the full pipeline."""
    st.session_state.pipeline_running = True
    
    progress_bar = st.progress(0, text="Starting pipeline...")
    status_text = st.empty()
    
    steps = [
        ("generate_leads", {"count": lead_count, "seed": seed}, "Generating leads..."),
        ("enrich_leads", {"mode": enrichment_mode, "batch_size": 50}, "Enriching leads..."),
        ("generate_messages", {"generate_ab_variants": True}, "Generating messages..."),
        ("send_outreach", {"mode": send_mode, "rate_limit": rate_limit, "max_retries": 2}, "Sending outreach...")
    ]
    
    for i, (tool_name, params, message) in enumerate(steps):
        progress = (i / len(steps))
        progress_bar.progress(progress, text=message)
        status_text.info(f"Step {i+1}/{len(steps)}: {message}")
        
        result = client.invoke_tool(tool_name, params)
        
        if not result or not result.get("success"):
            error_msg = result.get("error", "Unknown error") if result else "Failed to invoke tool"
            status_text.error(f"❌ Pipeline failed at {tool_name}: {error_msg}")
            st.session_state.pipeline_running = False
            return
        
        time.sleep(1)  # Brief pause between steps
    
    progress_bar.progress(1.0, text="Pipeline completed!")
    status_text.success("✅ Pipeline completed successfully!")
    
    st.session_state.pipeline_running = False
    st.session_state.last_refresh = datetime.now()
    
    time.sleep(2)
    st.rerun()


def render_messages_preview():
    """Render a preview of generated messages."""
    st.subheader("📧 Message Preview")
    
    # Get a sample lead with messages
    leads_data = client.get_leads(status="SENT", limit=5)
    
    if not leads_data or not leads_data.get("leads"):
        leads_data = client.get_leads(status="MESSAGED", limit=5)
    
    if not leads_data or not leads_data.get("leads"):
        st.info("No messages to preview. Run the message generation step first.")
        return
    
    # Get lead details with messages
    leads = leads_data.get("leads", [])
    
    if leads:
        selected_lead = st.selectbox(
            "Select Lead",
            options=leads,
            format_func=lambda x: f"{x.get('full_name', 'Unknown')} - {x.get('company_name', 'Unknown')}"
        )
        
        if selected_lead:
            # Display lead info
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Lead Info:**")
                st.write(f"Name: {selected_lead.get('full_name')}")
                st.write(f"Company: {selected_lead.get('company_name')}")
                st.write(f"Role: {selected_lead.get('role')}")
                st.write(f"Email: {selected_lead.get('email')}")
            
            with col2:
                st.markdown("**Status:**")
                st.write(f"Industry: {selected_lead.get('industry')}")
                st.write(f"Country: {selected_lead.get('country')}")
                st.write(f"Status: {selected_lead.get('status')}")
            
            st.markdown("---")
            st.markdown("*Note: Run the pipeline to see full message details*")


# =============================================================================
# MAIN APP
# =============================================================================

def main():
    """Main application entry point."""
    # Render header
    render_header()
    
    st.markdown("---")
    
    # Render sidebar controls
    render_controls()
    
    # Main content area
    # Get metrics
    metrics = client.get_metrics()
    
    if metrics:
        render_metrics(metrics)
    else:
        st.warning("Unable to fetch metrics. Is the MCP server running?")
    
    st.markdown("---")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Leads", "📧 Messages", "📊 Logs"])
    
    with tab1:
        leads_data = client.get_leads(limit=100)
        if leads_data:
            render_leads_table(leads_data)
    
    with tab2:
        render_messages_preview()
    
    with tab3:
        st.subheader("📊 Execution Logs")
        st.info("Logs are displayed in the MCP server console. Check the terminal running the server for detailed logs.")
        
        # Show recent activity based on metrics
        if metrics:
            st.markdown("**Recent Activity Summary:**")
            st.write(f"- Total leads processed: {metrics.get('total_leads', 0)}")
            st.write(f"- Messages generated: {metrics.get('total_messages', 0)}")
            st.write(f"- Successfully sent: {metrics.get('messages_sent', 0)}")
            st.write(f"- Failed: {metrics.get('messages_failed', 0)}")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style="text-align: center; color: #666;">
            MCP Lead Generation Pipeline Dashboard | Built with Streamlit<br>
            <small>Auto-refresh: Click the Refresh button or rerun the app</small>
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
