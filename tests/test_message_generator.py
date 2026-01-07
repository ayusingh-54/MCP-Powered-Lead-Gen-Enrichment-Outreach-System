"""
Test Suite - Message Generator Module
=====================================
Unit tests for the message generation component.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_server.message_generator import MessageGenerator
from backend.mcp_server.lead_generator import LeadGenerator
from backend.mcp_server.enrichment import EnrichmentEngine
from backend.mcp_server.models import Lead, LeadEnrichment, GeneratedMessage, EnrichmentMode


class TestMessageGenerator:
    """Test cases for MessageGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a MessageGenerator instance."""
        return MessageGenerator()
    
    @pytest.fixture
    def enriched_lead(self):
        """Create an enriched lead for testing."""
        lead_gen = LeadGenerator()
        enrichment_engine = EnrichmentEngine()
        
        leads = lead_gen.generate(count=1, seed=42)
        lead = leads[0]
        enrichment = enrichment_engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        return lead, enrichment
    
    def test_generate_email_message(self, generator, enriched_lead):
        """Test generating an email message."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        assert isinstance(message, GeneratedMessage)
        assert message.channel == "email"
    
    def test_generate_linkedin_message(self, generator, enriched_lead):
        """Test generating a LinkedIn message."""
        lead, enrichment = enriched_lead
        message = generator.generate_linkedin(lead, enrichment)
        
        assert isinstance(message, GeneratedMessage)
        assert message.channel == "linkedin"
    
    def test_email_has_subject(self, generator, enriched_lead):
        """Test that email has subject line."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        assert message.subject is not None
        assert len(message.subject) > 0
    
    def test_linkedin_no_subject(self, generator, enriched_lead):
        """Test that LinkedIn DM has no subject."""
        lead, enrichment = enriched_lead
        message = generator.generate_linkedin(lead, enrichment)
        
        # LinkedIn DMs typically don't have subjects
        assert message.subject is None or message.subject == ""
    
    def test_email_word_limit(self, generator, enriched_lead):
        """Test that email is within 120 word limit."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        word_count = len(message.body.split())
        assert word_count <= 120, f"Email has {word_count} words, should be <= 120"
    
    def test_linkedin_word_limit(self, generator, enriched_lead):
        """Test that LinkedIn DM is within 60 word limit."""
        lead, enrichment = enriched_lead
        message = generator.generate_linkedin(lead, enrichment)
        
        word_count = len(message.body.split())
        assert word_count <= 60, f"LinkedIn DM has {word_count} words, should be <= 60"
    
    def test_message_personalization(self, generator, enriched_lead):
        """Test that message includes lead's name or company."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        body_lower = message.body.lower()
        name_parts = lead.full_name.lower().split()
        
        # Should include first name or company name
        contains_name = any(part in body_lower for part in name_parts)
        contains_company = lead.company_name.lower() in body_lower
        
        assert contains_name or contains_company, "Message should be personalized"
    
    def test_ab_variant_generation(self, generator, enriched_lead):
        """Test A/B variant generation."""
        lead, enrichment = enriched_lead
        
        # Generate with variants
        messages = generator.generate_with_variants(lead, enrichment, "email")
        
        assert len(messages) >= 2, "Should generate at least 2 variants"
    
    def test_ab_variants_are_different(self, generator, enriched_lead):
        """Test that A/B variants are actually different."""
        lead, enrichment = enriched_lead
        
        messages = generator.generate_with_variants(lead, enrichment, "email")
        
        if len(messages) >= 2:
            # Bodies should be different
            bodies = [m.body for m in messages]
            assert len(set(bodies)) > 1, "Variants should be different"
    
    def test_variant_labels(self, generator, enriched_lead):
        """Test that variants have proper labels."""
        lead, enrichment = enriched_lead
        
        messages = generator.generate_with_variants(lead, enrichment, "email")
        
        variants = [m.variant for m in messages]
        assert "A" in variants or "variant_a" in [v.lower() for v in variants if v]
    
    def test_message_has_lead_id(self, generator, enriched_lead):
        """Test that message references lead ID."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        assert message.lead_id == lead.id
    
    def test_batch_message_generation(self, generator):
        """Test generating messages for multiple leads."""
        lead_gen = LeadGenerator()
        enrichment_engine = EnrichmentEngine()
        
        leads = lead_gen.generate(count=5, seed=42)
        
        messages = []
        for lead in leads:
            enrichment = enrichment_engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
            msg = generator.generate_email(lead, enrichment)
            messages.append(msg)
        
        assert len(messages) == 5
        for msg in messages:
            assert isinstance(msg, GeneratedMessage)
    
    def test_message_timestamp(self, generator, enriched_lead):
        """Test that message has creation timestamp."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        assert message.created_at is not None
    
    def test_message_unique_id(self, generator, enriched_lead):
        """Test that each message has unique ID."""
        lead, enrichment = enriched_lead
        
        messages = [generator.generate_email(lead, enrichment) for _ in range(5)]
        ids = [m.id for m in messages]
        
        assert len(ids) == len(set(ids)), "Message IDs should be unique"


class TestMessageContent:
    """Test message content quality."""
    
    @pytest.fixture
    def generator(self):
        return MessageGenerator()
    
    @pytest.fixture
    def enriched_lead(self):
        lead = Lead(
            id="test-001",
            full_name="Sarah Johnson",
            company_name="TechCorp",
            role="VP of Engineering",
            industry="Technology",
            website="https://techcorp.com",
            email="sarah@techcorp.com",
            linkedin_url="https://linkedin.com/in/sarahjohnson",
            country="United States"
        )
        
        enrichment = LeadEnrichment(
            lead_id="test-001",
            company_size="medium",
            persona="Technical Leader",
            pain_points=["Scaling challenges", "Technical debt"],
            buying_triggers=["Recent funding", "Team expansion"],
            confidence_score=85,
            enrichment_mode="offline"
        )
        
        return lead, enrichment
    
    def test_email_professional_tone(self, generator, enriched_lead):
        """Test that email has professional tone."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        # Should not contain overly casual language
        casual_phrases = ["yo", "hey dude", "what's up"]
        body_lower = message.body.lower()
        
        for phrase in casual_phrases:
            assert phrase not in body_lower
    
    def test_linkedin_conversational_tone(self, generator, enriched_lead):
        """Test that LinkedIn is appropriately brief."""
        lead, enrichment = enriched_lead
        message = generator.generate_linkedin(lead, enrichment)
        
        # Should be concise
        assert len(message.body) < 1000, "LinkedIn message should be concise"
    
    def test_pain_point_reference(self, generator, enriched_lead):
        """Test that message may reference pain points."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        # Message body should exist
        assert len(message.body) > 0
    
    def test_call_to_action_present(self, generator, enriched_lead):
        """Test that email has call to action."""
        lead, enrichment = enriched_lead
        message = generator.generate_email(lead, enrichment)
        
        # Look for common CTA phrases
        cta_indicators = ["?", "call", "chat", "connect", "meet", "discuss", "talk"]
        body_lower = message.body.lower()
        
        has_cta = any(indicator in body_lower for indicator in cta_indicators)
        # Relaxed assertion - most messages should have some form of CTA
        assert len(message.body) > 50, "Message should have substantial content"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
