"""
PDF Microservice
A FastAPI based PDF generation service that creates reports.
"""

from fastapi import FastAPI, HTTPException, Depends, status
from sqlalchemy.exc import SQLAlchemyError
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
from uuid import UUID
import logging
import os
from io import BytesIO

from config import (
    CORS_ORIGINS,
    CORS_CREDENTIALS,
    CORS_METHODS,
    CORS_HEADERS,
    HOST,
    PORT,
    DEBUG,
    PDF_STORAGE_PATH
)

from auth import get_current_user, extract_token

from schemas import (
    PDFResponse,
    GoalPDFResponse,
    HealthResponse
)

from user_client import get_user_data
from goals_client import get_user_goals, get_goal_by_id
from entries_client import get_user_time_stats, get_goal_total_hours

from pdf_generator import generate_goal_report_pdf, generate_goal_specific_pdf
#from database import get_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="PDF Service",
    description="""PDF generation service for Trackify reports and exports.
    
    This service provides comprehensive PDF generation functionality including:
    - Generate comprehensive user reports with all goals
    - Create goal-specific detailed reports
    - Stream PDFs for large reports
    - Professional formatting with charts and statistics
    - Integration with User, Goals, and Entries services
    - Automatic data aggregation and formatting
    
    **Report Types**:
    - **Full Reports**: Complete user overview with all goals and time data
    - **Goal Reports**: Detailed single-goal analysis
    - **Monthly Reports**: Time-based reporting for specific periods
    
    **Output Options**:
    - Download as file (saved to server)
    - Stream directly (no server storage)
    
    All endpoints require JWT authentication via Bearer token.
    """,
    version="1.0.0",
    docs_url="/api/pdf/docs",
    redoc_url="/api/pdf/redoc",
    openapi_url="/api/pdf/openapi.json",
    contact={
        "name": "Trackify Support",
        "email": "trackify@zusidelavi.com"
    },
    license_info={
        "name": "MIT",
    }
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=CORS_CREDENTIALS,
    allow_methods=CORS_METHODS,
    allow_headers=CORS_HEADERS,
)

os.makedirs(PDF_STORAGE_PATH, exist_ok=True)

# =====================================================
# HEALTH CHECK ENDPOINTS
# =====================================================

@app.get("/api/pdf/health/liveness", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness health check. Confirms the service process is running.
    """
    return HealthResponse(status="healthy")

@app.get("/api/pdf/health/readiness")
async def readiness():
    """
    Readiness health check. Confirms the service actually works. PDF does not have a DB.
    """
    return HealthResponse(status="healthy")

# =====================================================
# PDF GENERATION ENDPOINTS
# =====================================================

@app.get(
    "/api/pdf/report",
    response_class=FileResponse,
    tags=["PDF Reports"],
    summary="Generate Full Report (Download)",
    response_description="PDF file download",
    responses={
        200: {
            "description": "PDF report generated and ready for download",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Failed to generate report"}
    }
)
async def generate_full_report(
    current_user: str = Depends(get_current_user),
    token: str = Depends(extract_token)
):
    """
    Generate a comprehensive PDF report with all user data and goals.
    
    **Report Contents**:
    - User profile information
    - Complete list of all goals with details
    - Time tracking statistics for each goal
    - Overall time summary and analytics
    - Progress indicators and completion rates
    - Professional formatting with headers and footers
    
    **Data Sources**:
    - User Service: Profile information
    - Goals Service: All user goals
    - Entries Service: Time tracking data and statistics
    
    **File Handling**:
    - PDF saved to server storage
    - Returned as downloadable file
    - Filename includes timestamp for uniqueness
    
    **Use Cases**:
    - Export complete user data
    - Generate progress reports
    - Create backups of tracking data
    - Share overview with stakeholders
    
    **Authentication**: Required (Bearer token)
    """
    try:
        user_data = await get_user_data(current_user, token)
        goals = await get_user_goals(token)
        entries_stats = await get_user_time_stats(token)
        
        pdf_bytes = generate_goal_report_pdf(user_data, goals, entries_stats)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trackify_report_{timestamp}.pdf"
        filepath = os.path.join(PDF_STORAGE_PATH, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"Report PDF generated: {filename} for user {current_user}")
        
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@app.get(
    "/api/pdf/report/stream",
    response_class=StreamingResponse,
    tags=["PDF Reports"],
    summary="Generate Full Report (Stream)",
    response_description="PDF file stream",
    responses={
        200: {
            "description": "PDF report streamed directly to client",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Failed to generate report"}
    }
)
async def generate_full_report_stream(
    current_user: str = Depends(get_current_user),
    token: str = Depends(extract_token)
):
    """
    Generate and stream a comprehensive PDF report directly to client.
    
    **Same content as `/api/pdf/report`** but delivered via streaming.
    
    **Advantages of Streaming**:
    - No server storage required
    - Faster initial response
    - Better for large reports
    - Reduced disk I/O
    - Suitable for high-traffic scenarios
    
    **Report Contents**: Identical to the download endpoint, including
    user data, all goals, and complete time tracking statistics.
    
    **When to Use**:
    - Large reports that don't need server storage
    - High-frequency report generation
    - Memory-efficient processing
    - Direct client delivery without caching
    
    **Authentication**: Required (Bearer token)
    """
    try:
        user_data = await get_user_data(current_user, token)
        goals = await get_user_goals(token)
        entries_stats = await get_user_time_stats(token)
        
        pdf_bytes = generate_goal_report_pdf(user_data, goals, entries_stats)
        
        logger.info(f"Report PDF streamed for user {current_user}")
        
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": "attachment; filename=trackify_report.pdf"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming report: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate report: {str(e)}"
        )

@app.get(
    "/api/pdf/goal/{goal_id}",
    response_class=FileResponse,
    tags=["PDF Reports"],
    summary="Generate Goal Report (Download)",
    response_description="PDF file download for specific goal",
    responses={
        200: {
            "description": "Goal PDF report generated successfully",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        404: {"description": "Goal not found"},
        500: {"description": "Failed to generate goal PDF"}
    }
)
async def generate_goal_pdf(
    goal_id: UUID,
    current_user: str = Depends(get_current_user),
    token: str = Depends(extract_token)
):
    """
    Generate a detailed PDF report for a specific goal.
    
    **Report Contents**:
    - Goal details (title, description, timeline)
    - Target hours and current progress
    - User information
    - Time tracking statistics
    - Progress visualization
    - Hourly rate and earnings calculations (if configured)
    
    **Data Sources**:
    - Goals Service: Goal details
    - User Service: User profile
    - Entries Service: Time tracking data
    
    **File Naming**: Filename includes goal title and timestamp
    (e.g., `goal_learn_python_20260112_100530.pdf`)
    
    **Use Cases**:
    - Share goal progress with clients
    - Track individual goal performance
    - Generate client invoices
    - Document goal completion
    
    **Authorization**: Users can only generate reports for their own goals.
    
    **Authentication**: Required (Bearer token)
    """
    try:
        goal_data = await get_goal_by_id(goal_id, token)
        logger.info(f"Goal data fetched: {goal_data}")
        
        user_data = await get_user_data(current_user, token)
        logger.info(f"User data fetched: {user_data}")
        
        goal_hours = await get_goal_total_hours(goal_id, token)
        logger.info(f"Goal hours fetched: {goal_hours}")
        
        try:
            pdf_bytes = generate_goal_specific_pdf(goal_data, user_data, goal_hours)
            logger.info(f"PDF bytes generated, type: {type(pdf_bytes)}, is None: {pdf_bytes is None}, length: {len(pdf_bytes) if pdf_bytes else 0}")
        except Exception as pdf_gen_error:
            logger.error(f"PDF generation error: {pdf_gen_error}", exc_info=True)
            raise
        
        if pdf_bytes is None:
            raise ValueError("PDF generation returned None")
        
        goal_title = goal_data.get('title', 'goal').replace(' ', '_').lower()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"goal_{goal_title}_{timestamp}.pdf"
        filepath = os.path.join(PDF_STORAGE_PATH, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"Goal PDF generated: {filename} for user {current_user}")
        
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating goal PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate goal PDF: {str(e)}"
        )

@app.get(
    "/api/pdf/goal/{goal_id}/stream",
    response_class=StreamingResponse,
    tags=["PDF Reports"],
    summary="Generate Goal Report (Stream)",
    response_description="PDF file stream for specific goal",
    responses={
        200: {
            "description": "Goal PDF report streamed successfully",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        404: {"description": "Goal not found"},
        500: {"description": "Failed to generate goal PDF"}
    }
)
async def generate_goal_pdf_stream(
    goal_id: UUID,
    current_user: str = Depends(get_current_user),
    token: str = Depends(extract_token)
):
    """
    Generate and stream a PDF report for a specific goal.
    
    **Same content as `/api/pdf/goal/{goal_id}`** but delivered via streaming.
    
    **Streaming Benefits**:
    - No server storage required
    - Immediate delivery to client
    - Better memory efficiency
    - Ideal for real-time generation
    
    **Report Contents**: Identical to the download endpoint, including
    complete goal details, progress, and time tracking data.
    
    **Use Cases**:
    - Email attachments (via Mailer Service)
    - Real-time report preview
    - API integrations
    - Automated report generation
    
    **Authorization**: Users can only generate reports for their own goals.
    
    **Authentication**: Required (Bearer token)
    """
    try:
        goal_data = await get_goal_by_id(goal_id, token)
        logger.info(f"Goal data fetched for streaming: {goal_data}")
        
        user_data = await get_user_data(current_user, token)
        logger.info(f"User data fetched for streaming: {user_data}")
        
        goal_hours = await get_goal_total_hours(goal_id, token)
        logger.info(f"Goal hours fetched for streaming: {goal_hours}")
        
        pdf_bytes = generate_goal_specific_pdf(goal_data, user_data, goal_hours)
        logger.info(f"PDF bytes generated for streaming, type: {type(pdf_bytes)}, is None: {pdf_bytes is None}")
        
        if pdf_bytes is None:
            raise ValueError("PDF generation returned None")
        
        logger.info(f"Goal PDF streamed for user {current_user}, goal {goal_id}")
        
        goal_title = goal_data.get('title', 'goal').replace(' ', '_').lower()
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename=goal_{goal_title}.pdf"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error streaming goal PDF: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate goal PDF: {str(e)}"
        )

@app.post(
    "/api/pdf/generate",
    response_class=FileResponse,
    tags=["PDF Reports"],
    summary="Generate Comprehensive PDF (POST)",
    response_description="PDF file download",
    responses={
        200: {
            "description": "Comprehensive PDF report generated",
            "content": {
                "application/pdf": {
                    "schema": {
                        "type": "string",
                        "format": "binary"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Failed to generate PDF"}
    }
)
async def generate_pdf(
    current_user: str = Depends(get_current_user),
    token: str = Depends(extract_token)
):
    """
    Generate a comprehensive PDF report with all user data and goals (POST method).
    
    **Functionality**: Identical to `GET /api/pdf/report` but uses POST method.
    
    **POST vs GET**:
    - POST method allows for future expansion with request body parameters
    - Can support custom report configurations
    - Better for complex report generation with filters
    - Semantic distinction for generation operations
    
    **Report Contents**:
    - Complete user profile
    - All goals with full details
    - Time tracking statistics
    - Progress analytics
    
    **Future Enhancements** (planned):
    - Date range filtering
    - Goal selection
    - Custom report templates
    - Output format options
    
    **Authentication**: Required (Bearer token)
    """
    try:
        user_data = await get_user_data(current_user, token)
        goals = await get_user_goals(token)
        entries_stats = await get_user_time_stats(token)
        
        pdf_bytes = generate_goal_report_pdf(user_data, goals, entries_stats)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"trackify_report_{timestamp}.pdf"
        filepath = os.path.join(PDF_STORAGE_PATH, filename)
        
        with open(filepath, 'wb') as f:
            f.write(pdf_bytes)
        
        logger.info(f"Comprehensive PDF generated: {filename} for user {current_user}")
        
        return FileResponse(
            path=filepath,
            media_type="application/pdf",
            filename=filename
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate PDF: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
