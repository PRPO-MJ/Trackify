"""
Comprehensive Unit and Integration Tests for User-Service
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
import sys
import os
from sqlalchemy.sql import text

os.environ["TEST_ENV"] = "true"

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, get_db
from database import Base, User
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


@pytest.fixture(autouse=True)
def reset_db():
    """Reset database before each test"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    run_init_sql()  # Run the init.sql script
    yield
    Base.metadata.drop_all(bind=engine)


def run_init_sql():
    """Run init.sql to create the database schema"""
    with engine.connect() as connection:
        with open(os.path.join(os.path.dirname(__file__), '../../Database/user_test.sql'), 'r') as file:
            sql_script = file.read()
            connection.execute(text(sql_script))


@pytest.fixture
def test_user():
    """Create a test user in database"""
    db = TestingSessionLocal()
    user = User(
        google_sub="test_google_sub_12345",
        google_email="test@example.com",
        full_name="Test User",
        address="123 Test St",
        country="TestLand",
        phone="+1234567890",
        currency="USD",
        timezone="UTC",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    token = create_access_token(user.google_sub)
    db.close()
    return {"user": user, "token": token}


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_liveness_health_check():
    """Test liveness health check endpoint"""
    response = client.get("/api/users/health/liveness")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_readiness_health_check():
    """Test readiness health check endpoint"""
    response = client.get("/api/users/health/readiness")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


# ============================================================================
# AUTHENTICATION TESTS
# ============================================================================

@patch('auth.verify_google_token')
def test_google_auth_new_user(mock_verify):
    """Test Google authentication with new user registration"""
    mock_verify.return_value = {
        'sub': 'google_new_user_123',
        'email': 'newuser@gmail.com',
        'given_name': 'New',
        'family_name': 'User',
        'name': 'New User'
    }
    
    response = client.post(
        "/api/auth/google",
        json={"token": "mock_google_token"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["google_email"] == "newuser@gmail.com"
    assert data["user"]["full_name"] == "New User"


@patch('auth.verify_google_token')
def test_google_auth_existing_user(mock_verify, test_user):
    """Test Google authentication with existing user"""
    mock_verify.return_value = {
        'sub': test_user['user'].google_sub,
        'email': test_user['user'].google_email,
        'given_name': 'Test',
        'family_name': 'User',
        'name': 'Test User'
    }
    
    response = client.post(
        "/api/auth/google",
        json={"token": "mock_google_token"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["google_email"] == test_user['user'].google_email


@patch('auth.verify_google_token')
def test_google_auth_missing_email(mock_verify):
    """Test Google authentication fails when email is missing"""
    mock_verify.return_value = {
        'sub': 'google_123',
    }
    
    response = client.post(
        "/api/auth/google",
        json={"token": "mock_google_token"}
    )
    
    assert response.status_code == 400
    assert "Email not found" in response.json()["detail"]


@patch('auth.verify_google_token')
def test_google_auth_invalid_token(mock_verify):
    """Test Google authentication with invalid token"""
    mock_verify.side_effect = Exception("Invalid token")
    
    response = client.post(
        "/api/auth/google",
        json={"token": "invalid_token"}
    )
    
    assert response.status_code == 401


def test_google_auth_missing_token():
    """Test Google authentication without token"""
    response = client.post("/api/auth/google", json={})
    assert response.status_code == 422  


@patch('auth.exchange_code_for_token')
def test_google_callback_new_user(mock_exchange):
    """Test Google OAuth callback with new user"""
    mock_exchange.return_value = {
        'sub': 'google_callback_123',
        'email': 'callback@gmail.com',
        'given_name': 'Callback',
        'family_name': 'User'
    }
    
    response = client.post(
        "/auth/google/callback",
        json={
            "code": "mock_auth_code",
            "redirect_uri": "http://localhost:8080/callback"
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["user"]["google_email"] == "callback@gmail.com"


def test_verify_token_valid(test_user):
    """Test JWT token verification with valid token"""
    response = client.get(
        "/api/auth/verify",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == test_user['user'].google_sub
    assert data["valid"] is True


def test_verify_token_missing():
    """Test token verification without token"""
    response = client.get("/api/auth/verify")
    assert response.status_code == 403


def test_verify_token_invalid():
    """Test token verification with invalid token"""
    response = client.get(
        "/api/auth/verify",
        headers={"Authorization": "Bearer invalid_token_12345"}
    )
    assert response.status_code == 401


# ============================================================================
# USER PROFILE TESTS
# ============================================================================

def test_get_current_user_profile(test_user):
    """Test getting current user's profile"""
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["google_sub"] == test_user['user'].google_sub
    assert data["google_email"] == test_user['user'].google_email
    assert data["full_name"] == test_user['user'].full_name
    assert data["address"] == test_user['user'].address
    assert data["country"] == test_user['user'].country
    assert data["phone"] == test_user['user'].phone
    assert data["currency"] == test_user['user'].currency
    assert data["timezone"] == test_user['user'].timezone


def test_get_current_user_without_token():
    """Test getting current user without authentication"""
    response = client.get("/api/users/me")
    assert response.status_code == 403


def test_get_user_by_id(test_user):
    """Test getting user profile by ID"""
    response = client.get(
        f"/api/users/{test_user['user'].google_sub}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["google_sub"] == test_user['user'].google_sub
    assert data["google_email"] == test_user['user'].google_email


def test_get_user_by_id_not_found(test_user):
    """Test getting non-existent user by ID"""
    response = client.get(
        "/api/users/nonexistent_user_id",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_get_all_users_pagination(test_user):
    """Test getting all users with pagination"""
    db = TestingSessionLocal()
    for i in range(5):
        user = User(
            google_sub=f"google_sub_{i}",
            google_email=f"user{i}@example.com",
            full_name=f"User {i}",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(user)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/users?skip=0&limit=3",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) <= 3


def test_get_all_users_without_auth():
    """Test getting all users without authentication"""
    response = client.get("/api/users")
    assert response.status_code == 403


# ============================================================================
# USER UPDATE TESTS
# ============================================================================

def test_update_user_profile_full_name(test_user):
    """Test updating user's full name"""
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"full_name": "Updated Name"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Name"
    assert data["google_email"] == test_user['user'].google_email


def test_update_user_profile_multiple_fields(test_user):
    """Test updating multiple user profile fields"""
    update_data = {
        "full_name": "New Name",
        "address": "456 New St",
        "country": "NewCountry",
        "phone": "+9876543210",
        "currency": "EUR",
        "timezone": "Europe/London"
    }
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == update_data["full_name"]
    assert data["address"] == update_data["address"]
    assert data["country"] == update_data["country"]
    assert data["phone"] == update_data["phone"]
    assert data["currency"] == update_data["currency"]
    assert data["timezone"] == update_data["timezone"]


def test_update_user_profile_partial(test_user):
    """Test partial update of user profile"""
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"currency": "GBP"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["currency"] == "GBP"
    assert data["full_name"] == test_user['user'].full_name


def test_update_user_profile_without_auth():
    """Test updating user profile without authentication"""
    response = client.put(
        "/api/users/me",
        json={"full_name": "New Name"}
    )
    assert response.status_code == 403


def test_update_user_profile_invalid_field():
    """Test updating user profile with extra fields (should be rejected)"""
    db = TestingSessionLocal()
    user = User(
        google_sub="test_extra_field",
        google_email="extra@example.com",
        full_name="Extra Test",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    token = create_access_token(user.google_sub)
    db.close()
    
    response = client.put(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
        json={"full_name": "Valid", "invalid_field": "Should be rejected"}
    )
    
    assert response.status_code == 422


# ============================================================================
# USER DELETE TESTS
# ============================================================================

def test_delete_current_user(test_user):
    """Test deleting current user account"""
    response = client.delete(
        "/api/users/me",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert response.json() == {"message": "User deleted successfully"}
    
    db = TestingSessionLocal()
    deleted_user = db.query(User).filter(
        User.google_sub == test_user['user'].google_sub
    ).first()
    assert deleted_user is None
    db.close()


def test_delete_user_without_auth():
    """Test deleting user without authentication"""
    response = client.delete("/api/users/me")
    assert response.status_code == 403


def test_deleted_user_cannot_access_endpoints():
    """Test that deleted user cannot access protected endpoints"""
    db = TestingSessionLocal()
    user = User(
        google_sub="to_be_deleted",
        google_email="delete@example.com",
        full_name="Delete Me",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(user)
    db.commit()
    token = create_access_token(user.google_sub)
    db.close()
    
    response = client.delete(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    
    response = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 404  


# ============================================================================
# CORS AND OPTIONS TESTS
# ============================================================================

def test_options_google_auth():
    """Test CORS preflight for Google auth endpoint"""
    response = client.options("/api/auth/google")
    assert response.status_code == 200


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_create_user_with_minimal_google_info():
    """Test user creation when Google provides minimal information"""
    with patch('auth.verify_google_token') as mock_verify:
        mock_verify.return_value = {
            'sub': 'google_minimal_123',
            'email': 'minimal@gmail.com',
            'name': 'Minimal User'
        }
        
        response = client.post(
            "/api/auth/google",
            json={"token": "mock_token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["full_name"] == "Minimal User"


def test_create_user_with_no_name_info():
    """Test user creation when Google provides no name information"""
    with patch('auth.verify_google_token') as mock_verify:
        mock_verify.return_value = {
            'sub': 'google_no_name_123',
            'email': 'noname@gmail.com'
        }
        
        response = client.post(
            "/api/auth/google",
            json={"token": "mock_token"}
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["user"]["full_name"] == "noname"


def test_invalid_pagination_parameters(test_user):
    """Test pagination with invalid parameters"""
    response = client.get(
        "/api/users?skip=-1&limit=10",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422
    
    response = client.get(
        "/api/users?skip=0&limit=1000",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422
    
    response = client.get(
        "/api/users?skip=0&limit=0",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])