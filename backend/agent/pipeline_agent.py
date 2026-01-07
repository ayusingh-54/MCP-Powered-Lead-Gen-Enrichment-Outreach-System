"""
Pipeline Agent
==============
Orchestration agent that:
- Reads current pipeline state
- Decides which MCP tool to call next
- Executes the full pipeline workflow
- Handles retries and failures
- Provides progress updates

The agent follows a state machine approach:
NEW -> ENRICHED -> MESSAGED -> SENT/FAILED
"""

import os
import time
import json
import logging
import requests
from datetime import datetime
from typing import Optional, Dict, List, Callable
from enum import Enum
from dataclasses import dataclass

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("leadgen.agent")


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class AgentConfig:
    """Configuration for the pipeline agent."""
    mcp_server_url: str = "http://localhost:8000"
    lead_count: int = 200
    enrichment_mode: str = "offline"  # offline or ai
    send_mode: str = "dry_run"  # dry_run or live
    rate_limit: int = 10
    max_retries: int = 2
    batch_size: int = 50
    step_delay: float = 1.0  # Delay between steps in seconds
    seed: Optional[int] = None
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create config from environment variables."""
        return cls(
            mcp_server_url=os.getenv("MCP_SERVER_URL", "http://localhost:8000"),
            lead_count=int(os.getenv("LEAD_COUNT", "200")),
            enrichment_mode=os.getenv("ENRICHMENT_MODE", "offline"),
            send_mode=os.getenv("SEND_MODE", "dry_run"),
            rate_limit=int(os.getenv("RATE_LIMIT", "10")),
            max_retries=int(os.getenv("MAX_RETRIES", "2")),
            batch_size=int(os.getenv("BATCH_SIZE", "50")),
            step_delay=float(os.getenv("STEP_DELAY", "1.0")),
            seed=int(os.getenv("SEED")) if os.getenv("SEED") else None
        )


# =============================================================================
# PIPELINE STATE
# =============================================================================

class PipelineStep(str, Enum):
    """Pipeline execution steps."""
    IDLE = "idle"
    GENERATING = "generating"
    ENRICHING = "enriching"
    MESSAGING = "messaging"
    SENDING = "sending"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineState:
    """Current state of the pipeline."""
    step: PipelineStep = PipelineStep.IDLE
    total_leads: int = 0
    new_leads: int = 0
    enriched_leads: int = 0
    messaged_leads: int = 0
    sent_leads: int = 0
    failed_leads: int = 0
    total_messages: int = 0
    messages_sent: int = 0
    messages_failed: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert state to dictionary."""
        return {
            "step": self.step.value,
            "total_leads": self.total_leads,
            "new_leads": self.new_leads,
            "enriched_leads": self.enriched_leads,
            "messaged_leads": self.messaged_leads,
            "sent_leads": self.sent_leads,
            "failed_leads": self.failed_leads,
            "total_messages": self.total_messages,
            "messages_sent": self.messages_sent,
            "messages_failed": self.messages_failed,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_error": self.last_error
        }
    
    def update_from_metrics(self, metrics: Dict):
        """Update state from MCP metrics response."""
        self.total_leads = metrics.get("total_leads", 0)
        self.new_leads = metrics.get("new_leads", 0)
        self.enriched_leads = metrics.get("enriched_leads", 0)
        self.messaged_leads = metrics.get("messaged_leads", 0)
        self.sent_leads = metrics.get("sent_leads", 0)
        self.failed_leads = metrics.get("failed_leads", 0)
        self.total_messages = metrics.get("total_messages", 0)
        self.messages_sent = metrics.get("messages_sent", 0)
        self.messages_failed = metrics.get("messages_failed", 0)


# =============================================================================
# MCP CLIENT
# =============================================================================

class MCPClient:
    """
    Client for communicating with the MCP server.
    Handles HTTP requests and response parsing.
    """
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        """
        Initialize MCP client.
        
        Args:
            base_url: MCP server base URL
        """
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.timeout = 120  # 2 minute timeout for long operations
    
    def _invoke_tool(self, tool_name: str, params: Dict) -> Dict:
        """
        Invoke an MCP tool.
        
        Args:
            tool_name: Name of the tool to invoke
            params: Tool parameters
            
        Returns:
            Tool response dictionary
        """
        url = f"{self.base_url}/mcp/invoke/{tool_name}"
        
        logger.info(f"Invoking MCP tool: {tool_name}")
        logger.debug(f"Parameters: {json.dumps(params, indent=2)}")
        
        try:
            response = self.session.post(
                url,
                json=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Tool {tool_name} completed: success={result.get('success')}")
            
            return result
            
        except requests.exceptions.RequestException as e:
            logger.error(f"MCP tool invocation failed: {str(e)}")
            raise
    
    def generate_leads(
        self,
        count: int = 200,
        seed: Optional[int] = None,
        industries: Optional[List[str]] = None
    ) -> Dict:
        """Invoke generate_leads tool."""
        params = {"count": count}
        if seed is not None:
            params["seed"] = seed
        if industries:
            params["industries"] = industries
        
        return self._invoke_tool("generate_leads", params)
    
    def enrich_leads(
        self,
        lead_ids: Optional[List[str]] = None,
        mode: str = "offline",
        batch_size: int = 50
    ) -> Dict:
        """Invoke enrich_leads tool."""
        params = {
            "mode": mode,
            "batch_size": batch_size
        }
        if lead_ids:
            params["lead_ids"] = lead_ids
        
        return self._invoke_tool("enrich_leads", params)
    
    def generate_messages(
        self,
        lead_ids: Optional[List[str]] = None,
        channels: List[str] = None,
        generate_ab_variants: bool = True
    ) -> Dict:
        """Invoke generate_messages tool."""
        params = {
            "generate_ab_variants": generate_ab_variants
        }
        if lead_ids:
            params["lead_ids"] = lead_ids
        if channels:
            params["channels"] = channels
        
        return self._invoke_tool("generate_messages", params)
    
    def send_outreach(
        self,
        lead_ids: Optional[List[str]] = None,
        mode: str = "dry_run",
        channel: Optional[str] = None,
        variant: str = "A",
        rate_limit: int = 10,
        max_retries: int = 2
    ) -> Dict:
        """Invoke send_outreach tool."""
        params = {
            "mode": mode,
            "variant": variant,
            "rate_limit": rate_limit,
            "max_retries": max_retries
        }
        if lead_ids:
            params["lead_ids"] = lead_ids
        if channel:
            params["channel"] = channel
        
        return self._invoke_tool("send_outreach", params)
    
    def get_status(
        self,
        include_leads: bool = False,
        include_messages: bool = False
    ) -> Dict:
        """Invoke get_status tool."""
        params = {
            "include_leads": include_leads,
            "include_messages": include_messages
        }
        
        return self._invoke_tool("get_status", params)
    
    def get_metrics(self) -> Dict:
        """Get pipeline metrics directly."""
        url = f"{self.base_url}/api/metrics"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get metrics: {str(e)}")
            raise
    
    def health_check(self) -> bool:
        """Check if MCP server is healthy."""
        url = f"{self.base_url}/health"
        
        try:
            response = self.session.get(url, timeout=10)
            return response.status_code == 200
        except:
            return False


# =============================================================================
# PIPELINE AGENT
# =============================================================================

class PipelineAgent:
    """
    Orchestration agent that manages the lead generation pipeline.
    Uses a state machine approach to decide which MCP tool to call next.
    """
    
    def __init__(
        self,
        config: Optional[AgentConfig] = None,
        progress_callback: Optional[Callable[[PipelineState], None]] = None
    ):
        """
        Initialize the pipeline agent.
        
        Args:
            config: Agent configuration
            progress_callback: Optional callback for progress updates
        """
        self.config = config or AgentConfig.from_env()
        self.client = MCPClient(self.config.mcp_server_url)
        self.state = PipelineState()
        self.progress_callback = progress_callback
    
    def _update_state_from_response(self, response: Dict):
        """Update internal state from MCP response."""
        if response.get("metrics"):
            self.state.update_from_metrics(response["metrics"])
        
        if self.progress_callback:
            self.progress_callback(self.state)
    
    def _determine_next_step(self) -> PipelineStep:
        """
        Determine the next pipeline step based on current state.
        Implements the agent's decision logic.
        
        Returns:
            Next step to execute
        """
        # If there was an error, stay in failed state
        if self.state.step == PipelineStep.FAILED:
            return PipelineStep.FAILED
        
        # Check for completion
        if self.state.step == PipelineStep.COMPLETED:
            return PipelineStep.COMPLETED
        
        # If no leads exist, start generating
        if self.state.total_leads == 0:
            return PipelineStep.GENERATING
        
        # If there are NEW leads, enrich them
        if self.state.new_leads > 0:
            return PipelineStep.ENRICHING
        
        # If there are ENRICHED leads without messages, generate messages
        if self.state.enriched_leads > 0:
            return PipelineStep.MESSAGING
        
        # If there are MESSAGED leads, send outreach
        if self.state.messaged_leads > 0:
            return PipelineStep.SENDING
        
        # All done
        return PipelineStep.COMPLETED
    
    def _execute_step(self, step: PipelineStep) -> bool:
        """
        Execute a single pipeline step.
        
        Args:
            step: Step to execute
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if step == PipelineStep.GENERATING:
                logger.info(f"Generating {self.config.lead_count} leads...")
                response = self.client.generate_leads(
                    count=self.config.lead_count,
                    seed=self.config.seed
                )
                
            elif step == PipelineStep.ENRICHING:
                logger.info(f"Enriching leads (mode: {self.config.enrichment_mode})...")
                response = self.client.enrich_leads(
                    mode=self.config.enrichment_mode,
                    batch_size=self.config.batch_size
                )
                
            elif step == PipelineStep.MESSAGING:
                logger.info("Generating messages...")
                response = self.client.generate_messages(
                    generate_ab_variants=True
                )
                
            elif step == PipelineStep.SENDING:
                logger.info(f"Sending outreach (mode: {self.config.send_mode})...")
                response = self.client.send_outreach(
                    mode=self.config.send_mode,
                    rate_limit=self.config.rate_limit,
                    max_retries=self.config.max_retries
                )
            
            else:
                return True  # No action needed for IDLE, COMPLETED, FAILED
            
            # Update state from response
            self._update_state_from_response(response)
            
            # Check for errors in response
            if not response.get("success"):
                self.state.last_error = response.get("error", "Unknown error")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Step {step.value} failed: {str(e)}")
            self.state.last_error = str(e)
            return False
    
    def run_pipeline(self, single_step: bool = False) -> PipelineState:
        """
        Run the full pipeline or a single step.
        
        Args:
            single_step: If True, execute only one step
            
        Returns:
            Final pipeline state
        """
        logger.info("=" * 60)
        logger.info("Starting Pipeline Agent")
        logger.info(f"MCP Server: {self.config.mcp_server_url}")
        logger.info(f"Mode: {self.config.send_mode}")
        logger.info("=" * 60)
        
        # Check server health
        if not self.client.health_check():
            logger.error("MCP server is not available!")
            self.state.step = PipelineStep.FAILED
            self.state.last_error = "MCP server not available"
            return self.state
        
        # Initialize state
        self.state.started_at = datetime.utcnow()
        
        # Get initial metrics
        try:
            metrics = self.client.get_metrics()
            self.state.update_from_metrics(metrics)
        except Exception as e:
            logger.warning(f"Failed to get initial metrics: {e}")
        
        # Main execution loop
        max_iterations = 10  # Prevent infinite loops
        iterations = 0
        
        while iterations < max_iterations:
            iterations += 1
            
            # Determine next step
            next_step = self._determine_next_step()
            logger.info(f"[Iteration {iterations}] Next step: {next_step.value}")
            
            # Check for termination
            if next_step in [PipelineStep.COMPLETED, PipelineStep.FAILED]:
                self.state.step = next_step
                break
            
            # Execute step
            self.state.step = next_step
            success = self._execute_step(next_step)
            
            if not success:
                self.state.step = PipelineStep.FAILED
                logger.error(f"Pipeline failed at step: {next_step.value}")
                break
            
            # Single step mode
            if single_step:
                break
            
            # Delay between steps
            if self.config.step_delay > 0:
                time.sleep(self.config.step_delay)
        
        # Finalize
        self.state.completed_at = datetime.utcnow()
        
        # Final status update
        try:
            metrics = self.client.get_metrics()
            self.state.update_from_metrics(metrics)
        except:
            pass
        
        # Log summary
        duration = (self.state.completed_at - self.state.started_at).total_seconds()
        logger.info("=" * 60)
        logger.info("Pipeline Execution Complete")
        logger.info(f"Status: {self.state.step.value}")
        logger.info(f"Duration: {duration:.2f} seconds")
        logger.info(f"Leads: {self.state.total_leads}")
        logger.info(f"Messages Sent: {self.state.messages_sent}")
        logger.info(f"Messages Failed: {self.state.messages_failed}")
        logger.info("=" * 60)
        
        return self.state
    
    def get_state(self) -> PipelineState:
        """Get current pipeline state."""
        # Refresh from server
        try:
            metrics = self.client.get_metrics()
            self.state.update_from_metrics(metrics)
        except:
            pass
        
        return self.state


# =============================================================================
# CLI INTERFACE
# =============================================================================

def main():
    """Main entry point for the agent CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Lead Generation Pipeline Agent")
    parser.add_argument("--server", default="http://localhost:8000", help="MCP server URL")
    parser.add_argument("--leads", type=int, default=200, help="Number of leads to generate")
    parser.add_argument("--mode", choices=["dry_run", "live"], default="dry_run", help="Send mode")
    parser.add_argument("--enrichment", choices=["offline", "ai"], default="offline", help="Enrichment mode")
    parser.add_argument("--seed", type=int, help="Random seed for reproducibility")
    parser.add_argument("--single-step", action="store_true", help="Execute only one step")
    
    args = parser.parse_args()
    
    # Create config
    config = AgentConfig(
        mcp_server_url=args.server,
        lead_count=args.leads,
        send_mode=args.mode,
        enrichment_mode=args.enrichment,
        seed=args.seed
    )
    
    # Create and run agent
    agent = PipelineAgent(config=config)
    state = agent.run_pipeline(single_step=args.single_step)
    
    # Print final state
    print("\nFinal State:")
    print(json.dumps(state.to_dict(), indent=2))


if __name__ == "__main__":
    main()
