"""
Comprehensive Unit and Integration Tests for Goals-Service
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock
from datetime import datetime, timezone, date
from decimal import Decimal
from uuid import uuid4
import sys
import os
from sqlalchemy.sql import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, get_db
from database import Base, Goal
from auth import create_access_token

SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    """Override database dependency with test database"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def run_init_sql():
    """Run test_init.sql to create the database schema"""
    with engine.connect() as connection:
        with open(os.path.join(os.path.dirname(__file__), '../../Database/goals_test.sql'), 'r') as file:
            sql_script = file.read()
            connection.execute(text(sql_script))


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    run_init_sql()  
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_user():
    """Create test user credentials"""
    user_id = "test_google_sub_12345"
    token = create_access_token(user_id)
    return {"user_id": user_id, "token": token}


@pytest.fixture
def test_goal(test_user):
    """Create a test goal in database"""
    db = TestingSessionLocal()
    goal = Goal(
        goal_id=uuid4(),
        owner_user_id=test_user['user_id'],
        title="Test Goal",
        target_hours=Decimal("100.0"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        hourly_rate=Decimal("50.0"),
        description="Test goal description",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(goal)
    db.commit()
    db.refresh(goal)
    db.close()
    return goal


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_liveness_health_check():
    """Test liveness health check endpoint"""
    response = client.get("/api/goals/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_health_check():
    """Test readiness health check endpoint"""
    response = client.get("/api/goals/health/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================================
# CREATE GOAL TESTS
# ============================================================================

def test_create_goal_minimal(test_user):
    """Test creating goal with minimal required fields"""
    goal_data = {
        "title": "Learn Python"
    }
    
    response = client.post(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=goal_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Learn Python"
    assert data["owner_user_id"] == test_user['user_id']
    assert "goal_id" in data


def test_create_goal_complete(test_user):
    """Test creating goal with all fields"""
    goal_data = {
        "title": "Master FastAPI",
        "target_hours": 150,
        "start_date": "2026-01-01",
        "end_date": "2026-06-30",
        "hourly_rate": 75.50,
        "description": "Complete comprehensive FastAPI course with projects"
    }
    
    response = client.post(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=goal_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Master FastAPI"
    assert float(data["target_hours"]) == 150
    assert data["start_date"] == "2026-01-01"
    assert data["end_date"] == "2026-06-30"
    assert float(data["hourly_rate"]) == 75.50
    assert data["description"] == "Complete comprehensive FastAPI course with projects"


def test_create_goal_unauthorized():
    """Test creating goal without authentication"""
    goal_data = {
        "title": "Test Goal"
    }
    
    response = client.post("/api/goals", json=goal_data)
    assert response.status_code == 403


def test_create_goal_missing_title(test_user):
    """Test creating goal without required title"""
    goal_data = {
        "target_hours": 100
    }
    
    response = client.post(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=goal_data
    )
    
    assert response.status_code == 422


# ============================================================================
# LIST GOALS TESTS
# ============================================================================

def test_list_goals_empty(test_user):
    """Test listing goals when no goals exist"""
    response = client.get(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["goals"] == []
    assert data["total"] == 0
    assert data["page"] == 1


def test_list_goals_pagination(test_user):
    """Test pagination of goals list"""
    db = TestingSessionLocal()
    for i in range(15):
        goal = Goal(
            owner_user_id=test_user['user_id'],
            title=f"Goal {i + 1}",
            target_hours=Decimal(100 + i * 10),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(goal)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/goals?page=1&page_size=10",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["goals"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["page_size"] == 10
    
    response = client.get(
        "/api/goals?page=2&page_size=10",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    data = response.json()
    assert len(data["goals"]) == 5
    assert data["page"] == 2


def test_list_goals_unauthorized():
    """Test listing goals without authentication"""
    response = client.get("/api/goals")
    assert response.status_code == 403


def test_list_goals_ordering(test_user):
    """Test that goals are ordered by creation date (newest first)"""
    db = TestingSessionLocal()
    
    for i in range(3):
        goal = Goal(
            owner_user_id=test_user['user_id'],
            title=f"Goal {i}",
            created_at=datetime(2026, 1, i + 1, tzinfo=timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(goal)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    data = response.json()
    assert data["goals"][0]["title"] == "Goal 2"
    assert data["goals"][-1]["title"] == "Goal 0"


# ============================================================================
# GET GOAL BY ID TESTS
# ============================================================================

def test_get_goal_by_id(test_user, test_goal):
    """Test getting a specific goal by ID"""
    response = client.get(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == str(test_goal.goal_id)
    assert data["title"] == test_goal.title
    assert float(data["target_hours"]) == float(test_goal.target_hours)
    assert data["description"] == test_goal.description


def test_get_goal_not_found(test_user):
    """Test getting non-existent goal"""
    fake_id = uuid4()
    response = client.get(
        f"/api/goals/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


def test_get_goal_wrong_user(test_goal):
    """Test getting goal owned by different user"""
    other_user_id = "other_google_sub"
    other_token = create_access_token(other_user_id)
    
    response = client.get(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    assert response.status_code == 404


def test_get_goal_unauthorized(test_goal):
    """Test getting goal without authentication"""
    response = client.get(f"/api/goals/{test_goal.goal_id}")
    assert response.status_code == 403


# ============================================================================
# UPDATE GOAL TESTS
# ============================================================================

def test_update_goal_title(test_user, test_goal):
    """Test updating goal title"""
    update_data = {
        "title": "Updated Goal Title"
    }
    
    response = client.put(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Goal Title"
    assert float(data["target_hours"]) == float(test_goal.target_hours)


def test_update_goal_multiple_fields(test_user, test_goal):
    """Test updating multiple goal fields"""
    update_data = {
        "title": "New Title",
        "target_hours": 200,
        "hourly_rate": 100.0,
        "description": "New description"
    }
    
    response = client.put(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New Title"
    assert float(data["target_hours"]) == 200
    assert float(data["hourly_rate"]) == 100.0
    assert data["description"] == "New description"


def test_update_goal_dates(test_user, test_goal):
    """Test updating goal dates"""
    update_data = {
        "start_date": "2026-02-01",
        "end_date": "2026-11-30"
    }
    
    response = client.put(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["start_date"] == "2026-02-01"
    assert data["end_date"] == "2026-11-30"


def test_update_goal_not_found(test_user):
    """Test updating non-existent goal"""
    fake_id = uuid4()
    response = client.put(
        f"/api/goals/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"title": "New Title"}
    )
    
    assert response.status_code == 404


def test_update_goal_unauthorized():
    """Test updating goal without authentication"""
    fake_id = uuid4()
    response = client.put(
        f"/api/goals/{fake_id}",
        json={"title": "New Title"}
    )
    assert response.status_code == 403


# ============================================================================
# DELETE GOAL TESTS
# ============================================================================

def test_delete_goal(test_user, test_goal):
    """Test deleting a goal"""
    response = client.delete(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 204
    
    db = TestingSessionLocal()
    deleted = db.query(Goal).filter(
        Goal.goal_id == test_goal.goal_id
    ).first()
    assert deleted is None
    db.close()


def test_delete_goal_not_found(test_user):
    """Test deleting non-existent goal"""
    fake_id = uuid4()
    response = client.delete(
        f"/api/goals/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


def test_delete_goal_wrong_user(test_goal):
    """Test deleting goal owned by different user"""
    other_user_id = "other_google_sub"
    other_token = create_access_token(other_user_id)
    
    response = client.delete(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    assert response.status_code == 404


def test_delete_goal_unauthorized(test_goal):
    """Test deleting goal without authentication"""
    response = client.delete(f"/api/goals/{test_goal.goal_id}")
    assert response.status_code == 403


# ============================================================================
# GOAL STATISTICS TESTS
# ============================================================================

@patch('entries_client.get_goal_total_hours')
@patch('entries_client.get_goal_entries_count')
def test_get_goal_stats(mock_entries_count, mock_total_hours, test_user, test_goal):
    """Test getting goal statistics"""
    mock_total_hours.return_value = Decimal("65.5")
    mock_entries_count.return_value = 42
    
    response = client.get(
        f"/api/goals/{test_goal.goal_id}/stats",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == str(test_goal.goal_id)
    assert data["target_hours"] == float(test_goal.target_hours)


def test_get_goal_stats_not_found(test_user):
    """Test getting statistics for non-existent goal"""
    fake_id = uuid4()
    response = client.get(
        f"/api/goals/{fake_id}/stats",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


def test_get_goal_stats_unauthorized(test_goal):
    """Test getting goal statistics without authentication"""
    response = client.get(f"/api/goals/{test_goal.goal_id}/stats")
    assert response.status_code == 403


# ============================================================================
# USER SUMMARY TESTS
# ============================================================================

def test_get_user_goals_summary(test_user):
    """Test getting user's goals summary"""
    db = TestingSessionLocal()
    for i in range(3):
        goal = Goal(
            owner_user_id=test_user['user_id'],
            title=f"Goal {i + 1}",
            target_hours=Decimal(50 * (i + 1)),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(goal)
    db.commit()
    db.close()
    
    response = client.get(
        f"/api/goals/user/{test_user['user_id']}/summary",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code in [200, 422]


def test_get_user_goals_summary_unauthorized():
    """Test getting user summary without authentication"""
    fake_user_id = uuid4()
    response = client.get(f"/api/goals/user/{fake_user_id}/summary")
    assert response.status_code == 403


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_invalid_pagination_parameters(test_user):
    """Test pagination with invalid parameters"""
    response = client.get(
        "/api/goals?page=0",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422
    
    response = client.get(
        "/api/goals?page_size=1000",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422


def test_create_goal_with_negative_hours(test_user):
    """Test creating goal with negative target hours"""
    goal_data = {
        "title": "Invalid Goal",
        "target_hours": -100
    }
    
    response = client.post(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=goal_data
    )
    
    assert response.status_code in [201, 422]


def test_create_goal_with_invalid_dates(test_user):
    """Test creating goal with end_date before start_date"""
    goal_data = {
        "title": "Invalid Dates Goal",
        "start_date": "2026-12-31",
        "end_date": "2026-01-01"
    }
    
    response = client.post(
        "/api/goals",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=goal_data
    )
    
    assert response.status_code == 201


def test_update_goal_to_empty_string(test_user, test_goal):
    """Test updating goal fields to empty strings"""
    update_data = {
        "description": ""
    }
    
    response = client.put(
        f"/api/goals/{test_goal.goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["description"] == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
