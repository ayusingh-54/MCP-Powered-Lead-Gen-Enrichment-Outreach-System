"""
Test Suite Configuration
========================
Pytest configuration and fixtures for all tests.
"""

import pytest
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set test environment variables
os.environ["DATABASE_PATH"] = ":memory:"  # Use in-memory database for tests
os.environ["LOG_LEVEL"] = "WARNING"  # Reduce log noise during tests


@pytest.fixture(scope="session")
def test_database():
    """Create a test database for the session."""
    from backend.storage.database import DatabaseManager
    
    db = DatabaseManager(":memory:")
    yield db


@pytest.fixture(autouse=True)
def reset_database(test_database):
    """Reset database before each test."""
    # Clear all tables
    with test_database.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM leads")
        cursor.execute("DELETE FROM enrichments")
        cursor.execute("DELETE FROM messages")
        cursor.execute("DELETE FROM outreach_results")
        conn.commit()
    
    yield


@pytest.fixture
def sample_lead():
    """Create a sample lead for testing."""
    from backend.mcp_server.models import Lead
    
    return Lead(
        id="test-lead-001",
        full_name="John Doe",
        company_name="Acme Corporation",
        role="VP of Sales",
        industry="Technology",
        website="https://acme.com",
        email="john.doe@acme.com",
        linkedin_url="https://linkedin.com/in/johndoe",
        country="United States"
    )


@pytest.fixture
def sample_enrichment(sample_lead):
    """Create a sample enrichment for testing."""
    from backend.mcp_server.models import LeadEnrichment
    
    return LeadEnrichment(
        lead_id=sample_lead.id,
        company_size="medium",
        persona="Sales Leader",
        pain_points=["Pipeline visibility", "Sales forecasting accuracy"],
        buying_triggers=["New sales leadership", "Revenue targets"],
        confidence_score=85,
        enrichment_mode="offline"
    )


# Markers for test categories
def pytest_configure(config):
    """Configure custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )
