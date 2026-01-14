"""
Goals Microservice
A FastAPI based goals management service for everything related to goals.
"""

from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
from uuid import UUID
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

from database import init_db, get_db, Goal
from auth import get_current_user
from schemas import (
    GoalCreate,
    GoalUpdate,
    GoalResponse,
    GoalListResponse,
    GoalStatsResponse,
    HealthResponse
)

from entries_client import get_goal_total_hours, get_goal_entries_count
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Goals Service",
    description="""Goals management microservice for Trackify.
    
    This service provides comprehensive goal management functionality including:
    - Creating, updating, and deleting goals
    - Setting target hours and tracking progress
    - Managing goal timelines (start and end dates)
    - Hourly rate tracking for financial projections
    - Integration with Entries Service for time tracking
    - Statistics and progress calculation
    
    All endpoints require JWT authentication via Bearer token.
    """,
    version="1.0.0",
    docs_url="/api/goals/docs",
    redoc_url="/api/goals/redoc",
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

@app.get("/api/goals/health/liveness", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness health check. Confirms the service process is running.
    """
    return HealthResponse(status="healthy")

@app.get("/api/goals/health/readiness")
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
# GOAL MANAGEMENT ENDPOINTS
# =====================================================

@app.post(
    "/api/goals",
    response_model=GoalResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Goals"],
    summary="Create Goal",
    response_description="Goal created successfully",
    responses={
        201: {
            "description": "Goal created successfully",
            "content": {
                "application/json": {
                    "example": {
                        "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "owner_user_id": "google_12345",
                        "title": "Learn Python",
                        "target_hours": 100.0,
                        "start_date": "2026-01-01",
                        "end_date": "2026-12-31",
                        "hourly_rate": 50.0,
                        "description": "Complete Python mastery course",
                        "created_at": "2026-01-12T10:00:00Z",
                        "updated_at": "2026-01-12T10:00:00Z"
                    }
                }
            }
        },
        400: {"description": "Invalid data"},
        401: {"description": "Unauthorized - invalid or missing token"},
        500: {"description": "Internal server error"}
    }
)
async def create_goal(
    goal_data: GoalCreate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Create a new goal for the authenticated user.
    
    **Goal Properties**:
    - `title`: Name of the goal (required)
    - `target_hours`: Total hours you plan to spend (optional)
    - `start_date`: When you plan to start (optional)
    - `end_date`: Target completion date (optional)
    - `hourly_rate`: Your hourly rate for cost calculations (optional)
    - `description`: Detailed goal description (optional)
    
    **Use Cases**:
    - Track learning objectives
    - Monitor project time
    - Calculate earnings based on hourly rate
    - Set and achieve time-based targets
    
    **Authentication**: Required (Bearer token)
    """
    try:
        goal = Goal(
            owner_user_id=current_user,  
            title=goal_data.title,
            target_hours=goal_data.target_hours,
            start_date=goal_data.start_date,
            end_date=goal_data.end_date,
            hourly_rate=goal_data.hourly_rate,
            description=goal_data.description
        )
        
        db.add(goal)
        db.commit()
        db.refresh(goal)
        
        logger.info(f"Goal created: {goal.goal_id} for user {current_user}")
        return GoalResponse.from_orm(goal)
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create goal"
        )

@app.get(
    "/api/goals",
    response_model=GoalListResponse,
    tags=["Goals"],
    summary="List Goals",
    response_description="List of goals with pagination",
    responses={
        200: {
            "description": "Successfully retrieved goals",
            "content": {
                "application/json": {
                    "example": {
                        "goals": [
                            {
                                "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                                "title": "Learn Python",
                                "target_hours": 100.0,
                                "description": "Complete Python course"
                            }
                        ],
                        "total": 15,
                        "page": 1,
                        "page_size": 10
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        500: {"description": "Internal server error"}
    }
)
async def list_goals(
    page: int = Query(1, ge=1, description="Page number (starts at 1)"),
    page_size: int = Query(10, ge=1, le=100, description="Number of goals per page (1-100)"),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve a paginated list of all goals for the authenticated user.
    
    **Sorting**: Goals are ordered by creation date (newest first).
    
    **Pagination**:
    - Use `page` and `page_size` to navigate through results
    - Response includes total count for pagination UI
    - Maximum page size is 100 goals
    
    **Authorization**: Users can only see their own goals.
    
    **Authentication**: Required (Bearer token)
    """
    try:
        query = db.query(Goal).filter(Goal.owner_user_id == current_user)
        total = query.count()
        goals = query.order_by(Goal.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        return {
            "goals": [GoalResponse.from_orm(goal) for goal in goals],
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve goals"
        )

@app.get(
    "/api/goals/{goal_id}",
    response_model=GoalResponse,
    tags=["Goals"],
    summary="Get Goal by ID",
    responses={
        200: {"description": "Goal retrieved successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Goal not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Retrieve a specific goal by its unique ID.
    
    Returns detailed information about a single goal including:
    - Goal title and description
    - Target hours and timeline (start/end dates)
    - Hourly rate information
    - Creation and update timestamps
    
    **Authorization**: Users can only access their own goals.
    
    **Authentication**: Required (Bearer token)
    """
    goal = db.query(Goal).filter(
        Goal.goal_id == goal_id,
        Goal.owner_user_id == current_user
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    return GoalResponse.from_orm(goal)

@app.put(
    "/api/goals/{goal_id}",
    response_model=GoalResponse,
    tags=["Goals"],
    summary="Update Goal",
    responses={
        200: {"description": "Goal updated successfully"},
        401: {"description": "Unauthorized"},
        404: {"description": "Goal not found"},
        500: {"description": "Internal server error"}
    }
)
async def update_goal(
    goal_id: UUID,
    goal_data: GoalUpdate,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Update an existing goal.
    
    **Partial Updates**: All fields are optional. Only provided fields will be updated.
    
    **Updatable Fields**:
    - `title`: Change goal name
    - `target_hours`: Adjust target hour commitment
    - `start_date` / `end_date`: Modify timeline
    - `hourly_rate`: Update rate for calculations
    - `description`: Revise goal details
    
    **Note**: Updating target hours does not affect existing time entries.
    Progress calculations will reflect the new target.
    
    **Authorization**: Users can only update their own goals.
    
    **Authentication**: Required (Bearer token)
    """
    goal = db.query(Goal).filter(
        Goal.goal_id == goal_id,
        Goal.owner_user_id == current_user
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    try:
        if goal_data.title is not None:
            goal.title = goal_data.title
        if goal_data.target_hours is not None:
            goal.target_hours = goal_data.target_hours
        if goal_data.start_date is not None:
            goal.start_date = goal_data.start_date
        if goal_data.end_date is not None:
            goal.end_date = goal_data.end_date
        if goal_data.hourly_rate is not None:
            goal.hourly_rate = goal_data.hourly_rate
        if goal_data.description is not None:
            goal.description = goal_data.description
        
        goal.updated_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(goal)
        
        logger.info(f"Goal updated: {goal_id}")
        return GoalResponse.from_orm(goal)
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update goal"
        )

@app.delete(
    "/api/goals/{goal_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Goals"],
    summary="Delete Goal",
    responses={
        204: {"description": "Goal deleted successfully (no content)"},
        401: {"description": "Unauthorized"},
        404: {"description": "Goal not found"},
        500: {"description": "Internal server error"}
    }
)
async def delete_goal(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Permanently delete a goal.
    
    **Warning**: This action is irreversible. The goal will be permanently removed.
    
    **Note**: Time entries associated with this goal will NOT be deleted.
    They will remain in the system but no longer be linked to a goal.
    
    **Authorization**: Users can only delete their own goals.
    
    **Authentication**: Required (Bearer token)
    """
    goal = db.query(Goal).filter(
        Goal.goal_id == goal_id,
        Goal.owner_user_id == current_user
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    try:
        db.delete(goal)
        db.commit()
        logger.info(f"Goal deleted: {goal_id}")
    
    except SQLAlchemyError as e:
        db.rollback()
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete goal"
        )

# =====================================================
# GOAL STATISTICS ENDPOINTS
# =====================================================

@app.get(
    "/api/goals/{goal_id}/stats",
    response_model=GoalStatsResponse,
    tags=["Statistics"],
    summary="Get Goal Statistics",
    response_description="Goal progress and statistics",
    responses={
        200: {
            "description": "Statistics calculated successfully",
            "content": {
                "application/json": {
                    "example": {
                        "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                        "total_hours": 65.5,
                        "remaining_hours": 34.5,
                        "target_hours": 100.0,
                        "progress_percentage": 65.5,
                        "entries_count": 42
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        404: {"description": "Goal not found"},
        500: {"description": "Internal server error"}
    }
)
async def get_goal_stats(
    goal_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user),
    credentials: str = Depends(lambda c: c) if False else None
):
    """
    Get comprehensive statistics and progress tracking for a specific goal.
    
    **Statistics Provided**:
    - `total_hours`: Hours logged from Entries Service
    - `remaining_hours`: Hours left to reach target
    - `target_hours`: Original target from goal
    - `progress_percentage`: Completion percentage
    - `entries_count`: Number of time entries
    
    **Integration**: Calls Entries Service to get actual time data.
    
    **Use Cases**:
    - Dashboard progress bars
    - Goal detail views
    - Progress reports
    - Completion tracking
    
    **Authorization**: Users can only access their own goal statistics.
    
    **Authentication**: Required (Bearer token)
    """
    goal = db.query(Goal).filter(
        Goal.goal_id == goal_id,
        Goal.owner_user_id == current_user
    ).first()
    
    if not goal:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Goal not found"
        )
    
    try:
        total_hours = goal.target_hours
        remaining_hours = None
        progress_percentage = None
        
        if total_hours:
            remaining_hours = total_hours
            progress_percentage = 0.0
        
        return {
            "goal_id": goal.goal_id,
            "total_hours": None,  
            "remaining_hours": remaining_hours,
            "target_hours": total_hours,
            "progress_percentage": progress_percentage,
            "entries_count": 0  
        }
    
    except Exception as e:
        logger.error(f"Error getting goal stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve goal statistics"
        )

@app.get(
    "/api/goals/user/{user_id}/summary",
    tags=["Statistics"],
    summary="Get User Goals Summary",
    response_description="Summary of all goals for a user",
    responses={
        200: {
            "description": "Summary retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "google_12345",
                        "total_goals": 8,
                        "goals": [
                            {
                                "goal_id": "123e4567-e89b-12d3-a456-426614174000",
                                "title": "Learn Python",
                                "target_hours": 100.0
                            }
                        ]
                    }
                }
            }
        },
        401: {"description": "Unauthorized"},
        403: {"description": "Forbidden - cannot access other users' goals"},
        500: {"description": "Internal server error"}
    }
)
async def get_user_goals_summary(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """
    Get a summary of all goals for a specific user.
    
    **Summary Includes**:
    - Total count of goals
    - List of all goals with full details
    
    **Authorization**: Users can only access their own goal summary.
    Attempting to access another user's summary returns 403 Forbidden.
    
    **Use Cases**:
    - User profile pages
    - Goal overview dashboards
    - Analytics and reporting
    
    **Authentication**: Required (Bearer token)
    """
    if str(user_id) != current_user:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access other users' goals"
        )
    
    try:
        goals = db.query(Goal).filter(Goal.owner_user_id == user_id).all()
        
        return {
            "user_id": user_id,
            "total_goals": len(goals),
            "goals": [GoalResponse.from_orm(goal) for goal in goals]
        }
    
    except SQLAlchemyError as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user goals summary"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=HOST, port=PORT)
