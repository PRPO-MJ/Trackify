"""
Entries Microservice
A FastAPI based time entries service for logging hours / entries.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from datetime import datetime, timezone, time
from uuid import UUID
from typing import Optional
import logging
from decimal import Decimal

from config import (
    CORS_ORIGINS,
    CORS_CREDENTIALS,
    CORS_METHODS,
    CORS_HEADERS,
    HOST,
    PORT,
    DEBUG
)

from database import init_db, get_db, TimeEntry
from auth import get_current_user, security

from schemas import (
    TimeEntryCreate,
    TimeEntryUpdate,
    TimeEntryResponse,
    TimeEntryListResponse,
    TimeEntrySummaryResponse,
    GoalTimeStatsResponse,
    UserTimeStatsResponse,
    HealthResponse
)

from goals_client import validate_goal_ownership

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Entries Service",
    description="""Time entries and time tracking microservice for Trackify.
    
    This service provides comprehensive time tracking functionality including:
    - Creating, updating, and deleting time entries
    - Associating time entries with goals
    - Automatic time calculation from start/end times
    - Advanced filtering and sorting capabilities
    - Statistics and aggregation by goals and users
    
    All endpoints require JWT authentication via Bearer token.
    """,
    version="1.0.0",
    docs_url="/api/entries/docs",
    redoc_url="/api/entries/redoc",
    openapi_url="/api/entries/openapi.json",
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

@app.on_event("startup")
def startup_event():
    """Initialize database on application startup"""
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {str(e)}")
        raise

# =====================================================
# HEALTH CHECK ENDPOINTS
# =====================================================

@app.get("/api/entries/health/liveness", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness health check. Confirms the service process is running.
    """
    return HealthResponse(status="healthy")

@app.get("/api/entries/health/readiness")
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
# TIME ENTRY MANAGEMENT ENDPOINTS
# =====================================================

@app.post(
    "/api/entries",
    response_model=TimeEntryResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Time Entries"],
    summary="Create Time Entry",
    response_description="Time entry created successfully",
    responses={
        201: {
            "description": "Time entry created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "entry_id": "123e4567-e89b-12d3-a456-426614174000",
                        "owner_user_id": "google_12345",
                        "related_goal_id": "123e4567-e89b-12d3-a456-426614174001",
                        "work_date": "2026-01-12",
                        "start_time": "09:00:00",
                        "end_time": "12:00:00",
                        "minutes": 180,
                        "description": "Morning work session",
                        "created_at": "2026-01-12T09:00:00Z",
                        "updated_at": "2026-01-12T09:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid goal ID or validation error"},
        401: {"description": "Unauthorized - invalid or missing token"},
        500: {"description": "Internal server error"}
    }
)
async def create_entry(
    entry_data: TimeEntryCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Create a new time entry for the authenticated user.
    
    Time entries can be created in two ways:
    1. **Manual duration**: Provide `minutes` directly
    2. **Time-based**: Provide `start_time` and `end_time`, minutes will be calculated automatically
    
    Features:
    - Can be associated with a specific goal using `related_goal_id`
    - Validates goal ownership before creating entry
    - Automatically calculates duration from time range
    - Defaults to current date if `work_date` is not provided
    - Supports overnight time entries (end_time before start_time)
    
    **Authentication**: Required (Bearer token)
    """
    try:
        if entry_data.related_goal_id:
            goal_valid = await validate_goal_ownership(entry_data.related_goal_id, credentials.credentials)
            if not goal_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Goal {entry_data.related_goal_id} not found or does not belong to you"
                )
        
        minutes = entry_data.minutes
        if entry_data.start_time and entry_data.end_time:
            start = datetime.combine(datetime.today(), entry_data.start_time)
            end = datetime.combine(datetime.today(), entry_data.end_time)
            if end < start:
                end = end.replace(day=end.day + 1)
            delta = end - start
            minutes = Decimal(delta.total_seconds() / 60)
        
        work_date = entry_data.work_date or datetime.now(timezone.utc).date()
        
        entry = TimeEntry(
            owner_user_id=current_user, 
            related_goal_id=entry_data.related_goal_id,
            work_date=work_date,
            start_time=entry_data.start_time,
            end_time=entry_data.end_time,
            minutes=minutes or Decimal(0),
            description=entry_data.description
        )
        
        db.add(entry)
        db.commit()
        db.refresh(entry)
        
        logger.info(f"Entry created: {entry.entry_id} for user {current_user}")
        return TimeEntryResponse.from_orm(entry)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create entry"
        )

@app.get(
    "/api/entries",
    response_model=TimeEntryListResponse,
    tags=["Time Entries"],
    summary="List Time Entries",
    response_description="List of time entries with pagination",
    responses={
        200: {
            "description": "Successfully retrieved time entries",
            "content": {
                "application/json": {
                    "example": {
                        "entries": [
                            {
                                "entry_id": "123e4567-e89b-12d3-a456-426614174000",
                                "work_date": "2026-01-12",
                                "minutes": 180,
                                "description": "Morning session"
                            }
                        ],
                        "total": 45,
                        "page": 1,
                        "page_size": 10
                    }
                }
            }
        },
        400: {"description": "Invalid parameters"},
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def list_entries(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of entries per page (1-100)"),
    goal_id: Optional[str] = Query(None, description="Filter entries by goal ID (UUID)"),
    sort_by: str = Query(
        "work_date",
        pattern="^(minutes|work_date|start_time|end_time|created_at|updated_at)$",
        description="Field to sort by"
    ),
    sort_order: str = Query(
        "desc",
        pattern="^(asc|desc)$",
        description="Sort order: asc (ascending) or desc (descending)"
    ),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve a paginated list of time entries for the authenticated user.
    
    **Filtering:**
    - Filter by specific goal using `goal_id` parameter
    - Only returns entries owned by the authenticated user
    
    **Sorting Options:**
    - `work_date`: Date when work was performed (default)
    - `start_time`: Start time of the entry
    - `end_time`: End time of the entry
    - `minutes`: Duration of the entry
    - `created_at`: Entry creation timestamp
    - `updated_at`: Entry last update timestamp
    
    **Sort Order:**
    - `asc`: Ascending order (oldest/smallest first)
    - `desc`: Descending order (newest/largest first, default)
    
    **Pagination:**
    - Use `page` and `page_size` to navigate through results
    - Response includes total count for pagination UI
    
    **Authentication**: Required (Bearer token)
    """
    try:
        query = db.query(TimeEntry).filter(TimeEntry.owner_user_id == current_user)
        
        if goal_id:
            try:
                goal_uuid = UUID(goal_id)
                query = query.filter(TimeEntry.related_goal_id == goal_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid goal_id format"
                )
        
        sort_column = getattr(TimeEntry, sort_by)
        if sort_order == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        total = query.count()
        entries = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "entries": [TimeEntryResponse.from_orm(entry) for entry in entries],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve entries"
        )

@app.get(
    "/api/entries/{entry_id}",
    response_model=TimeEntryResponse,
    tags=["Time Entries"],
    summary="Get Time Entry by ID",
    responses={
        200: {"description": "Time entry retrieved successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Time entry not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve a specific time entry by its unique ID.
    
    Returns detailed information about a single time entry including:
    - Work date and time range
    - Duration in minutes
    - Associated goal (if any)
    - Description
    - Creation and update timestamps
    
    **Authorization**: Users can only access their own time entries.
    
    **Authentication**: Required (Bearer token)
    """
    entry = db.query(TimeEntry).filter(
        TimeEntry.entry_id == entry_id,
        TimeEntry.owner_user_id == current_user
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    return TimeEntryResponse.from_orm(entry)

@app.put(
    "/api/entries/{entry_id}",
    response_model=TimeEntryResponse,
    tags=["Time Entries"],
    summary="Update Time Entry",
    responses={
        200: {"description": "Time entry updated successfully"},
        400: {"description": "Invalid data or goal validation failed"},
        401: {"description": "Unauthorized"},
        404: {"description": "Time entry not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_entry(
    entry_id: UUID,
    entry_data: TimeEntryUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing time entry.
    
    **Partial Updates**: All fields are optional. Only provided fields will be updated.
    
    **Time Calculation**:
    - If `start_time` or `end_time` is updated, duration is automatically recalculated
    - Manual `minutes` value overrides automatic calculation if times are not provided
    
    **Goal Association**:
    - Validates new goal ownership before updating
    - Can remove goal association by setting `related_goal_id` to null
    
    **Authorization**: Users can only update their own time entries.
    
    **Authentication**: Required (Bearer token)
    """
    entry = db.query(TimeEntry).filter(
        TimeEntry.entry_id == entry_id,
        TimeEntry.owner_user_id == current_user
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    try:
        if entry_data.related_goal_id is not None:
            if entry_data.related_goal_id:
                goal_valid = await validate_goal_ownership(entry_data.related_goal_id, "Bearer token_placeholder")
                if not goal_valid:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Goal {entry_data.related_goal_id} not found or does not belong to you"
                    )
            entry.related_goal_id = entry_data.related_goal_id
        
        if entry_data.start_time is not None:
            entry.start_time = entry_data.start_time
        if entry_data.end_time is not None:
            entry.end_time = entry_data.end_time
        
        if entry_data.start_time or entry_data.end_time:
            start = entry.start_time or entry_data.start_time
            end = entry.end_time or entry_data.end_time
            if start and end:
                start_dt = datetime.combine(datetime.today(), start)
                end_dt = datetime.combine(datetime.today(), end)
                if end_dt < start_dt:
                    end_dt = end_dt.replace(day=end_dt.day + 1)
                delta = end_dt - start_dt
                entry.minutes = Decimal(delta.total_seconds() / 60)
        elif entry_data.minutes is not None:
            entry.minutes = entry_data.minutes
        
        if entry_data.description is not None:
            entry.description = entry_data.description
        
        entry.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(entry)
        
        logger.info(f"Entry updated: {entry_id}")
        return TimeEntryResponse.from_orm(entry)
    
    except HTTPException:
        raise
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update entry"
        )

@app.delete(
    "/api/entries/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Time Entries"],
    summary="Delete Time Entry",
    responses={
        204: {"description": "Time entry deleted successfully (no content)"},
        401: {"description": "Unauthorized"},
        404: {"description": "Time entry not found"},
        500: {"description": "Internal server error"}
    }
)
async def delete_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Permanently delete a time entry.
    
    **Warning**: This action is irreversible. The time entry will be permanently removed.
    
    **Authorization**: Users can only delete their own time entries.
    
    **Authentication**: Required (Bearer token)
    """
    entry = db.query(TimeEntry).filter(
        TimeEntry.entry_id == entry_id,
        TimeEntry.owner_user_id == current_user
    ).first()
    
    if not entry:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Entry not found"
        )
    
    try:
        db.delete(entry)
        db.commit()
        logger.info(f"Entry deleted: {entry_id}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete entry"
        )

# =====================================================
# TIME STATISTICS ENDPOINTS
# =====================================================

@app.get(
    "/api/entries/goal/{goal_id}/total",
    tags=["Statistics"],
    summary="Get Goal Total Hours",
    response_description="Total hours and minutes for the goal",
    responses={
        200: {
            "description": "Goal totals calculated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "total_minutes": 7200,
                        "total_hours": 120.0
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def get_goal_total_hours(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Calculate total time logged for a specific goal.
    
    Returns aggregated time data including:
    - Total minutes logged
    - Total hours (minutes / 60)
    
    **Use Case**: Primary endpoint used by Goals Service to calculate progress percentages.
    
    **Authorization**: Only returns data for goals owned by the authenticated user.
    
    **Authentication**: Required (Bearer token)
    """
    try:
        result = db.query(
            func.sum(TimeEntry.minutes).label("total_minutes")
        ).filter(
            TimeEntry.owner_user_id == current_user,
            TimeEntry.related_goal_id == goal_id
        ).first()
        
        total_minutes = result[0] or Decimal(0)
        total_hours = total_minutes / Decimal(60)
        
        return {
            "goal_id": goal_id,
            "total_minutes": float(total_minutes),
            "total_hours": float(total_hours)
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve goal total"
        )

@app.get(
    "/api/entries/goal/{goal_id}/count",
    tags=["Statistics"],
    summary="Get Goal Entry Count",
    response_description="Number of time entries for the goal",
    responses={
        200: {
            "description": "Entry count retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "count": 42
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def get_goal_entries_count(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get the total count of time entries associated with a specific goal.
    
    **Use Case**: Used by Goals Service and analytics to show activity level.
    
    **Authorization**: Only counts entries for goals owned by the authenticated user.
    
    **Authentication**: Required (Bearer token)
    """
    try:
        count = db.query(TimeEntry).filter(
            TimeEntry.owner_user_id == current_user,
            TimeEntry.related_goal_id == goal_id
        ).count()
        
        return {
            "goal_id": goal_id,
            "count": count
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve entry count"
        )

@app.get(
    "/api/entries/summary",
    response_model=UserTimeStatsResponse,
    tags=["Statistics"],
    summary="Get User Time Statistics",
    response_description="Comprehensive time tracking statistics",
    responses={
        200: {
            "description": "Statistics calculated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "google_12345",
                        "total_minutes": 14400,
                        "total_hours": 240.0,
                        "total_entries": 156,
                        "by_goal": [
                            {
                                "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                                "total_minutes": 7200,
                                "total_hours": 120.0,
                                "entry_count": 78
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
async def get_user_time_stats(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get comprehensive time tracking statistics for the authenticated user.
    
    Returns aggregated data including:
    - **Total Time**: Sum of all time entries across all goals
    - **Total Entries**: Count of all time entries
    - **By Goal Breakdown**: Time and entry counts for each goal
    
    **Use Cases**:
    - Dashboard overview
    - User profile statistics
    - PDF report generation
    - Analytics and insights
    
    **Note**: Only includes entries associated with goals in the breakdown.
    Standalone entries are included in totals but not in goal breakdown.
    
    **Authentication**: Required (Bearer token)
    """
    try:
        total_result = db.query(
            func.sum(TimeEntry.minutes).label("total_minutes"),
            func.count(TimeEntry.entry_id).label("count")
        ).filter(
            TimeEntry.owner_user_id == current_user
        ).first()
        
        total_minutes = total_result[0] or Decimal(0)
        total_entries = total_result[1] or 0
        total_hours = total_minutes / Decimal(60)
        
        goal_stats = db.query(
            TimeEntry.related_goal_id,
            func.sum(TimeEntry.minutes).label("goal_minutes"),
            func.count(TimeEntry.entry_id).label("goal_count")
        ).filter(
            TimeEntry.owner_user_id == current_user,
            TimeEntry.related_goal_id.isnot(None)
        ).group_by(TimeEntry.related_goal_id).all()
        
        by_goal = []
        for goal_id, minutes, count in goal_stats:
            goal_minutes = minutes or Decimal(0)
            goal_hours = goal_minutes / Decimal(60)
            by_goal.append({
                "goal_id": goal_id,
                "total_minutes": float(goal_minutes),
                "total_hours": float(goal_hours),
                "entry_count": count or 0
            })
        
        return {
            "user_id": current_user,
            "total_minutes": float(total_minutes),
            "total_hours": float(total_hours),
            "total_entries": total_entries,
            "by_goal": by_goal
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
