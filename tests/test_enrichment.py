"""
Test Suite - Enrichment Module
==============================
Unit tests for the lead enrichment component.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_server.enrichment import EnrichmentEngine
from backend.mcp_server.lead_generator import LeadGenerator
from backend.mcp_server.models import Lead, LeadEnrichment, EnrichmentMode, CompanySize


class TestEnrichmentEngine:
    """Test cases for EnrichmentEngine class."""
    
    @pytest.fixture
    def engine(self):
        """Create an EnrichmentEngine instance."""
        return EnrichmentEngine()
    
    @pytest.fixture
    def sample_leads(self):
        """Generate sample leads for testing."""
        generator = LeadGenerator()
        return generator.generate(count=10, seed=42)
    
    def test_enrich_single_lead_offline(self, engine, sample_leads):
        """Test enriching a single lead in offline mode."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert isinstance(enrichment, LeadEnrichment)
        assert enrichment.lead_id == lead.id
    
    def test_enrichment_has_pain_points(self, engine, sample_leads):
        """Test that enrichment includes pain points."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert enrichment.pain_points is not None
        assert len(enrichment.pain_points) >= 2
        assert len(enrichment.pain_points) <= 3
    
    def test_enrichment_has_buying_triggers(self, engine, sample_leads):
        """Test that enrichment includes buying triggers."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert enrichment.buying_triggers is not None
        assert len(enrichment.buying_triggers) >= 1
        assert len(enrichment.buying_triggers) <= 2
    
    def test_enrichment_has_persona(self, engine, sample_leads):
        """Test that enrichment includes persona."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert enrichment.persona is not None
        assert len(enrichment.persona) > 0
    
    def test_enrichment_has_company_size(self, engine, sample_leads):
        """Test that enrichment includes company size."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert enrichment.company_size is not None
        assert enrichment.company_size in [s.value for s in CompanySize]
    
    def test_enrichment_has_confidence_score(self, engine, sample_leads):
        """Test that enrichment includes confidence score."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert enrichment.confidence_score is not None
        assert 0 <= enrichment.confidence_score <= 100
    
    def test_enrichment_mode_stored(self, engine, sample_leads):
        """Test that enrichment mode is stored correctly."""
        lead = sample_leads[0]
        
        enrichment_offline = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        assert enrichment_offline.enrichment_mode == EnrichmentMode.OFFLINE.value
    
    def test_batch_enrichment(self, engine, sample_leads):
        """Test enriching multiple leads."""
        enrichments = engine.enrich_batch(sample_leads, mode=EnrichmentMode.OFFLINE)
        
        assert len(enrichments) == len(sample_leads)
        for enrichment in enrichments:
            assert isinstance(enrichment, LeadEnrichment)
    
    def test_ai_mode_enrichment(self, engine, sample_leads):
        """Test AI mode enrichment (mock)."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.AI)
        
        assert isinstance(enrichment, LeadEnrichment)
        assert enrichment.enrichment_mode == EnrichmentMode.AI.value
    
    def test_persona_based_on_role(self, engine):
        """Test that persona is influenced by role."""
        # Create leads with different roles
        vp_lead = Lead(
            id="vp-001",
            full_name="Jane Smith",
            company_name="Tech Corp",
            role="VP Operations",
            industry="Technology",
            website="https://techcorp.com",
            email="jane@techcorp.com",
            linkedin_url="https://linkedin.com/in/janesmith",
            country="United States"
        )
        
        enrichment = engine.enrich(vp_lead, mode=EnrichmentMode.OFFLINE)
        
        # Persona should be set
        assert enrichment.persona is not None
    
    def test_pain_points_are_strings(self, engine, sample_leads):
        """Test that pain points are strings."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        for pain_point in enrichment.pain_points:
            assert isinstance(pain_point, str)
            assert len(pain_point) > 0
    
    def test_buying_triggers_are_strings(self, engine, sample_leads):
        """Test that buying triggers are strings."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        for trigger in enrichment.buying_triggers:
            assert isinstance(trigger, str)
            assert len(trigger) > 0
    
    def test_enrichment_timestamp(self, engine, sample_leads):
        """Test that enrichment has timestamp."""
        lead = sample_leads[0]
        enrichment = engine.enrich(lead, mode=EnrichmentMode.OFFLINE)
        
        assert enrichment.enriched_at is not None


class TestEnrichmentRules:
    """Test enrichment rule engine."""
    
    @pytest.fixture
    def engine(self):
        return EnrichmentEngine()
    
    def test_tech_industry_pain_points(self, engine):
        """Test that tech industry gets relevant pain points."""
        tech_lead = Lead(
            id="tech-001",
            full_name="John Tech",
            company_name="Software Inc",
            role="CTO",
            industry="Technology",
            website="https://software.com",
            email="john@software.com",
            linkedin_url="https://linkedin.com/in/johntech",
            country="United States"
        )
        
        enrichment = engine.enrich(tech_lead, mode=EnrichmentMode.OFFLINE)
        
        # Should have pain points
        assert len(enrichment.pain_points) >= 2
    
    def test_finance_industry_pain_points(self, engine):
        """Test that finance industry gets relevant pain points."""
        finance_lead = Lead(
            id="fin-001",
            full_name="Jane Finance",
            company_name="Bank Corp",
            role="CFO",
            industry="Finance",
            website="https://bankcorp.com",
            email="jane@bankcorp.com",
            linkedin_url="https://linkedin.com/in/janefinance",
            country="United States"
        )
        
        enrichment = engine.enrich(finance_lead, mode=EnrichmentMode.OFFLINE)
        
        # Should have pain points
        assert len(enrichment.pain_points) >= 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
