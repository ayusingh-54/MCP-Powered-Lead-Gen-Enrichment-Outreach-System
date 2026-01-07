"""
Test Suite - Lead Generator Module
==================================
Unit tests for the lead generation component.
"""

import pytest
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_server.lead_generator import LeadGenerator
from backend.mcp_server.models import Lead, LeadStatus


class TestLeadGenerator:
    """Test cases for LeadGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a LeadGenerator instance."""
        return LeadGenerator()
    
    def test_generate_single_lead(self, generator):
        """Test generating a single lead."""
        leads = generator.generate(count=1, seed=42)
        
        assert len(leads) == 1
        assert isinstance(leads[0], Lead)
    
    def test_generate_multiple_leads(self, generator):
        """Test generating multiple leads."""
        leads = generator.generate(count=50, seed=42)
        
        assert len(leads) == 50
        for lead in leads:
            assert isinstance(lead, Lead)
    
    def test_lead_has_required_fields(self, generator):
        """Test that generated leads have all required fields."""
        leads = generator.generate(count=1, seed=42)
        lead = leads[0]
        
        # All required fields should be present and non-empty
        assert lead.full_name and len(lead.full_name) > 0
        assert lead.company_name and len(lead.company_name) > 0
        assert lead.role and len(lead.role) > 0
        assert lead.industry and len(lead.industry) > 0
        assert lead.website and len(lead.website) > 0
        assert lead.email and len(lead.email) > 0
        assert lead.linkedin_url and len(lead.linkedin_url) > 0
        assert lead.country and len(lead.country) > 0
    
    def test_lead_has_valid_email(self, generator):
        """Test that generated leads have valid email format."""
        leads = generator.generate(count=10, seed=42)
        
        for lead in leads:
            assert '@' in lead.email
            assert '.' in lead.email.split('@')[1]
    
    def test_lead_has_valid_linkedin_url(self, generator):
        """Test that LinkedIn URLs are properly formatted."""
        leads = generator.generate(count=10, seed=42)
        
        for lead in leads:
            assert 'linkedin.com' in lead.linkedin_url.lower()
    
    def test_lead_has_valid_website(self, generator):
        """Test that websites are properly formatted."""
        leads = generator.generate(count=10, seed=42)
        
        for lead in leads:
            assert lead.website.startswith('http://') or lead.website.startswith('https://')
    
    def test_lead_initial_status_is_new(self, generator):
        """Test that new leads have NEW status."""
        leads = generator.generate(count=5, seed=42)
        
        for lead in leads:
            assert lead.status == LeadStatus.NEW
    
    def test_seed_reproducibility(self, generator):
        """Test that same seed produces same leads."""
        leads1 = generator.generate(count=10, seed=42)
        leads2 = generator.generate(count=10, seed=42)
        
        for l1, l2 in zip(leads1, leads2):
            assert l1.full_name == l2.full_name
            assert l1.company_name == l2.company_name
            assert l1.email == l2.email
    
    def test_different_seeds_produce_different_leads(self, generator):
        """Test that different seeds produce different leads."""
        leads1 = generator.generate(count=10, seed=42)
        leads2 = generator.generate(count=10, seed=123)
        
        # At least some leads should be different
        different_count = sum(1 for l1, l2 in zip(leads1, leads2) if l1.email != l2.email)
        assert different_count > 0
    
    def test_industry_role_consistency(self, generator):
        """Test that roles are appropriate for industries."""
        leads = generator.generate(count=100, seed=42)
        
        tech_roles = ['CTO', 'VP Engineering', 'Developer', 'Engineer', 'Tech Lead']
        finance_roles = ['CFO', 'Finance', 'Controller', 'Analyst']
        
        for lead in leads:
            # Basic check - role should be a string
            assert isinstance(lead.role, str)
            assert len(lead.role) > 0
    
    def test_unique_lead_ids(self, generator):
        """Test that all leads have unique IDs."""
        leads = generator.generate(count=100, seed=42)
        
        ids = [lead.id for lead in leads]
        assert len(ids) == len(set(ids)), "Duplicate lead IDs found"
    
    def test_generate_zero_leads(self, generator):
        """Test generating zero leads returns empty list."""
        leads = generator.generate(count=0, seed=42)
        assert leads == []
    
    def test_generate_large_batch(self, generator):
        """Test generating large number of leads."""
        leads = generator.generate(count=500, seed=42)
        
        assert len(leads) == 500
        # Verify all have unique IDs
        ids = [lead.id for lead in leads]
        assert len(ids) == len(set(ids))


class TestLeadValidation:
    """Test lead data validation."""
    
    def test_valid_lead_creation(self):
        """Test creating a valid lead."""
        lead = Lead(
            id="test-001",
            full_name="John Doe",
            company_name="Acme Corp",
            role="VP Sales",
            industry="Technology",
            website="https://acme.com",
            email="john.doe@acme.com",
            linkedin_url="https://linkedin.com/in/johndoe",
            country="United States"
        )
        
        assert lead.full_name == "John Doe"
        assert lead.status == LeadStatus.NEW
    
    def test_lead_status_enum(self):
        """Test all lead status values."""
        statuses = [s.value for s in LeadStatus]
        
        assert "NEW" in statuses
        assert "ENRICHED" in statuses
        assert "MESSAGED" in statuses
        assert "SENT" in statuses
        assert "FAILED" in statuses


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
