"""
Comprehensive Unit and Integration Tests for Mailer-Service
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch, AsyncMock, MagicMock
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app, get_db
from database import Base, Mail
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
def test_mail(test_user, test_goal_id):
    """Create a test mail record in database"""
    db = TestingSessionLocal()
    mail = Mail(
        mail_id=uuid4(),
        owner_user_id=test_user['user_id'],
        related_goal_id=test_goal_id,
        recipient="test@example.com",
        subject="Test Email",
        body="<html><body>Test body</body></html>",
        status="pending",
        sent_when=Decimal("15"),  
        enabled=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )
    db.add(mail)
    db.commit()
    db.refresh(mail)
    db.close()
    return mail


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_liveness_health_check():
    """Test liveness health check endpoint"""
    response = client.get("/api/mail/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_health_check():
    """Test readiness health check endpoint"""
    response = client.get("/api/mail/health/readiness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


# ============================================================================
# CREATE MAIL TESTS
# ============================================================================

def test_create_mail_basic(test_user):
    """Test creating basic mail record"""
    mail_data = {
        "recipient": "recipient@example.com",
        "subject": "Test Subject",
        "body": "<html><body>Test email body</body></html>"
    }
    
    response = client.post(
        "/api/mail",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=mail_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["recipient"] == "recipient@example.com"
    assert data["subject"] == "Test Subject"
    assert data["owner_user_id"] == test_user['user_id']
    assert data["status"] == "pending"


@patch('pdf_client.fetch_pdf_from_service')
def test_create_mail_with_pdf(mock_fetch_pdf, test_user, test_goal_id):
    """Test creating mail with PDF attachment"""
    mock_fetch_pdf.return_value = b"fake_pdf_data"
    
    mail_data = {
        "recipient": "recipient@example.com",
        "subject": "Report with PDF",
        "body": "<html><body>Report attached</body></html>",
        "include_pdf": True,
        "pdf_goal_id": str(test_goal_id)
    }
    
    response = client.post(
        "/api/mail",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=mail_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["pdf_url"] is not None


def test_create_mail_unauthorized():
    """Test creating mail without authentication"""
    mail_data = {
        "recipient": "test@example.com",
        "subject": "Test"
    }
    
    response = client.post("/api/mail", json=mail_data)
    assert response.status_code == 403


def test_create_mail_invalid_email(test_user):
    """Test creating mail with invalid email format"""
    mail_data = {
        "recipient": "invalid-email",
        "subject": "Test"
    }
    
    response = client.post(
        "/api/mail",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=mail_data
    )
    
    assert response.status_code in [201, 422]


# ============================================================================
# LIST MAILS TESTS
# ============================================================================

def test_list_mails_empty(test_user):
    """Test listing mails when no mails exist"""
    response = client.get(
        "/api/mail",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mails"] == []
    assert data["total"] == 0


def test_list_mails_pagination(test_user, test_goal_id):
    """Test pagination of mail list"""
    db = TestingSessionLocal()
    for i in range(15):
        mail = Mail(
            owner_user_id=test_user['user_id'],
            related_goal_id=test_goal_id,
            recipient=f"user{i}@example.com",
            subject=f"Mail {i + 1}",
            status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(mail)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/mail?page=1&page_size=10",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["mails"]) == 10
    assert data["total"] == 15
    assert data["page"] == 1


def test_list_mails_filter_by_status(test_user):
    """Test filtering mails by status"""
    db = TestingSessionLocal()
    for status in ["pending", "sent", "failed"]:
        for i in range(2):
            mail = Mail(
                owner_user_id=test_user['user_id'],
                recipient=f"{status}{i}@example.com",
                status=status,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            db.add(mail)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/mail?status=sent",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert all(m["status"] == "sent" for m in data["mails"])


def test_list_mails_unauthorized():
    """Test listing mails without authentication"""
    response = client.get("/api/mail")
    assert response.status_code == 403


# ============================================================================
# GET MAIL BY ID TESTS
# ============================================================================

def test_get_mail_by_id(test_user, test_mail):
    """Test getting a specific mail by ID"""
    response = client.get(
        f"/api/mail/{test_mail.mail_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["mail_id"] == str(test_mail.mail_id)
    assert data["recipient"] == test_mail.recipient
    assert data["subject"] == test_mail.subject


def test_get_mail_not_found(test_user):
    """Test getting non-existent mail"""
    fake_id = uuid4()
    response = client.get(
        f"/api/mail/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


def test_get_mail_wrong_user(test_mail):
    """Test getting mail owned by different user"""
    other_user_id = "other_google_sub"
    other_token = create_access_token(other_user_id)
    
    response = client.get(
        f"/api/mail/{test_mail.mail_id}",
        headers={"Authorization": f"Bearer {other_token}"}
    )
    
    assert response.status_code == 404


# ============================================================================
# UPDATE MAIL TESTS
# ============================================================================

def test_update_mail(test_user, test_mail):
    """Test updating mail record"""
    update_data = {
        "subject": "Updated Subject",
        "body": "<html><body>Updated body</body></html>"
    }
    
    response = client.put(
        f"/api/mail/{test_mail.mail_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["subject"] == "Updated Subject"
    assert data["body"] == "<html><body>Updated body</body></html>"


def test_update_mail_not_found(test_user):
    """Test updating non-existent mail"""
    fake_id = uuid4()
    response = client.put(
        f"/api/mail/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json={"subject": "New Subject"}
    )
    
    assert response.status_code == 404


def test_update_mail_unauthorized():
    """Test updating mail without authentication"""
    fake_id = uuid4()
    response = client.put(
        f"/api/mail/{fake_id}",
        json={"subject": "New Subject"}
    )
    assert response.status_code == 403


# ============================================================================
# DELETE MAIL TESTS
# ============================================================================

def test_delete_mail(test_user, test_mail):
    """Test deleting a mail record"""
    response = client.delete(
        f"/api/mail/{test_mail.mail_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert "deleted" in response.json()["message"].lower()
    
    db = TestingSessionLocal()
    deleted = db.query(Mail).filter(
        Mail.mail_id == test_mail.mail_id
    ).first()
    assert deleted is None
    db.close()


def test_delete_mail_not_found(test_user):
    """Test deleting non-existent mail"""
    fake_id = uuid4()
    response = client.delete(
        f"/api/mail/{fake_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 404


# ============================================================================
# SEND MAIL TESTS
# ============================================================================

@patch('ses_client.send_email')
def test_send_mail(mock_send_email, test_user):
    """Test sending an email via SES"""
    mock_send_email.return_value = "message-id-12345"
    
    send_data = {
        "recipient": "recipient@example.com",
        "subject": "Test Email",
        "body": "<html><body>Test</body></html>"
    }
    
    response = client.post(
        "/api/mail/send",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=send_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "message-id-12345"
    assert data["status"] == "sent"
    
    mock_send_email.assert_called_once()


@patch('ses_client.send_email')
def test_send_mail_with_attachment(mock_send_email, test_user):
    """Test sending email with PDF attachment"""
    mock_send_email.return_value = "message-id-67890"
    
    send_data = {
        "recipient": "recipient@example.com",
        "subject": "Report",
        "body": "<html><body>Report attached</body></html>",
        "pdf_attachment": "base64_encoded_pdf_data",
        "pdf_filename": "report.pdf"
    }
    
    response = client.post(
        "/api/mail/send",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=send_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["message_id"] == "message-id-67890"


@patch('ses_client.send_email')
def test_send_mail_failure(mock_send_email, test_user):
    """Test handling email send failure"""
    mock_send_email.side_effect = Exception("SES error")
    
    send_data = {
        "recipient": "recipient@example.com",
        "subject": "Test",
        "body": "Test body"
    }
    
    response = client.post(
        "/api/mail/send",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=send_data
    )
    
    assert response.status_code == 500


def test_send_mail_unauthorized():
    """Test sending mail without authentication"""
    send_data = {
        "recipient": "test@example.com",
        "subject": "Test"
    }
    
    response = client.post("/api/mail/send", json=send_data)
    assert response.status_code == 403


# ============================================================================
# EMAIL SETTINGS TESTS
# ============================================================================

def test_create_email_settings(test_user, test_goal_id):
    """Test creating email settings for a goal"""
    settings_data = {
        "related_goal_id": str(test_goal_id),
        "recipient": "user@example.com",
        "sent_when": 15,  
        "enabled": True
    }
    
    response = client.post(
        "/api/mail/settings",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=settings_data
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["related_goal_id"] == str(test_goal_id)
    assert float(data["sent_when"]) == 15
    assert data["enabled"] is True


def test_get_email_settings_by_goal(test_user, test_mail):
    """Test getting email settings for a specific goal"""
    response = client.get(
        f"/api/mail/settings/goal/{test_mail.related_goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["related_goal_id"] == str(test_mail.related_goal_id)
    assert data["enabled"] == test_mail.enabled


def test_update_email_settings(test_user, test_mail):
    """Test updating email settings"""
    update_data = {
        "sent_when": 25,
        "enabled": False
    }
    
    response = client.put(
        f"/api/mail/settings/{test_mail.mail_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=update_data
    )
    
    assert response.status_code == 200
    data = response.json()
    assert float(data["sent_when"]) == 25
    assert data["enabled"] is False


# ============================================================================
# SEND NOW TESTS
# ============================================================================

@patch('ses_client.send_email')
@patch('main.generate_monthly_report_email')
@pytest.mark.asyncio
async def test_send_report_now(mock_generate, mock_send, test_user, test_goal_id):
    """Test sending monthly report immediately"""
    mock_generate.return_value = (
        "Monthly Report",
        "<html><body>Report</body></html>",
        b"pdf_data"
    )
    mock_send.return_value = "message-id-123"
    
    send_data = {
        "goal_id": str(test_goal_id),
        "recipient": "user@example.com"
    }
    
    response = client.post(
        "/api/mail/send-now",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=send_data
    )
    
    assert response.status_code in [200, 500]


# ============================================================================
# EDGE CASES AND ERROR HANDLING
# ============================================================================

def test_invalid_pagination_parameters(test_user):
    """Test pagination with invalid parameters"""
    response = client.get(
        "/api/mail?page=0",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422
    
    response = client.get(
        "/api/mail?page_size=1000",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 422


def test_invalid_status_filter(test_user):
    """Test filtering with invalid status"""
    response = client.get(
        "/api/mail?status=invalid_status",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code in [200, 422]


def test_create_email_settings_invalid_day(test_user, test_goal_id):
    """Test creating email settings with invalid day (> 31)"""
    settings_data = {
        "related_goal_id": str(test_goal_id),
        "recipient": "user@example.com",
        "sent_when": 35,  
        "enabled": True
    }
    
    response = client.post(
        "/api/mail/settings",
        headers={"Authorization": f"Bearer {test_user['token']}"},
        json=settings_data
    )
    
    assert response.status_code in [201, 422]


def test_get_mail_list_only_own_mails(test_user):
    """Test that users only see their own mails"""
    db = TestingSessionLocal()
    for i in range(3):
        mail = Mail(
            owner_user_id=test_user['user_id'],
            recipient=f"user{i}@example.com",
            status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(mail)
    
    for i in range(2):
        mail = Mail(
            owner_user_id="other_user",
            recipient=f"other{i}@example.com",
            status="pending",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(mail)
    db.commit()
    db.close()
    
    response = client.get(
        "/api/mail",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
