"""
Outreach Sender Module
======================
Handles sending outreach messages via various channels:
- Email (SMTP or Mailhog)
- LinkedIn (simulated)

Features:
- Dry-run mode (preview only)
- Live mode with actual sending
- Retry logic with exponential backoff
- Rate limiting (configurable messages per minute)
- Structured logging
"""

import smtplib
import time
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import os

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_server.models import (
    GeneratedMessage, OutreachResult, SendMode, LeadStatus
)
from utils.rate_limiter import RateLimiter, RetryConfig, retry_with_backoff


# Configure logging
logger = logging.getLogger("leadgen.outreach")


# =============================================================================
# SMTP CONFIGURATION
# =============================================================================

class SMTPConfig:
    """SMTP server configuration."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 1025,  # Mailhog default
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = False,
        sender_email: str = "outreach@leadgen.demo"
    ):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.sender_email = sender_email
    
    @classmethod
    def from_env(cls) -> "SMTPConfig":
        """Create config from environment variables."""
        # Use 'mailhog' hostname when running in Docker, localhost otherwise
        default_host = "mailhog" if os.getenv("DOCKER_ENV", "false").lower() == "true" else "localhost"
        smtp_host = os.getenv("SMTP_HOST", default_host)
        
        # If SMTP_HOST is localhost but we're in Docker, use mailhog
        if smtp_host == "localhost" and os.path.exists("/.dockerenv"):
            smtp_host = "mailhog"
            
        return cls(
            host=smtp_host,
            port=int(os.getenv("SMTP_PORT", "1025")),
            username=os.getenv("SMTP_USERNAME"),
            password=os.getenv("SMTP_PASSWORD"),
            use_tls=os.getenv("SMTP_USE_TLS", "false").lower() == "true",
            sender_email=os.getenv("SMTP_SENDER_EMAIL", "outreach@leadgen.demo")
        )


# =============================================================================
# OUTREACH SENDER ENGINE
# =============================================================================

class OutreachSender:
    """
    Sends outreach messages with rate limiting and retry logic.
    Supports both dry-run and live modes.
    """
    
    def __init__(
        self,
        mode: SendMode = SendMode.DRY_RUN,
        smtp_config: Optional[SMTPConfig] = None,
        rate_limit: int = 10,  # messages per minute
        max_retries: int = 2
    ):
        """
        Initialize outreach sender.
        
        Args:
            mode: Send mode (dry_run or live)
            smtp_config: SMTP configuration for email
            rate_limit: Maximum messages per minute
            max_retries: Maximum retry attempts
        """
        self.mode = mode
        self.smtp_config = smtp_config or SMTPConfig.from_env()
        self.rate_limiter = RateLimiter(max_requests=rate_limit, time_window=60)
        self.max_retries = max_retries
        
        # Retry configuration
        self.retry_config = RetryConfig(
            max_retries=max_retries,
            base_delay=2.0,
            max_delay=30.0,
            exponential_backoff=True
        )
        
        # Results tracking
        self.results: List[OutreachResult] = []
    
    def _log_send_attempt(
        self,
        message: GeneratedMessage,
        recipient: str,
        success: bool,
        error: Optional[str] = None
    ):
        """Log a send attempt with structured data."""
        log_data = {
            "message_id": message.id,
            "lead_id": message.lead_id,
            "channel": message.channel,
            "variant": message.variant,
            "recipient": recipient,
            "success": success,
            "mode": self.mode.value,
            "error": error
        }
        
        if success:
            logger.info(f"Message sent successfully: {message.channel} to {recipient}", extra=log_data)
        else:
            logger.error(f"Message send failed: {message.channel} to {recipient} - {error}", extra=log_data)
    
    def _send_email_live(
        self,
        message: GeneratedMessage,
        recipient_email: str,
        recipient_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Actually send an email via SMTP.
        
        Args:
            message: GeneratedMessage object
            recipient_email: Recipient email address
            recipient_name: Recipient name for display
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.smtp_config.sender_email
            msg["To"] = recipient_email
            msg["Subject"] = message.subject or f"Message for {recipient_name}"
            
            # Add body
            msg.attach(MIMEText(message.body, "plain"))
            
            # Connect and send
            if self.smtp_config.use_tls:
                server = smtplib.SMTP(self.smtp_config.host, self.smtp_config.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.smtp_config.host, self.smtp_config.port)
            
            # Authenticate if credentials provided
            if self.smtp_config.username and self.smtp_config.password:
                server.login(self.smtp_config.username, self.smtp_config.password)
            
            # Send email
            server.sendmail(
                self.smtp_config.sender_email,
                recipient_email,
                msg.as_string()
            )
            server.quit()
            
            return True, None
            
        except smtplib.SMTPException as e:
            return False, f"SMTP error: {str(e)}"
        except Exception as e:
            return False, f"Email error: {str(e)}"
    
    def _send_linkedin_live(
        self,
        message: GeneratedMessage,
        linkedin_url: str,
        recipient_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Simulate sending a LinkedIn DM.
        In production, this would use a compliant API.
        
        Args:
            message: GeneratedMessage object
            linkedin_url: Recipient LinkedIn URL
            recipient_name: Recipient name
            
        Returns:
            Tuple of (success, error_message)
        """
        # SIMULATION: LinkedIn DM sending
        # In a real implementation, you would use LinkedIn's API
        # which requires OAuth and has strict rate limits
        
        logger.info(f"[SIMULATED] LinkedIn DM to {recipient_name} ({linkedin_url})")
        logger.debug(f"[SIMULATED] Message body: {message.body[:100]}...")
        
        # Simulate some network latency
        time.sleep(0.5)
        
        # Simulate occasional failures (5% failure rate)
        import random
        if random.random() < 0.05:
            return False, "Simulated LinkedIn rate limit"
        
        return True, None
    
    def _send_dry_run(
        self,
        message: GeneratedMessage,
        recipient: str,
        recipient_name: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Perform a dry-run send (log only, no actual sending).
        
        Args:
            message: GeneratedMessage object
            recipient: Recipient identifier (email or LinkedIn URL)
            recipient_name: Recipient name
            
        Returns:
            Tuple of (success, error_message)
        """
        logger.info(
            f"[DRY RUN] Would send {message.channel} to {recipient_name}\n"
            f"  Recipient: {recipient}\n"
            f"  Subject: {message.subject or 'N/A'}\n"
            f"  Body preview: {message.body[:100]}...\n"
            f"  Word count: {message.word_count}"
        )
        
        return True, None
    
    def send_message(
        self,
        message: GeneratedMessage,
        lead: Dict
    ) -> OutreachResult:
        """
        Send a single message with retry logic.
        
        Args:
            message: GeneratedMessage to send
            lead: Lead dictionary with contact info
            
        Returns:
            OutreachResult with send status
        """
        # Apply rate limiting
        self.rate_limiter.acquire()
        
        recipient_name = lead.get("full_name", "Lead")
        
        # Determine recipient based on channel
        if message.channel == "email":
            recipient = lead.get("email", "")
        else:  # linkedin
            recipient = lead.get("linkedin_url", "")
        
        # Track attempts
        attempt = 0
        success = False
        error_message = None
        
        while attempt <= self.max_retries and not success:
            attempt += 1
            
            try:
                if self.mode == SendMode.DRY_RUN:
                    success, error_message = self._send_dry_run(
                        message, recipient, recipient_name
                    )
                elif message.channel == "email":
                    success, error_message = self._send_email_live(
                        message, recipient, recipient_name
                    )
                else:  # linkedin
                    success, error_message = self._send_linkedin_live(
                        message, recipient, recipient_name
                    )
                
                if not success and attempt <= self.max_retries:
                    # Wait before retry with exponential backoff
                    wait_time = self.retry_config.base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Retry {attempt}/{self.max_retries} in {wait_time}s for {recipient}")
                    time.sleep(wait_time)
                    
            except Exception as e:
                error_message = str(e)
                if attempt <= self.max_retries:
                    wait_time = self.retry_config.base_delay * (2 ** (attempt - 1))
                    logger.warning(f"Exception on attempt {attempt}, retry in {wait_time}s: {e}")
                    time.sleep(wait_time)
        
        # Log the result
        self._log_send_attempt(message, recipient, success, error_message)
        
        # Create result
        result = OutreachResult(
            message_id=message.id or "",
            lead_id=message.lead_id,
            channel=message.channel,
            status="sent" if success else ("dry_run" if self.mode == SendMode.DRY_RUN else "failed"),
            attempt_count=attempt,
            error_message=error_message if not success else None,
            sent_at=datetime.utcnow() if success else None
        )
        
        self.results.append(result)
        return result
    
    def send_messages(
        self,
        messages: List[GeneratedMessage],
        leads_map: Dict[str, Dict]
    ) -> List[OutreachResult]:
        """
        Send multiple messages with rate limiting.
        
        Args:
            messages: List of messages to send
            leads_map: Dictionary mapping lead_id to lead data
            
        Returns:
            List of OutreachResult objects
        """
        results = []
        
        for message in messages:
            lead = leads_map.get(message.lead_id, {})
            
            if not lead:
                logger.warning(f"Lead not found for message {message.id}, skipping")
                continue
            
            result = self.send_message(message, lead)
            results.append(result)
        
        return results
    
    def get_summary(self) -> Dict:
        """
        Get summary of all send attempts.
        
        Returns:
            Dictionary with send statistics
        """
        total = len(self.results)
        sent = sum(1 for r in self.results if r.status == "sent")
        dry_run = sum(1 for r in self.results if r.status == "dry_run")
        failed = sum(1 for r in self.results if r.status == "failed")
        
        return {
            "total_attempts": total,
            "successful_sends": sent,
            "dry_run_previews": dry_run,
            "failed_sends": failed,
            "success_rate": (sent / total * 100) if total > 0 else 0,
            "mode": self.mode.value,
            "rate_limit_status": self.rate_limiter.get_status()
        }
    
    def reset_results(self):
        """Reset the results tracker."""
        self.results = []


# =============================================================================
# MODULE-LEVEL FUNCTIONS
# =============================================================================

def send_outreach(
    messages: List[GeneratedMessage],
    leads: List[Dict],
    mode: SendMode = SendMode.DRY_RUN,
    rate_limit: int = 10,
    max_retries: int = 2
) -> Tuple[List[OutreachResult], Dict]:
    """
    Convenience function to send outreach messages.
    
    Args:
        messages: List of messages to send
        leads: List of lead dictionaries
        mode: Send mode
        rate_limit: Messages per minute
        max_retries: Max retry attempts
        
    Returns:
        Tuple of (results, summary)
    """
    # Create leads map for quick lookup
    leads_map = {lead["id"]: lead for lead in leads}
    
    # Create sender
    sender = OutreachSender(
        mode=mode,
        rate_limit=rate_limit,
        max_retries=max_retries
    )
    
    # Send messages
    results = sender.send_messages(messages, leads_map)
    summary = sender.get_summary()
    
    return results, summary


if __name__ == "__main__":
    # Test outreach sending
    print("Testing Outreach Sender...")
    print("=" * 60)
    
    # Set up logging for testing
    logging.basicConfig(level=logging.INFO)
    
    # Sample data
    test_message = GeneratedMessage(
        id="msg-123",
        lead_id="lead-456",
        channel="email",
        variant="A",
        subject="Quick question about operations",
        body="Hi John, I noticed your company is in tech. Would love to connect!",
        word_count=15,
        cta="15-minute call",
        referenced_insight="scaling operations"
    )
    
    test_lead = {
        "id": "lead-456",
        "full_name": "John Smith",
        "email": "john@test.com",
        "linkedin_url": "https://linkedin.com/in/johnsmith"
    }
    
    # Test dry run
    print("\n--- DRY RUN MODE ---")
    results, summary = send_outreach(
        messages=[test_message],
        leads=[test_lead],
        mode=SendMode.DRY_RUN
    )
    print(f"Results: {len(results)}")
    print(f"Summary: {summary}")
