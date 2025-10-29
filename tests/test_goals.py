"""
Goals tests.
"""

import pytest
from datetime import datetime, timedelta
from httpx import AsyncClient

from app.repositories import GoalRepository


class TestGoals:
    """Test goals endpoints."""
    
    async def test_create_goal_success(self, client: AsyncClient, auth_headers):
        """Test successful goal creation."""
        goal_data = {
            "name": "Test Goal",
            "description": "A test goal",
            "emoji": "🎯",
            "goal_type": "count",
            "unit": "items",
            "target": 100,
            "timeframe_type": "fixed",
            "start_at": "2025-01-01T00:00:00Z",
            "end_at": "2025-12-31T23:59:59Z",
            "privacy": "private",
        }
        
        response = await client.post(
            "/api/v1/goals/",
            json=goal_data,
            headers=auth_headers
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Goal"
        assert data["goal_type"] == "count"
        assert data["status"] == "active"
        assert "id" in data
        assert "owner_id" in data
    
    async def test_create_goal_unauthorized(self, client: AsyncClient):
        """Test goal creation without authentication."""
        goal_data = {
            "name": "Test Goal",
            "description": "A test goal",
            "emoji": "🎯",
            "goal_type": "count",
            "unit": "items",
            "target": 100,
            "timeframe_type": "fixed",
            "start_at": "2025-01-01T00:00:00Z",
            "end_at": "2025-12-31T23:59:59Z",
            "privacy": "private",
        }
        
        response = await client.post(
            "/api/v1/goals/",
            json=goal_data
        )
        
        assert response.status_code == 401
    
    async def test_list_goals(self, client: AsyncClient, auth_headers, test_user, db_session):
        """Test listing user's goals."""
        # Create a test goal
        goal_repo = GoalRepository(db_session)
        goal_data = {
            "owner_id": test_user.id,
            "name": "Test Goal",
            "description": "A test goal",
            "emoji": "🎯",
            "goal_type": "count",
            "unit": "items",
            "target": 100,
            "timeframe_type": "fixed",
            "start_at": datetime.utcnow(),
            "end_at": datetime.utcnow() + timedelta(days=30),
            "privacy": "private",
            "status": "active",
        }
        await goal_repo.create(goal_data)
        
        response = await client.get(
            "/api/v1/goals/",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "page" in data
        assert "page_size" in data
        assert "total" in data
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Test Goal"
    
    async def test_get_goal_success(self, client: AsyncClient, auth_headers, test_user, db_session):
        """Test getting a specific goal."""
        # Create a test goal
        goal_repo = GoalRepository(db_session)
        goal_data = {
            "owner_id": test_user.id,
            "name": "Test Goal",
            "description": "A test goal",
            "emoji": "🎯",
            "goal_type": "count",
            "unit": "items",
            "target": 100,
            "timeframe_type": "fixed",
            "start_at": datetime.utcnow(),
            "end_at": datetime.utcnow() + timedelta(days=30),
            "privacy": "private",
            "status": "active",
        }
        goal = await goal_repo.create(goal_data)
        
        response = await client.get(
            f"/api/v1/goals/{goal.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Goal"
        assert data["id"] == goal.id
    
    async def test_get_goal_not_found(self, client: AsyncClient, auth_headers):
        """Test getting a non-existent goal."""
        response = await client.get(
            "/api/v1/goals/99999",
            headers=auth_headers
        )
        
        assert response.status_code == 404
        assert "Goal not found" in response.json()["detail"]
    
    async def test_update_goal_success(self, client: AsyncClient, auth_headers, test_user, db_session):
        """Test successful goal update."""
        # Create a test goal
        goal_repo = GoalRepository(db_session)
        goal_data = {
            "owner_id": test_user.id,
            "name": "Test Goal",
            "description": "A test goal",
            "emoji": "🎯",
            "goal_type": "count",
            "unit": "items",
            "target": 100,
            "timeframe_type": "fixed",
            "start_at": datetime.utcnow(),
            "end_at": datetime.utcnow() + timedelta(days=30),
            "privacy": "private",
            "status": "active",
        }
        goal = await goal_repo.create(goal_data)
        
        update_data = {
            "name": "Updated Goal",
            "description": "An updated test goal",
        }
        
        response = await client.patch(
            f"/api/v1/goals/{goal.id}",
            json=update_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Updated Goal"
        assert data["description"] == "An updated test goal"
    
    async def test_delete_goal_success(self, client: AsyncClient, auth_headers, test_user, db_session):
        """Test successful goal deletion."""
        # Create a test goal
        goal_repo = GoalRepository(db_session)
        goal_data = {
            "owner_id": test_user.id,
            "name": "Test Goal",
            "description": "A test goal",
            "emoji": "🎯",
            "goal_type": "count",
            "unit": "items",
            "target": 100,
            "timeframe_type": "fixed",
            "start_at": datetime.utcnow(),
            "end_at": datetime.utcnow() + timedelta(days=30),
            "privacy": "private",
            "status": "active",
        }
        goal = await goal_repo.create(goal_data)
        
        response = await client.delete(
            f"/api/v1/goals/{goal.id}",
            headers=auth_headers
        )
        
        assert response.status_code == 204
        
        # Verify goal is soft deleted
        updated_goal = await goal_repo.get_by_id(goal.id)
        assert updated_goal.status == "ended"
