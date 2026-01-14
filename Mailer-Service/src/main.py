"""
Mailer Microservice
A FastAPI based mailer service for sending scheduled monthly reports.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone, timedelta
from dateutil.relativedelta import relativedelta
from uuid import UUID
import logging
import asyncio
import calendar

from config import (
    CORS_ORIGINS,
    CORS_CREDENTIALS,
    CORS_METHODS,
    CORS_HEADERS,
    HOST,
    PORT,
    DEBUG,
    ENTRIES_SERVICE_URL,
    USER_SERVICE_URL
)

from database import init_db, get_db, Mail
from auth import get_current_user, get_current_user_with_token

from schemas import (
    MailCreate,
    MailUpdate,
    MailResponse,
    MailListResponse,
    SendMailRequest,
    SendMailResponse,
    HealthResponse,
    EmailSettingsCreate,
    EmailSettingsUpdate,
    EmailSettingsResponse,
    SendNowRequest
)

from ses_client import send_email
from pdf_client import generate_report_pdf, fetch_pdf_from_service
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Mailer Service",
    description="""Email sending microservice for Trackify with Amazon SES integration.
    
    This service provides comprehensive email functionality including:
    - Send individual emails via Amazon SES
    - Batch email sending capabilities
    - Scheduled monthly report emails
    - Email settings management per goal
    - PDF attachment support
    - Integration with PDF Service for report generation
    - Automatic monthly report scheduling
    
    **Features**:
    - Configure email settings per goal with custom send day
    - Automatic monthly report generation and sending
    - Send reports immediately on-demand
    - Track email delivery status and history
    
    All endpoints require JWT authentication via Bearer token.
    """,
    version="1.0.0",
    docs_url="/api/mail/docs",
    redoc_url="/api/mail/redoc",
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

scheduler_running = False

async def get_user_info(user_id: str, token: str) -> dict:
    """Fetch user information from User Service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{USER_SERVICE_URL}/api/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10.0
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Failed to fetch user info: {response.status_code}")
                return {}
    except Exception as e:
        logger.error(f"Error fetching user info: {str(e)}")
        return {}

async def get_entries_for_month(goal_id: UUID, year: int, month: int, token: str) -> list:
    """Fetch entries from Entries Service for a specific month"""
    try:
        first_day = datetime(year, month, 1)
        last_day_num = calendar.monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num, 23, 59, 59)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{ENTRIES_SERVICE_URL}/api/entries",
                params={
                    "goal_id": str(goal_id),
                    "page": 1,
                    "page_size": 100,  
                },
                headers={"Authorization": f"Bearer {token}"},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                entries = data.get("entries", [])
                filtered_entries = []
                for entry in entries:
                    work_date_str = entry.get("work_date")
                    if not work_date_str:
                        continue
                    
                    work_date = datetime.fromisoformat(work_date_str.split('T')[0])
                    if work_date.year == year and work_date.month == month:
                        filtered_entries.append(entry)
                
                return filtered_entries
            else:
                logger.error(f"Failed to fetch entries: {response.status_code}")
                return []
    except Exception as e:
        logger.error(f"Error fetching entries: {str(e)}")
        return []

async def generate_monthly_report_email(goal_id: UUID, recipient_email: str, user_id: str, token: str) -> tuple[str, str, bytes]:
    """Generate email content and PDF for monthly report"""
    today = datetime.now(timezone.utc)
    first_day_current = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    last_day_prev = first_day_current - timedelta(days=1)
    first_day_prev = last_day_prev.replace(day=1)
    
    month_name = last_day_prev.strftime("%B %Y")
    entries = await get_entries_for_month(
        goal_id,
        last_day_prev.year,
        last_day_prev.month,
        token
    )
    
    user_info = await get_user_info(user_id, token)
    user_display_name = user_info.get("full_name") or user_info.get("google_email") or recipient_email
    
    total_minutes = sum(float(entry.get("minutes", 0)) for entry in entries)
    total_hours = total_minutes / 60
    
    pdf_data = await generate_report_pdf(goal_id, last_day_prev.year, last_day_prev.month, token)
    
    subject = f"Monthly Time Report - {month_name}"
    body = f"""
    <html>
    <body style="font-family: Arial, sans-serif;">
        <h2>Monthly Time Report for {month_name}</h2>
        <p>Here is {user_display_name}'s monthly time tracking report.</p>
        <h3>Summary:</h3>
        <ul>
            <li><strong>Total Hours:</strong> {total_hours:.2f} hours</li>
            <li><strong>Total Entries:</strong> {len(entries)}</li>
            <li><strong>Period:</strong> {first_day_prev.strftime('%B %d')} - {last_day_prev.strftime('%B %d, %Y')}</li>
        </ul>
        <p>Please find the detailed report attached as a PDF.</p>
        <p>Best regards,<br>Trackify Team</p>
    </body>
    </html>
    """
    
    return subject, body, pdf_data

async def send_scheduled_emails():
    """Background task to send scheduled emails"""
    global scheduler_running
    scheduler_running = True
    
    logger.info("Email scheduler started")
    
    while scheduler_running:
        try:
            await asyncio.sleep(3600)
            today = datetime.now(timezone.utc)
            current_day = today.day
            
            last_day_of_month = calendar.monthrange(today.year, today.month)[1]
            is_last_day = current_day == last_day_of_month
            
            db = next(get_db())
            
            try:
                if is_last_day:
                    settings_to_send = db.query(Mail).filter(
                        Mail.enabled == True,
                        Mail.sent_when >= current_day,  
                        Mail.related_goal_id != None
                    ).all()
                    logger.info(f"Last day of month ({current_day}): Found {len(settings_to_send)} emails to send (scheduled for day {current_day} or later)")
                else:
                    settings_to_send = db.query(Mail).filter(
                        Mail.enabled == True,
                        Mail.sent_when == current_day,
                        Mail.related_goal_id != None
                    ).all()
                    logger.info(f"Found {len(settings_to_send)} emails to send today (day {current_day})")
                
                for setting in settings_to_send:
                    if setting.last_sent_at:
                        last_sent = setting.last_sent_at.replace(tzinfo=timezone.utc)
                        if last_sent.month == today.month and last_sent.year == today.year:
                            logger.info(f"Email for goal {setting.goal_id} already sent this month")
                            continue
                    
                    try:
                        token = "system_token"  
                        subject, body, pdf_data = await generate_monthly_report_email(
                            setting.related_goal_id,
                            setting.recipient,
                            setting.owner_user_id,
                            token
                        )
                        
                        message_id = send_email(
                            recipient=setting.recipient,
                            subject=subject,
                            body=body,
                            pdf_attachment=pdf_data,
                            pdf_filename=f"report_{datetime.now().strftime('%Y_%m')}.pdf"
                        )
                        
                        setting.last_sent_at = datetime.now(timezone.utc)
                        setting.updated_at = datetime.now(timezone.utc)
                        db.commit()
                        
                        logger.info(f"Scheduled email sent for goal {setting.related_goal_id}, MessageId: {message_id}")
                        
                    except Exception as e:
                        logger.error(f"Failed to send scheduled email for goal {setting.related_goal_id}: {str(e)}")
                        db.rollback()
                        
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Error in email scheduler: {str(e)}")

@app.on_event("startup")
async def startup_event():
    """Initialize database and start scheduler on application startup"""
    try:
        init_db()
        logger.info("Database initialized successfully")
        
        asyncio.create_task(send_scheduled_emails())
        logger.info("Email scheduler task created")
    except Exception as e:
        logger.error(f"Failed to initialize: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Stop scheduler on shutdown"""
    global scheduler_running
    scheduler_running = False
    logger.info("Email scheduler stopped")

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/api/mail/health/liveness", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness health check. Confirms the service process is running.
    """
    return HealthResponse(status="healthy")

@app.get("/api/mail/health/readiness")
async def readiness():
    """
    Readiness health check. Confirms the service actually works.
    """
    try:
        db = next(get_db())
        db.execute("SELECT 1")
    except SQLAlchemyError:
        return HealthResponse(status="unhealthy"), 503
    return HealthResponse(status="healthy")

# =====================================================
# MAIL MANAGEMENT ENDPOINTS
# =====================================================

@app.post(
    "/api/mail",
    response_model=MailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Mail Management"],
    summary="Create Mail Record",
    response_description="Mail record created successfully",
    responses={
        201: {
            "description": "Mail record created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "mail_id": "123e4567-e89b-12d3-a456-426614174000",
                        "owner_user_id": "google_12345",
                        "recipient": "user@example.com",
                        "subject": "Monthly Report",
                        "body": "<html>...</html>",
                        "status": "pending",
                        "created_at": "2026-01-12T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def create_mail(
    mail_data: MailCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new mail record (draft) without sending.
    
    **Optional PDF Integration**:
    - Set `include_pdf` to true and provide `pdf_goal_id`
    - PDF will be fetched from PDF Service and attached
    - PDF URL/reference stored with mail record
    
    **Mail Status**: Created mails have status "pending" until sent.
    
    **Use Cases**:
    - Prepare emails for later sending
    - Create email templates
    - Queue emails for batch processing
    
    **Authentication**: Required (Bearer token)
    """
    try:
        pdf_url = None
        
        if mail_data.include_pdf and mail_data.pdf_goal_id:
            try:
                pdf_data = await fetch_pdf_from_service(
                    mail_data.pdf_goal_id,
                    "Bearer token_here"
                )
                pdf_url = f"pdf://{mail_data.pdf_goal_id}"
                logger.info(f"PDF fetched for goal {mail_data.pdf_goal_id}")
            except HTTPException as e:
                logger.warning(f"Failed to fetch PDF: {str(e)}")
                if not mail_data.include_pdf:
                    raise
        
        mail = Mail(
            owner_user_id=current_user,  
            related_goal_id=mail_data.related_goal_id,
            recipient=mail_data.recipient,
            subject=mail_data.subject,
            body=mail_data.body,
            pdf_url=pdf_url,
            status="pending"
        )
        
        db.add(mail)
        db.commit()
        db.refresh(mail)
        
        logger.info(f"Mail created: {mail.mail_id}")
        return MailResponse.from_orm(mail)
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create mail"
        )

@app.get("/api/mail", response_model=MailListResponse)
async def list_mails(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status_filter: str = Query(None),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    List mails for current user with pagination
    """
    try:
        query = db.query(Mail).filter(Mail.owner_user_id == current_user)
        
        if status_filter:
            query = query.filter(Mail.status == status_filter)
        
        total = query.count()
        mails = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "mails": [MailResponse.from_orm(mail) for mail in mails],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve mails"
        )

@app.get("/api/mail/{mail_id}", response_model=MailResponse)
async def get_mail(
    mail_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a specific mail by ID
    """
    mail = db.query(Mail).filter(
        Mail.mail_id == mail_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not mail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mail not found"
        )
    
    return MailResponse.from_orm(mail)

@app.put("/api/mail/{mail_id}", response_model=MailResponse)
async def update_mail(
    mail_id: UUID,
    mail_data: MailUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update a mail record (only if not sent)
    """
    mail = db.query(Mail).filter(
        Mail.mail_id == mail_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not mail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mail not found"
        )
    
    if mail.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a sent mail"
        )
    
    try:
        if mail_data.recipient:
            mail.recipient = mail_data.recipient
        if mail_data.subject:
            mail.subject = mail_data.subject
        if mail_data.body:
            mail.body = mail_data.body
        if mail_data.sent_when is not None:
            mail.sent_when = mail_data.sent_when
        
        mail.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(mail)
        
        logger.info(f"Mail updated: {mail_id}")
        return MailResponse.from_orm(mail)
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update mail"
        )

@app.delete("/api/mail/{mail_id}", status_code=204)
async def delete_mail(
    mail_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete a mail record (only if not sent)
    """
    mail = db.query(Mail).filter(
        Mail.mail_id == mail_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not mail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mail not found"
        )
    
    if mail.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a sent mail"
        )
    
    try:
        db.delete(mail)
        db.commit()
        logger.info(f"Mail deleted: {mail_id}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete mail"
        )

# =====================================================
# EMAIL SETTINGS ENDPOINTS
# =====================================================

@app.post(
    "/api/mail/settings",
    response_model=EmailSettingsResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Email Settings"],
    summary="Create/Update Email Settings",
    response_description="Email settings configured",
    responses={
        201: {
            "description": "Email settings created or updated",
            "content": {
                "application/json": {
                    "example": {
                        "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "recipient_email": "user@example.com",
                        "enabled": True,
                        "send_day": 28,
                        "last_sent_at": None
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def create_email_settings(
    settings_data: EmailSettingsCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Configure automatic monthly email reports for a specific goal.
    
    **Settings Configuration**:
    - `goal_id`: Goal to send reports for
    - `recipient_email`: Email address to receive reports
    - `enabled`: Enable/disable automatic sending
    - `send_day`: Day of month to send (1-31)
    
    **Scheduling Logic**:
    - Reports sent on specified day each month
    - If day > last day of month (e.g., 31 in February), sends on last day
    - Reports cover the previous complete month
    
    **Idempotent**: If settings exist, they will be updated.
    
    **Use Cases**:
    - Set up automatic monthly progress reports
    - Configure client reporting
    - Enable stakeholder updates
    
    **Authentication**: Required (Bearer token)
    """
    try:
        existing = db.query(Mail).filter(
            Mail.related_goal_id == settings_data.goal_id,
            Mail.owner_user_id == current_user
        ).first()
        
        if existing:
            existing.recipient = settings_data.recipient_email
            existing.enabled = settings_data.enabled
            existing.sent_when = settings_data.send_day
            existing.updated_at = datetime.now(timezone.utc)
            db.commit()
            db.refresh(existing)
            logger.info(f"Email settings updated for goal: {settings_data.goal_id}")
            return EmailSettingsResponse.from_orm(existing)
        
        mail = Mail(
            owner_user_id=current_user,
            related_goal_id=settings_data.goal_id,
            recipient=settings_data.recipient_email,
            subject="Monthly Progress Report", 
            body="",  
            enabled=settings_data.enabled,
            sent_when=settings_data.send_day,
            status="scheduled"
        )
        
        db.add(mail)
        db.commit()
        db.refresh(mail)
        
        logger.info(f"Email settings created for goal: {settings_data.goal_id}")
        return EmailSettingsResponse.from_orm(mail)
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create email settings"
        )

@app.get(
    "/api/mail/settings/{goal_id}",
    response_model=EmailSettingsResponse,
    tags=["Email Settings"],
    summary="Get Email Settings",
    responses={
        200: {"description": "Email settings retrieved successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Email settings not found for this goal"},
        500: {"description": "Internal server error"}
    }
)
async def get_email_settings(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get email settings configuration for a specific goal.
    
    Returns current email settings including:
    - Recipient email address
    - Enabled/disabled status
    - Scheduled send day
    - Last sent timestamp
    
    **Authorization**: Users can only access their own goal settings.
    
    **Authentication**: Required (Bearer token)
    """
    settings = db.query(Mail).filter(
        Mail.related_goal_id == goal_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email settings not found for this goal"
        )
    
    return EmailSettingsResponse.from_orm(settings)

@app.put(
    "/api/mail/settings/{goal_id}",
    response_model=EmailSettingsResponse,
    tags=["Email Settings"],
    summary="Update Email Settings",
    responses={
        200: {"description": "Email settings updated successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Email settings not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_email_settings(
    goal_id: UUID,
    settings_data: EmailSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update email settings for a goal.
    
    **Partial Updates**: All fields are optional. Only provided fields will be updated.
    
    **Common Use Cases**:
    - Change recipient email
    - Enable/disable automatic sending
    - Adjust send day (e.g., from 15th to 28th)
    - Temporarily disable then re-enable
    
    **Note**: Changes take effect immediately for future scheduled sends.
    
    **Authorization**: Users can only update their own goal settings.
    
    **Authentication**: Required (Bearer token)
    """
    settings = db.query(Mail).filter(
        Mail.related_goal_id == goal_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email settings not found for this goal"
        )
    
    try:
        if settings_data.recipient_email is not None:
            settings.recipient = settings_data.recipient_email
        if settings_data.enabled is not None:
            settings.enabled = settings_data.enabled
        if settings_data.send_day is not None:
            settings.sent_when = settings_data.send_day
        
        settings.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(settings)
        
        logger.info(f"Email settings updated for goal: {goal_id}")
        return EmailSettingsResponse.from_orm(settings)
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update email settings"
        )

@app.delete(
    "/api/mail/settings/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Email Settings"],
    summary="Delete Email Settings",
    responses={
        204: {"description": "Email settings deleted successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Email settings not found"},
        500: {"description": "Internal server error"}
    }
)
async def delete_email_settings(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Delete email settings for a goal.
    
    **Effect**: Stops all automatic monthly reports for this goal.
    
    **Warning**: This action is irreversible. Settings must be recreated
    if you want to re-enable automatic reports.
    
    **Note**: Does not delete historical sent emails, only prevents future sends.
    
    **Authorization**: Users can only delete their own goal settings.
    
    **Authentication**: Required (Bearer token)
    """
    settings = db.query(Mail).filter(
        Mail.related_goal_id == goal_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email settings not found for this goal"
        )
    
    try:
        db.delete(settings)
        db.commit()
        logger.info(f"Email settings deleted for goal: {goal_id}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete email settings"
        )

# =====================================================
# MAIL SENDING ENDPOINTS
# =====================================================

@app.post(
    "/api/mail/send-now",
    response_model=SendMailResponse,
    tags=["Email Sending"],
    summary="Send Monthly Report Now",
    response_description="Report email sent immediately",
    responses={
        200: {
            "description": "Email sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "mail_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "sent",
                        "message": "Report email sent successfully to user@example.com",
                        "sent_at": "2026-01-12T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        404: {"description": "Email settings not found for this goal"},
        500: {"description": "Failed to send email"}
    }
)
async def send_now(
    request: SendNowRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    user_with_token: tuple[str, str] = Depends(get_current_user_with_token)
):
    """
    Send a monthly report email immediately for a specific goal.
    
    **Prerequisites**: Email settings must be configured for the goal.
    Use the email settings endpoints to set up recipient and preferences.
    
    **Report Generation**:
    - Fetches previous month's time entries from Entries Service
    - Generates comprehensive PDF report via PDF Service
    - Calculates summary statistics (total hours, entry count)
    - Sends HTML email with PDF attachment
    
    **Email Content**:
    - Professional HTML template
    - Summary statistics (hours, entries, period)
    - PDF attachment with detailed breakdown
    - Sent via Amazon SES
    
    **Use Cases**:
    - Send report outside regular schedule
    - Manual report generation
    - Testing email configuration
    
    **Authentication**: Required (Bearer token)
    """
    current_user, token = user_with_token
    
    settings = db.query(Mail).filter(
        Mail.related_goal_id == request.goal_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not settings:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email settings not found for this goal. Please configure email settings first."
        )
    
    try:
        subject, body, pdf_data = await generate_monthly_report_email(
            request.goal_id,
            settings.recipient,
            current_user,
            token
        )
        
        message_id = send_email(
            recipient=settings.recipient,
            subject=subject,
            body=body,
            pdf_attachment=pdf_data,
            pdf_filename=f"report_{datetime.now(timezone.utc).strftime('%Y_%m')}.pdf"
        )
        
        settings.last_sent_at = datetime.now(timezone.utc)
        settings.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.info(f"Immediate email sent for goal {request.goal_id}, MessageId: {message_id}")
        
        return SendMailResponse(
            mail_id=request.goal_id,  
            status="sent",
            message=f"Report email sent successfully to {settings.recipient}",
            sent_at=datetime.now(timezone.utc)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to send immediate email: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send email: {str(e)}"
        )

# =====================================================
# MAIL SENDING ENDPOINTS
# =====================================================

@app.post(
    "/api/mail/{mail_id}/send",
    response_model=SendMailResponse,
    tags=["Email Sending"],
    summary="Send Mail by ID",
    response_description="Mail sent via Amazon SES",
    responses={
        200: {
            "description": "Mail sent successfully",
            "content": {
                "application/json": {
                    "example": {
                        "mail_id": "123e4567-e89b-12d3-a456-426614174000",
                        "status": "sent",
                        "message": "Mail sent successfully (MessageId: xxx)",
                        "sent_at": "2026-01-12T10:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Mail already sent"},
        401: {"description": "Unauthorized"},
        404: {"description": "Mail not found"},
        500: {"description": "Failed to send via SES"}
    }
)
async def send_mail(
    mail_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Send a mail record via Amazon SES.
    
    **Process**:
    1. Validates mail exists and belongs to user
    2. Checks mail has not been sent already
    3. Sends via Amazon SES
    4. Updates status to "sent" with timestamp
    5. Returns SES MessageId for tracking
    
    **Error Handling**: If sending fails, status is marked as "failed"
    with error message stored.
    
    **Idempotency**: Cannot send the same mail twice. Returns error if
    mail status is already "sent".
    
    **Authorization**: Users can only send their own mails.
    
    **Authentication**: Required (Bearer token)
    """
    mail = db.query(Mail).filter(
        Mail.mail_id == mail_id,
        Mail.owner_user_id == current_user
    ).first()
    
    if not mail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mail not found"
        )
    
    if mail.status == "sent":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mail already sent"
        )
    
    try:
        message_id = send_email(
            recipient=mail.recipient,
            subject=mail.subject,
            body=mail.body
        )
        
        mail.status = "sent"
        mail.sent_at = datetime.now(timezone.utc)
        mail.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(mail)
        
        logger.info(f"Mail sent: {mail_id}, SES MessageId: {message_id}")
        
        return {
            "mail_id": mail.mail_id,
            "status": "sent",
            "message": f"Mail sent successfully (MessageId: {message_id})",
            "sent_at": mail.sent_at
        }
    
    except HTTPException as e:
        mail.status = "failed"
        mail.error_message = e.detail
        mail.updated_at = datetime.now(timezone.utc)
        db.commit()
        
        logger.error(f"Failed to send mail {mail_id}: {e.detail}")
        raise
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update mail status"
        )

@app.post(
    "/api/mail/batch/send",
    tags=["Email Sending"],
    summary="Send Multiple Mails",
    response_description="Batch send results",
    responses={
        200: {
            "description": "Batch processing completed",
            "content": {
                "application/json": {
                    "example": {
                        "total": 5,
                        "results": [
                            {
                                "mail_id": "123e4567-e89b-12d3-a456-426614174000",
                                "status": "sent",
                                "message": "Mail sent successfully"
                            },
                            {
                                "mail_id": "123e4567-e89b-12d3-a456-426614174001",
                                "status": "failed",
                                "message": "Mail not found"
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def send_batch_mails(
    mail_ids: list[UUID],
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Send multiple mail records in a single batch operation.
    
    **Batch Processing**:
    - Processes each mail ID sequentially
    - Continues on individual failures
    - Returns detailed status for each mail
    
    **Result Status Types**:
    - `sent`: Successfully sent via SES
    - `skipped`: Mail already sent previously
    - `failed`: Error occurred (see message for details)
    
    **Use Cases**:
    - Send multiple queued emails at once
    - Bulk email operations
    - Scheduled batch sends
    
    **Note**: Partial success is possible. Check individual results.
    
    **Authorization**: Only processes mails owned by authenticated user.
    
    **Authentication**: Required (Bearer token)
    """
    results = []
    
    for mail_id in mail_ids:
        try:
            mail = db.query(Mail).filter(
                Mail.mail_id == mail_id,
                Mail.owner_user_id == current_user
            ).first()
            
            if not mail:
                results.append({
                    "mail_id": mail_id,
                    "status": "failed",
                    "message": "Mail not found"
                })
                continue
            
            if mail.status == "sent":
                results.append({
                    "mail_id": mail_id,
                    "status": "skipped",
                    "message": "Mail already sent"
                })
                continue
            
            message_id = send_email(
                recipient=mail.recipient,
                subject=mail.subject,
                body=mail.body
            )
            
            mail.status = "sent"
            mail.sent_at = datetime.now(timezone.utc)
            mail.updated_at = datetime.now(timezone.utc)
            db.commit()
            
            results.append({
                "mail_id": mail_id,
                "status": "sent",
                "message": f"Mail sent successfully (MessageId: {message_id})"
            })
        
        except Exception as e:
            results.append({
                "mail_id": mail_id,
                "status": "failed",
                "message": str(e)
            })
    
    return {
        "total": len(mail_ids),
        "results": results
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
