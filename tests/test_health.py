"""
Health check tests.
"""

import pytest
from httpx import AsyncClient


class TestHealth:
    """Test health check endpoints."""
    
    async def test_health_check_success(self, client: AsyncClient):
        """Test successful health check."""
        response = await client.get("/api/v1/health/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "database" in data
        assert "timestamp" in data
        assert data["database"] == "healthy"
