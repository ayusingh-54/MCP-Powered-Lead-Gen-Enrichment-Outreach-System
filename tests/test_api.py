"""
Test Suite - MCP Server API
===========================
Integration tests for the FastAPI MCP server endpoints.
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.mcp_server.server import app


class TestHealthEndpoints:
    """Test health and status endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test /health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert "name" in data or "message" in data


class TestMCPToolDiscovery:
    """Test MCP tool discovery endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_list_tools(self, client):
        """Test listing available MCP tools."""
        response = client.get("/mcp/tools")
        
        assert response.status_code == 200
        data = response.json()
        assert "tools" in data
        
        tool_names = [t["name"] for t in data["tools"]]
        assert "generate_leads" in tool_names
        assert "enrich_leads" in tool_names
        assert "generate_messages" in tool_names
        assert "send_outreach" in tool_names
        assert "get_status" in tool_names
    
    def test_tool_has_description(self, client):
        """Test that tools have descriptions."""
        response = client.get("/mcp/tools")
        
        data = response.json()
        for tool in data["tools"]:
            assert "description" in tool
            assert len(tool["description"]) > 0


class TestGenerateLeadsTool:
    """Test generate_leads MCP tool."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_generate_leads_basic(self, client):
        """Test basic lead generation."""
        response = client.post(
            "/mcp/invoke/generate_leads",
            json={"count": 10, "seed": 42}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["leads_generated"] == 10
    
    def test_generate_leads_default_count(self, client):
        """Test lead generation with default count."""
        response = client.post(
            "/mcp/invoke/generate_leads",
            json={}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_generate_leads_with_seed(self, client):
        """Test reproducible lead generation."""
        response1 = client.post(
            "/mcp/invoke/generate_leads",
            json={"count": 5, "seed": 42}
        )
        response2 = client.post(
            "/mcp/invoke/generate_leads",
            json={"count": 5, "seed": 42}
        )
        
        # Both should succeed
        assert response1.status_code == 200
        assert response2.status_code == 200


class TestEnrichLeadsTool:
    """Test enrich_leads MCP tool."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def with_leads(self, client):
        """Generate leads first."""
        client.post("/mcp/invoke/generate_leads", json={"count": 10, "seed": 42})
        return client
    
    def test_enrich_leads_offline(self, with_leads):
        """Test offline enrichment."""
        response = with_leads.post(
            "/mcp/invoke/enrich_leads",
            json={"mode": "offline", "batch_size": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_enrich_leads_ai_mode(self, with_leads):
        """Test AI mode enrichment."""
        response = with_leads.post(
            "/mcp/invoke/enrich_leads",
            json={"mode": "ai", "batch_size": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestGenerateMessagesTool:
    """Test generate_messages MCP tool."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def with_enriched_leads(self, client):
        """Generate and enrich leads first."""
        client.post("/mcp/invoke/generate_leads", json={"count": 10, "seed": 42})
        client.post("/mcp/invoke/enrich_leads", json={"mode": "offline"})
        return client
    
    def test_generate_email_messages(self, with_enriched_leads):
        """Test email message generation."""
        response = with_enriched_leads.post(
            "/mcp/invoke/generate_messages",
            json={"channels": ["email"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_generate_linkedin_messages(self, with_enriched_leads):
        """Test LinkedIn message generation."""
        response = with_enriched_leads.post(
            "/mcp/invoke/generate_messages",
            json={"channels": ["linkedin"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
    
    def test_generate_with_variants(self, with_enriched_leads):
        """Test A/B variant generation."""
        response = with_enriched_leads.post(
            "/mcp/invoke/generate_messages",
            json={"channels": ["email"], "generate_ab_variants": True}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestSendOutreachTool:
    """Test send_outreach MCP tool."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    @pytest.fixture
    def with_messages(self, client):
        """Generate leads, enrich, and create messages."""
        client.post("/mcp/invoke/generate_leads", json={"count": 10, "seed": 42})
        client.post("/mcp/invoke/enrich_leads", json={"mode": "offline"})
        client.post("/mcp/invoke/generate_messages", json={"channels": ["email"]})
        return client
    
    def test_send_dry_run(self, with_messages):
        """Test dry-run sending."""
        response = with_messages.post(
            "/mcp/invoke/send_outreach",
            json={"mode": "dry_run", "rate_limit": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert data["mode"] == "dry_run"
    
    def test_send_with_rate_limit(self, with_messages):
        """Test sending with rate limit."""
        response = with_messages.post(
            "/mcp/invoke/send_outreach",
            json={"mode": "dry_run", "rate_limit": 5, "batch_size": 10}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True


class TestGetStatusTool:
    """Test get_status MCP tool."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_status(self, client):
        """Test getting pipeline status."""
        response = client.get("/mcp/invoke/get_status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "metrics" in data


class TestAPIEndpoints:
    """Test additional API endpoints."""
    
    @pytest.fixture
    def client(self):
        return TestClient(app)
    
    def test_get_metrics(self, client):
        """Test /api/metrics endpoint."""
        response = client.get("/api/metrics")
        
        assert response.status_code == 200
    
    def test_get_leads(self, client):
        """Test /api/leads endpoint."""
        # Generate some leads first
        client.post("/mcp/invoke/generate_leads", json={"count": 5, "seed": 42})
        
        response = client.get("/api/leads")
        
        assert response.status_code == 200
    
    def test_get_leads_with_status_filter(self, client):
        """Test filtering leads by status."""
        client.post("/mcp/invoke/generate_leads", json={"count": 5, "seed": 42})
        
        response = client.get("/api/leads", params={"status": "NEW"})
        
        assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
