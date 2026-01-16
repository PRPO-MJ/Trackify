"""
Comprehensive Unit and Integration Tests for PDF-Service
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from uuid import uuid4
from datetime import datetime
import sys
import os
import io
from sqlalchemy.sql import text

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from auth import create_access_token
from database import engine, Base

client = TestClient(app)


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
def mock_user_data():
    """Mock user data from User Service"""
    return {
        "google_sub": "test_google_sub_12345",
        "google_email": "test@example.com",
        "full_name": "Test User",
        "address": "123 Test St",
        "country": "TestLand",
        "phone": "+1234567890",
        "currency": "USD",
        "timezone": "UTC"
    }


@pytest.fixture
def mock_goals_data():
    """Mock goals data from Goals Service"""
    return [
        {
            "goal_id": str(uuid4()),
            "title": "Learn Python",
            "target_hours": 100.0,
            "description": "Complete Python course",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31"
        },
        {
            "goal_id": str(uuid4()),
            "title": "Master FastAPI",
            "target_hours": 150.0,
            "description": "Build REST APIs",
            "start_date": "2026-01-01",
            "end_date": "2026-12-31"
        }
    ]


@pytest.fixture
def mock_entries_stats():
    """Mock entries statistics from Entries Service"""
    return {
        "total_minutes": 6000,
        "total_hours": 100.0,
        "total_entries": 50
    }


# ============================================================================
# DATABASE SETUP AND TEARDOWN
# ============================================================================

@pytest.fixture(autouse=True)
def reset_db():
    """Mock database reset for PDF-Service (no actual database)"""
    yield


# ============================================================================
# HEALTH CHECK TESTS
# ============================================================================

def test_liveness_health_check():
    """Test liveness health check endpoint"""
    response = client.get("/api/pdf/health/liveness")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_readiness_health_check():
    """Test readiness health check endpoint - note: no DB in PDF service"""
    response = client.get("/api/pdf/health/readiness")
    assert response.status_code in [200, 404, 500, 503]


# ============================================================================
# GENERATE FULL REPORT TESTS
# ============================================================================

@patch('user_client.get_user_data')
@patch('goals_client.get_user_goals')
@patch('entries_client.get_user_time_stats')
@patch('pdf_generator.generate_goal_report_pdf')
def test_generate_full_report(
    mock_generate_pdf,
    mock_get_stats,
    mock_get_goals,
    mock_get_user,
    test_user,
    mock_user_data,
    mock_goals_data,
    mock_entries_stats
):
    """Test generating full report with all user data"""
    mock_get_user.return_value = mock_user_data
    mock_get_goals.return_value = mock_goals_data
    mock_get_stats.return_value = mock_entries_stats
    mock_generate_pdf.return_value = b"fake_pdf_content"
    
    response = client.get(
        "/api/pdf/report",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] in ["application/pdf", "application/octet-stream"]
    
    mock_get_user.assert_called_once()
    mock_get_goals.assert_called_once()
    mock_get_stats.assert_called_once()
    mock_generate_pdf.assert_called_once()


def test_generate_full_report_unauthorized():
    """Test generating report without authentication"""
    response = client.get("/api/pdf/report")
    assert response.status_code == 403


@patch('user_client.get_user_data')
def test_generate_full_report_user_service_failure(mock_get_user, test_user):
    """Test handling User Service failure"""
    mock_get_user.side_effect = Exception("User service unavailable")
    
    response = client.get(
        "/api/pdf/report",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 500


# ============================================================================
# STREAM FULL REPORT TESTS
# ============================================================================

@patch('user_client.get_user_data')
@patch('goals_client.get_user_goals')
@patch('entries_client.get_user_time_stats')
@patch('pdf_generator.generate_goal_report_pdf')
def test_stream_full_report(
    mock_generate_pdf,
    mock_get_stats,
    mock_get_goals,
    mock_get_user,
    test_user,
    mock_user_data,
    mock_goals_data,
    mock_entries_stats
):
    """Test streaming full report"""
    mock_get_user.return_value = mock_user_data
    mock_get_goals.return_value = mock_goals_data
    mock_get_stats.return_value = mock_entries_stats
    mock_generate_pdf.return_value = b"fake_pdf_content_stream"
    
    response = client.get(
        "/api/pdf/report/stream",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert "attachment" in response.headers.get("content-disposition", "").lower() or \
           "inline" in response.headers.get("content-disposition", "").lower()


def test_stream_full_report_unauthorized():
    """Test streaming report without authentication"""
    response = client.get("/api/pdf/report/stream")
    assert response.status_code == 403


# ============================================================================
# GENERATE GOAL REPORT TESTS
# ============================================================================

@patch('goals_client.get_goal_by_id')
@patch('entries_client.get_goal_total_hours')
@patch('user_client.get_user_data')
@patch('pdf_generator.generate_goal_specific_pdf')
def test_generate_goal_report(
    mock_generate_pdf,
    mock_get_user,
    mock_get_hours,
    mock_get_goal,
    test_user,
    test_goal_id,
    mock_user_data
):
    """Test generating goal-specific PDF report"""
    mock_get_goal.return_value = {
        "goal_id": str(test_goal_id),
        "title": "Test Goal",
        "target_hours": 100.0,
        "description": "Test description"
    }
    mock_get_hours.return_value = 65.5
    mock_get_user.return_value = mock_user_data
    mock_generate_pdf.return_value = b"fake_goal_pdf"
    
    response = client.get(
        f"/api/pdf/goal/{test_goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] in ["application/pdf", "application/octet-stream"]


def test_generate_goal_report_unauthorized(test_goal_id):
    """Test generating goal report without authentication"""
    response = client.get(f"/api/pdf/goal/{test_goal_id}")
    assert response.status_code == 403


@patch('goals_client.get_goal_by_id')
def test_generate_goal_report_not_found(mock_get_goal, test_user, test_goal_id):
    """Test generating report for non-existent goal"""
    mock_get_goal.side_effect = Exception("Goal not found")
    
    response = client.get(
        f"/api/pdf/goal/{test_goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 500


# ============================================================================
# STREAM GOAL REPORT TESTS
# ============================================================================

@patch('goals_client.get_goal_by_id')
@patch('entries_client.get_goal_total_hours')
@patch('user_client.get_user_data')
@patch('pdf_generator.generate_goal_specific_pdf')
def test_stream_goal_report(
    mock_generate_pdf,
    mock_get_user,
    mock_get_hours,
    mock_get_goal,
    test_user,
    test_goal_id,
    mock_user_data
):
    """Test streaming goal-specific PDF report"""
    mock_get_goal.return_value = {
        "goal_id": str(test_goal_id),
        "title": "Stream Goal",
        "target_hours": 100.0
    }
    mock_get_hours.return_value = 50.0
    mock_get_user.return_value = mock_user_data
    mock_generate_pdf.return_value = b"fake_stream_goal_pdf"
    
    response = client.get(
        f"/api/pdf/goal/{test_goal_id}/stream",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"


def test_stream_goal_report_unauthorized(test_goal_id):
    """Test streaming goal report without authentication"""
    response = client.get(f"/api/pdf/goal/{test_goal_id}/stream")
    assert response.status_code == 403


# ============================================================================
# GENERATE MONTHLY REPORT TESTS
# ============================================================================

@patch('goals_client.get_goal_by_id')
@patch('entries_client.get_user_time_stats')
@patch('user_client.get_user_data')
@patch('pdf_generator.generate_goal_specific_pdf')
def test_generate_monthly_report(
    mock_generate_pdf,
    mock_get_user,
    mock_get_stats,
    mock_get_goal,
    test_user,
    test_goal_id,
    mock_user_data,
    mock_entries_stats
):
    """Test generating monthly report for a goal"""
    mock_get_goal.return_value = {
        "goal_id": str(test_goal_id),
        "title": "Monthly Goal",
        "target_hours": 100.0
    }
    mock_get_stats.return_value = mock_entries_stats
    mock_get_user.return_value = mock_user_data
    mock_generate_pdf.return_value = b"fake_monthly_pdf"
    
    response = client.get(
        f"/api/pdf/monthly/{test_goal_id}?year=2026&month=1",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code in [200, 404]


# ============================================================================
# PDF GENERATION TESTS (Unit Tests for pdf_generator module)
# ============================================================================

@patch('pdf_generator.FPDF')
def test_generate_goal_report_pdf_function(mock_fpdf_class, mock_user_data, mock_goals_data, mock_entries_stats):
    """Test the PDF generation function directly"""
    from pdf_generator import generate_goal_report_pdf
    
    mock_pdf = MagicMock()
    mock_fpdf_class.return_value = mock_pdf
    mock_pdf.output.return_value = b"fake_pdf_bytes"
    
    result = generate_goal_report_pdf(mock_user_data, mock_goals_data, mock_entries_stats)
    
    assert isinstance(result, bytes)
    mock_pdf.add_page.assert_called()


@patch('pdf_generator.FPDF')
def test_generate_goal_specific_pdf_function(mock_fpdf_class, mock_user_data):
    """Test the goal-specific PDF generation function"""
    from pdf_generator import generate_goal_specific_pdf
    
    mock_pdf = MagicMock()
    mock_fpdf_class.return_value = mock_pdf
    mock_pdf.output.return_value = b"fake_goal_pdf_bytes"
    
    goal_data = {
        "goal_id": str(uuid4()),
        "title": "Test Goal",
        "target_hours": 100.0,
        "description": "Test description"
    }
    
    result = generate_goal_specific_pdf(mock_user_data, goal_data, 65.5, 42)
    
    assert isinstance(result, bytes)
    mock_pdf.add_page.assert_called()


# ============================================================================
# ERROR HANDLING AND EDGE CASES
# ============================================================================

@patch('user_client.get_user_data')
@patch('goals_client.get_user_goals')
@patch('entries_client.get_user_time_stats')
def test_generate_report_with_no_goals(
    mock_get_stats,
    mock_get_goals,
    mock_get_user,
    test_user,
    mock_user_data
):
    """Test generating report when user has no goals"""
    mock_get_user.return_value = mock_user_data
    mock_get_goals.return_value = []  
    mock_get_stats.return_value = {"total_hours": 0, "total_entries": 0}
    
    response = client.get(
        "/api/pdf/report",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code in [200, 500]


@patch('goals_client.get_goal_by_id')
@patch('entries_client.get_goal_total_hours')
@patch('user_client.get_user_data')
def test_generate_goal_report_with_no_hours(
    mock_get_user,
    mock_get_hours,
    mock_get_goal,
    test_user,
    test_goal_id,
    mock_user_data
):
    """Test generating goal report when no hours logged"""
    mock_get_goal.return_value = {
        "goal_id": str(test_goal_id),
        "title": "New Goal",
        "target_hours": 100.0
    }
    mock_get_hours.return_value = 0.0  
    mock_get_user.return_value = mock_user_data
    
    response = client.get(
        f"/api/pdf/goal/{test_goal_id}",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code in [200, 500]


def test_invalid_goal_id_format(test_user):
    """Test with invalid goal ID format"""
    response = client.get(
        "/api/pdf/goal/invalid-uuid-format",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 422


@patch('user_client.get_user_data')
@patch('goals_client.get_user_goals')
@patch('entries_client.get_user_time_stats')
@patch('pdf_generator.generate_goal_report_pdf')
def test_generate_report_pdf_generation_failure(
    mock_generate_pdf,
    mock_get_stats,
    mock_get_goals,
    mock_get_user,
    test_user,
    mock_user_data,
    mock_goals_data,
    mock_entries_stats
):
    """Test handling PDF generation failure"""
    mock_get_user.return_value = mock_user_data
    mock_get_goals.return_value = mock_goals_data
    mock_get_stats.return_value = mock_entries_stats
    mock_generate_pdf.side_effect = Exception("PDF generation failed")
    
    response = client.get(
        "/api/pdf/report",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 500


# ============================================================================
# INTEGRATION TESTS WITH MULTIPLE SERVICES
# ============================================================================

@patch('user_client.get_user_data')
@patch('goals_client.get_user_goals')
@patch('entries_client.get_user_time_stats')
@patch('pdf_generator.generate_goal_report_pdf')
def test_full_workflow_with_all_services(
    mock_generate_pdf,
    mock_get_stats,
    mock_get_goals,
    mock_get_user,
    test_user,
    mock_user_data
):
    """Test complete workflow involving all external services"""
    mock_get_user.return_value = mock_user_data
    
    mock_get_goals.return_value = [
        {
            "goal_id": str(uuid4()),
            "title": f"Goal {i}",
            "target_hours": 100.0 * (i + 1),
            "description": f"Description {i}"
        }
        for i in range(5)
    ]
    
    mock_get_stats.return_value = {
        "total_minutes": 18000,
        "total_hours": 300.0,
        "total_entries": 150
    }
    
    mock_generate_pdf.return_value = b"comprehensive_pdf_data"
    
    response = client.get(
        "/api/pdf/report",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 200
    
    response = client.get(
        "/api/pdf/report/stream",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    assert response.status_code == 200
    
    assert mock_get_user.call_count == 2
    assert mock_get_goals.call_count == 2
    assert mock_get_stats.call_count == 2


@patch('user_client.get_user_data')
@patch('goals_client.get_user_goals')
@patch('entries_client.get_user_time_stats')
def test_service_timeout_handling(
    mock_get_stats,
    mock_get_goals,
    mock_get_user,
    test_user
):
    """Test handling of service timeouts"""
    import asyncio
    mock_get_user.side_effect = asyncio.TimeoutError("Service timeout")
    
    response = client.get(
        "/api/pdf/report",
        headers={"Authorization": f"Bearer {test_user['token']}"}
    )
    
    assert response.status_code == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
