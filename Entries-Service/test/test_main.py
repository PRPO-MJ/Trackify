"""
Comprehensive Unit and Integration Tests for Entries-Service
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone, time, date
from decimal import Decimal
from uuid import uuid4
import sys
import os
from sqlalchemy.sql import text

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, get_db
from database import Base, TimeEntry
from auth import create_access_token

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
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
        with open(os.path.join(os.path.dirname(__file__), '../../Database/entries_test.sql'), 'r') as file:
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
def test_goal_id():
    """Create test goal ID"""
    return uuid4()


@pytest.fixture
def test_entry(test_user, test_goal_id):
    """Create a test time entry in database"""
    db = TestingSessionLocal()
    entry = TimeEntry(
        entry_id=uuid4(),
        owner_user_id=test_user['user_id'],
        related_goal_id=test_goal_id,
        work_date=date(2026, 1, 12),
        start_time=time(9, 0, 0),
        end_time=time(12, 0, 0),
        minutes=Decimal("180"),
        description="Test entry",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    db.close()
    return entry


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_liveness_health_check():
    """Test liveness health check endpoint"""
    response = client.get("/api/entries/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_health_check():
    """Test readiness health check endpoint"""
    response = client.get("/api/entries/health/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================================
# CREATE ENTRY TESTS
# ============================================================================

@patch('goals_client.validate_goal_ownership')
@pytest.mark.asyncio
async def test_create_entry_with_times(mock_validate, test_user, test_goal_id):
    """Test creating entry with start and end times (auto-calculate minutes)"""
    mock_validate.return_value = True
    
    entry_data = {
        "related_goal_id": str(test_goal_id),
        "work_date": "2026-01-12",
        "start_time": "09:00:00",
        "end_time": "12:00:00",
        "description": "Morning work session"
    }
    
    response = client.post(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=entry_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["owner_user_id"] == test_user['user_id']
    assert data["related_goal_id"] == str(test_goal_id)
    assert data["work_date"] == "2026-01-12"
    assert data["start_time"] == "09:00:00"
    assert data["end_time"] == "12:00:00"
    assert float(data["minutes"]) == 180  # 3 hours


@patch('goals_client.validate_goal_ownership')
def test_create_entry_with_manual_minutes(mock_validate, test_user, test_goal_id):
    """Test creating entry with manual minutes (no time calculation)"""
    mock_validate.return_value = True
    
    entry_data = {
        "related_goal_id": str(test_goal_id),
        "work_date": "2026-01-12",
        "minutes": 120,
        "description": "Manual 2-hour entry"
    }
    
    response = client.post(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=entry_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert float(data["minutes"]) == 120


def test_create_entry_without_goal(test_user):
    """Test creating entry without associating it to a goal"""
    entry_data = {
        "work_date": "2026-01-12",
        "minutes": 60,
        "description": "Independent work"
    }
    
    response = client.post(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=entry_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["related_goal_id"] is None
    assert float(data["minutes"]) == 60


@patch('goals_client.validate_goal_ownership')
def test_create_entry_invalid_goal(mock_validate, test_user):
    """Test creating entry with invalid/non-owned goal"""
    mock_validate.return_value = False
    
    fake_goal_id = uuid4()
    entry_data = {
        "related_goal_id": str(fake_goal_id),
        "minutes": 60
    }
    
    response = client.post(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=entry_data
    )
    
    assert response.status_code == 400
    assert "not found" in response.json()["detail"].lower()


def test_create_entry_unauthorized():
    """Test creating entry without authentication"""
    entry_data = {
        "minutes": 60,
        "description": "Test"
    }
    
    response = client.post("/api/entries", json=entry_data)
    assert response.status_code == 403


def test_create_entry_overnight(test_user):
    """Test creating entry with end_time before start_time (overnight work)"""
    entry_data = {
        "work_date": "2026-01-12",
        "start_time": "23:00:00",
        "end_time": "02:00:00",  
        "description": "Night shift"
    }
    
    response = client.post(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=entry_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert float(data["minutes"]) == 180


# ============================================================================
# LIST ENTRIES TESTS
# ============================================================================

def test_list_entries_empty(test_user):
    """Test listing entries when no entries exist"""
    response = client.get(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["entries"] == []
    assert data["total"] == 0
    assert data["page"] == 1


def test_list_entries_pagination(test_user):
    """Test pagination of entry list"""
    db = TestingSessionLocal()
    for i in range(15):
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            work_date=date(2026, 1, i + 1),
            minutes=Decimal(60 * (i + 1)),
            description=f"Entry {i + 1}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/entries?page=1&page_size=10",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["entries"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1
    assert data["page_size"] == 10
    
    response = client.get(
        "/api/entries?page=2&page_size=10",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    data = response.json()
    assert len(data["entries"]) == 5
    assert data["page"] == 2


def test_list_entries_filter_by_goal(test_user, test_goal_id):
    """Test filtering entries by goal ID"""
    other_goal_id = uuid4()
    
    db = TestingSessionLocal()
    for i in range(3):
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            related_goal_id=test_goal_id,
            work_date=date(2026, 1, i + 1),
            minutes=Decimal(60),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    
    for i in range(2):
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            related_goal_id=other_goal_id,
            work_date=date(2026, 1, i + 10),
            minutes=Decimal(90),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    db.commit()
    db.close()
    
    response = client.get(
        f"/api/entries?goal_id={str(test_goal_id)}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert all(e["related_goal_id"] == str(test_goal_id) for e in data["entries"])


def test_list_entries_sorting(test_user):
    """Test sorting entries by different fields"""
    db = TestingSessionLocal()
    
    entries_data = [
        {"work_date": date(2026, 1, 1), "minutes": Decimal(120)},
        {"work_date": date(2026, 1, 5), "minutes": Decimal(60)},
        {"work_date": date(2026, 1, 3), "minutes": Decimal(180)},
    ]
    
    for entry_data in entries_data:
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            **entry_data,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/entries?sort_by=work_date&sort_order=asc",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    data = response.json()
    dates = [e["work_date"] for e in data["entries"]]
    assert dates == sorted(dates)
    
    response = client.get(
        "/api/entries?sort_by=minutes&sort_order=desc",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    data = response.json()
    minutes = [float(e["minutes"]) for e in data["entries"]]
    assert minutes == sorted(minutes, reverse=True)


def test_list_entries_invalid_goal_id(test_user):
    """Test filtering with invalid goal ID format"""
    response = client.get(
        "/api/entries?goal_id=invalid-uuid",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 400


def test_list_entries_unauthorized():
    """Test listing entries without authentication"""
    response = client.get("/api/entries")
    assert response.status_code == 403


# ============================================================================
# GET ENTRY BY ID TESTS
# ============================================================================

def test_get_entry_by_id(test_user, test_entry):
    """Test getting a specific entry by ID"""
    response = client.get(
        f"/api/entries/{test_entry.entry_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["entry_id"] == str(test_entry.entry_id)
    assert data["owner_user_id"] == test_entry.owner_user_id
    assert float(data["minutes"]) == float(test_entry.minutes)


def test_get_entry_not_found(test_user):
    """Test getting non-existent entry"""
    fake_id = uuid4()
    response = client.get(
        f"/api/entries/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


def test_get_entry_wrong_user(test_entry):
    """Test getting entry owned by different user"""
    other_user_id = "other_google_sub"
    other_token = create_access_token(other_user_id)
    
    response = client.get(
        f"/api/entries/{test_entry.entry_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    assert response.status_code == 404


# ============================================================================
# UPDATE ENTRY TESTS
# ============================================================================

@patch('goals_client.validate_goal_ownership')
def test_update_entry(mock_validate, test_user, test_entry):
    """Test updating an entry"""
    mock_validate.return_value = True
    
    update_data = {
        "minutes": 240,
        "description": "Updated description"
    }
    
    response = client.put(
        f"/api/entries/{test_entry.entry_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert float(data["minutes"]) == 240
    assert data["description"] == "Updated description"


def test_update_entry_not_found(test_user):
    """Test updating non-existent entry"""
    fake_id = uuid4()
    response = client.put(
        f"/api/entries/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"minutes": 120}
    )
    
    assert response.status_code == 404


def test_update_entry_unauthorized():
    """Test updating entry without authentication"""
    fake_id = uuid4()
    response = client.put(
        f"/api/entries/{fake_id}",
        json={"minutes": 120}
    )
    assert response.status_code == 403


# ============================================================================
# DELETE ENTRY TESTS
# ============================================================================

def test_delete_entry(test_user, test_entry):
    """Test deleting an entry"""
    response = client.delete(
        f"/api/entries/{test_entry.entry_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()
    
    db = TestingSessionLocal()
    deleted = db.query(TimeEntry).filter(
        TimeEntry.entry_id == test_entry.entry_id
    ).first()
    assert deleted is None
    db.close()


def test_delete_entry_not_found(test_user):
    """Test deleting non-existent entry"""
    fake_id = uuid4()
    response = client.delete(
        f"/api/entries/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


# ============================================================================
# STATISTICS TESTS
# ============================================================================

def test_get_goal_total_hours(test_user, test_goal_id):
    """Test getting total hours for a specific goal"""
    db = TestingSessionLocal()
    for minutes in [60, 120, 90]:
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            related_goal_id=test_goal_id,
            minutes=Decimal(minutes),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    db.commit()
    db.close()
    
    response = client.get(
        f"/api/entries/goal/{test_goal_id}/stats",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["goal_id"] == str(test_goal_id)
    assert float(data["total_minutes"]) == 270
    assert float(data["total_hours"]) == 4.5
    assert data["entry_count"] == 3


def test_get_user_statistics(test_user, test_goal_id):
    """Test getting user's time statistics across all goals"""
    other_goal_id = uuid4()
    
    db = TestingSessionLocal()
    
    for minutes in [60, 120]:
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            related_goal_id=test_goal_id,
            minutes=Decimal(minutes),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    
    for minutes in [90, 150]:
        entry = TimeEntry(
            owner_user_id=test_user['user_id'],
            related_goal_id=other_goal_id,
            minutes=Decimal(minutes),
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(entry)
    
    db.commit()
    db.close()
    
    response = client.get(
        "/api/entries/stats",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert float(data["total_minutes"]) == 420  # 60+120+90+150
    assert float(data["total_hours"]) == 7.0
    assert data["total_entries"] == 4


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_invalid_pagination_parameters(test_user):
    """Test pagination with invalid parameters"""
    response = client.get(
        "/api/entries?page=0",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422
    
    response = client.get(
        "/api/entries?page_size=1000",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422


def test_invalid_sort_parameters(test_user):
    """Test sorting with invalid parameters"""
    response = client.get(
        "/api/entries?sort_by=invalid_field",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422
    
    response = client.get(
        "/api/entries?sort_order=invalid",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422


def test_create_entry_negative_minutes(test_user):
    """Test creating entry with negative minutes (should fail)"""
    entry_data = {
        "minutes": -60,
        "description": "Negative time"
    }
    
    response = client.post(
        "/api/entries",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=entry_data
    )
    
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
