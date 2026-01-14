"""
User Management Microservice
A FastAPI based user management service with Google OAuth and JWT authentication
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone
import traceback

from config import (
    CORS_ORIGINS,
    CORS_CREDENTIALS,
    CORS_METHODS,
    CORS_HEADERS,
    HOST,
    PORT,
    DEBUG
)

from database import init_db, get_db, User

from auth import (
    create_access_token,
    verify_token,
    verify_google_token,
    exchange_code_for_token,
    get_current_user
)

from schemas import (
    UserCreate,
    UserUpdate,
    UserResponse,
    TokenResponse,
    GoogleAuthRequest,
    GoogleCallbackRequest,
    TokenVerifyResponse,
    HealthResponse,
    DeleteResponse
)

init_db()

app = FastAPI(
    title="User Management Service",
    description="""User management microservice for Trackify with Google OAuth integration.
    
    This service provides comprehensive user management functionality including:
    - Google OAuth 2.0 authentication (ID token and authorization code flows)
    - JWT token generation and verification
    - User profile management
    - User settings (timezone, currency, contact info)
    - PostgreSQL database integration
    
    **Authentication Flows**:
    - **Direct ID Token**: Frontend sends Google ID token directly
    - **Authorization Code**: Traditional OAuth redirect flow
    
    **User Features**:
    - Automatic user creation on first login
    - Profile updates (name, address, timezone, etc.)
    - Account deletion
    - JWT-based session management
    
    **Security**:
    - Google token verification
    - JWT token authentication for all protected endpoints
    - CORS configuration for cross-origin requests
    
    All user endpoints (except auth) require JWT authentication via Bearer token.
    """,
    version="1.0.0",
    docs_url="/api/users/docs",
    redoc_url="/api/users/redoc",
    openapi_url="/api/users/openapi.json",
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
    expose_headers=["*"],
    max_age=600,
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all unhandled exceptions and ensure CORS headers are present"""
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": request.headers.get("origin", "*"),
            "Access-Control-Allow-Credentials": "true",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS, PATCH",
            "Access-Control-Allow-Headers": "*",
        }
    )

# ============================================================================
# HEALTH CHECK ENDPOINTS
# ============================================================================

@app.get("/api/users/health/liveness", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """
    Liveness health check. Confirms the service process is running.
    """
    return HealthResponse(status="healthy")

@app.get("/api/users/health/readiness")
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

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.options("/api/auth/google")
async def options_google_auth():
    """Handle CORS preflight for Google auth endpoint"""
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Credentials": "true",
        }
    )

@app.post(
    "/api/auth/google",
    response_model=TokenResponse,
    tags=["Authentication"],
    summary="Login/Register with Google ID Token",
    response_description="JWT token and user profile",
    responses={
        200: {
            "description": "Existing user logged in successfully",
            "content": {
                "application/json": {
                    "example": {
                        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                        "token_type": "bearer",
                        "user": {
                            "google_sub": "google_12345",
                            "google_email": "user@example.com",
                            "full_name": "John Doe",
                            "currency": "USD",
                            "timezone": "UTC"
                        }
                    }
                }
            }
        },
        201: {
            "description": "New user registered successfully",
        },
        400: {"description": "Email not found in Google token"},
        401: {"description": "Invalid Google token"}
    }
)
async def google_auth(request: GoogleAuthRequest, db: Session = Depends(get_db)):
    """
    Authenticate with Google ID token (client-side flow).
    
    **Authentication Flow**:
    1. Frontend uses Google Sign-In to get ID token
    2. Frontend sends ID token to this endpoint
    3. Backend verifies token with Google
    4. User created (if new) or retrieved (if existing)
    5. JWT token generated and returned
    
    **Request Body**:
    - `token`: Google ID token from frontend Google Sign-In
    
    **Response**:
    - `access_token`: JWT token for API authentication
    - `token_type`: Always "bearer"
    - `user`: Complete user profile
    
    **Status Codes**:
    - `200`: Existing user logged in
    - `201`: New user registered
    
    **Use Cases**:
    - Single-page application login
    - Mobile app authentication
    - Client-side Google Sign-In integration
    
    **No Authentication Required**: This is the login endpoint.
    """
    try:
        google_info = verify_google_token(request.token)
        email = google_info.get('email')
        google_sub = google_info.get("sub")
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email not found in Google token"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    
    user = db.query(User).filter(User.google_sub == google_sub).first()
    is_new_user = user is None
    
    if is_new_user:
        given_name = google_info.get('given_name', '')
        family_name = google_info.get('family_name', '')
        if not given_name and not family_name:
            full_name = google_info.get('name', email.split('@')[0])
        else:
            full_name = f"{given_name} {family_name}".strip() or email.split('@')[0]
        
        user = User(
            google_sub=google_sub,
            google_email=email,
            full_name=full_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(str(user.google_sub))
    
    response = JSONResponse(
        status_code=status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "google_sub": user.google_sub,
                "google_email": user.google_email,
                "full_name": user.full_name,
                "address": user.address,
                "country": user.country,
                "phone": user.phone,
                "currency": user.currency,
                "timezone": user.timezone,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        domain=".zusidelavi.com",
        httponly=True,
        secure=True,
        samesite="none"
    )
    return response

@app.post(
    "/api/auth/google/callback",
    response_model=TokenResponse,
    tags=["Authentication"],
    summary="Google OAuth Callback (Server-Side Flow)",
    response_description="JWT token and user profile",
    responses={
        200: {
            "description": "Existing user authenticated successfully",
        },
        201: {
            "description": "New user registered successfully",
        },
        400: {"description": "Email or sub not found in Google token"},
        401: {"description": "Invalid authorization code"}
    }
)
async def google_callback(request: GoogleCallbackRequest, db: Session = Depends(get_db)):
    """
    Handle Google OAuth callback (server-side authorization code flow).
    
    **Server-Side Flow**:
    1. Frontend redirects user to Google login page
    2. User logs in with Google
    3. Google redirects back with authorization code
    4. Frontend sends code to this endpoint
    5. Backend exchanges code for tokens with Google
    6. User created/retrieved and JWT token issued
    
    **Request Body**:
    - `code`: Authorization code from Google OAuth redirect
    - `redirect_uri`: Same redirect_uri used in authorization request
    
    **Google Authorization URL Example**:
    ```
    https://accounts.google.com/o/oauth2/v2/auth?
      client_id=YOUR_CLIENT_ID&
      redirect_uri=http://localhost:8080/auth/google/callback&
      response_type=code&
      scope=openid+email+profile
    ```
    
    **Response**: Same as `/api/auth/google` - JWT token and user profile.
    
    **Use Cases**:
    - Traditional web applications
    - Server-side OAuth implementation
    - When client-side flow is not suitable
    
    **No Authentication Required**: This is the OAuth callback endpoint.
    """
    google_info = exchange_code_for_token(request.code, request.redirect_uri)
    email = google_info.get('email')
    google_sub = google_info.get('sub')
    
    if not email or not google_sub:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email or sub not found in Google token"
        )
    
    user = db.query(User).filter(User.google_sub == google_sub).first()
    is_new_user = user is None
    
    if is_new_user:
        given_name = google_info.get('given_name', '')
        family_name = google_info.get('family_name', '')
        if not given_name and not family_name:
            full_name = google_info.get('name', email.split('@')[0])
        else:
            full_name = f"{given_name} {family_name}".strip() or email.split('@')[0]
        
        user = User(
            google_sub=google_sub,
            google_email=email,
            full_name=full_name,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = create_access_token(str(user.google_sub))
    
    response = JSONResponse(
        status_code=status.HTTP_201_CREATED if is_new_user else status.HTTP_200_OK,
        content={
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "google_sub": user.google_sub,
                "google_email": user.google_email,
                "full_name": user.full_name,
                "address": user.address,
                "country": user.country,
                "phone": user.phone,
                "currency": user.currency,
                "timezone": user.timezone,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat()
            }
        }
    )
    response.set_cookie(
        key="access_token",
        value=access_token,
        domain=".zusidelavi.com",
        httponly=True,
        secure=True,
        samesite="none"
    )
    return response

@app.get(
    "/api/auth/verify",
    response_model=TokenVerifyResponse,
    tags=["Authentication"],
    summary="Verify JWT Token",
    response_description="Token validation result",
    responses={
        200: {
            "description": "Token is valid",
            "content": {
                "application/json": {
                    "example": {
                        "user_id": "google_12345",
                        "valid": True
                    }
                }
            }
        },
        401: {"description": "Invalid or expired token"}
    }
)
async def verify_jwt_token(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Verify if a JWT token is valid and not expired.
    
    **Purpose**: Check token validity without making other API calls.
    
    **Response**:
    - `user_id`: Google sub (user identifier)
    - `valid`: Always true if endpoint succeeds (false cases return 401)
    
    **Use Cases**:
    - Check if user is still logged in
    - Validate token before making API calls
    - Session management
    - Token refresh logic
    
    **Authentication**: Required (Bearer token) - the token being verified.
    """
    return TokenVerifyResponse(
        user_id=str(current_user.google_sub),
        valid=True
    )

# ============================================================================
# USER ENDPOINTS
# ============================================================================

@app.get(
    "/api/users/me",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get Current User Profile",
    response_description="Authenticated user's profile",
    responses={
        200: {
            "description": "User profile retrieved successfully",
            "content": {
                "application/json": {
                    "example": {
                        "google_sub": "google_12345",
                        "google_email": "user@example.com",
                        "full_name": "John Doe",
                        "address": "123 Main St, City, Country",
                        "country": "United States",
                        "phone": "+1234567890",
                        "currency": "USD",
                        "timezone": "America/New_York",
                        "created_at": "2026-01-01T00:00:00Z",
                        "updated_at": "2026-01-12T10:00:00Z"
                    }
                }
            }
        },
        401: {"description": "Unauthorized - invalid or missing token"}
    }
)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get the complete profile of the currently authenticated user.
    
    **Profile Information**:
    - `google_sub`: Unique Google identifier
    - `google_email`: Email from Google account
    - `full_name`: User's full name
    - `address`: Physical address (optional)
    - `country`: Country of residence (optional)
    - `phone`: Contact phone number (optional)
    - `currency`: Preferred currency for financial calculations (optional)
    - `timezone`: User's timezone (optional)
    - `created_at`: Account creation timestamp
    - `updated_at`: Last profile update timestamp
    
    **Use Cases**:
    - Display user profile page
    - Show user info in navigation
    - Pre-fill forms with user data
    - User settings display
    
    **Authentication**: Required (Bearer token)
    """
    return UserResponse.model_validate(current_user)

@app.get(
    "/api/users/{user_id}",
    response_model=UserResponse,
    tags=["Users"],
    summary="Get User by ID",
    response_description="User profile by ID",
    responses={
        200: {"description": "User profile retrieved successfully"},
        401: {"description": "Unauthorized - authentication required"},
        404: {"description": "User not found"}
    }
)
async def get_user(
    user_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get any user's profile by their user ID (Google sub).
    
    **Parameters**:
    - `user_id`: Google sub (unique identifier) of the user to retrieve
    
    **Note**: This endpoint requires authentication but allows viewing
    any user's public profile information. In production, you may want
    to restrict this to only allow users to view their own profile.
    
    **Use Cases**:
    - Admin user management
    - User directory/search
    - Collaboration features
    - User lookups
    
    **Authentication**: Required (Bearer token)
    """
    user = db.query(User).filter(User.google_sub == user_id).first()
    
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)

@app.get(
    "/api/users",
    response_model=list[UserResponse],
    tags=["Users"],
    summary="Get All Users (Paginated)",
    response_description="List of users",
    responses={
        200: {
            "description": "List of users retrieved successfully",
            "content": {
                "application/json": {
                    "example": [
                        {
                            "google_sub": "google_12345",
                            "google_email": "user1@example.com",
                            "full_name": "John Doe"
                        },
                        {
                            "google_sub": "google_67890",
                            "google_email": "user2@example.com",
                            "full_name": "Jane Smith"
                        }
                    ]
                }
            }
        },
        401: {"description": "Unauthorized"}
    }
)
async def get_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum records to return (1-100)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a paginated list of all users in the system.
    
    **Pagination**:
    - `skip`: Number of records to skip (default: 0)
    - `limit`: Maximum number of records to return (default: 10, max: 100)
    
    **Example**: `GET /api/users?skip=0&limit=20` returns first 20 users.
    
    **Use Cases**:
    - User administration interfaces
    - User directory/listing
    - Analytics and reporting
    - System monitoring
    
    **Note**: In production, this endpoint should likely be restricted
    to admin users only for privacy and security.
    
    **Authentication**: Required (Bearer token)
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return [UserResponse.model_validate(user) for user in users]

@app.put(
    "/api/users/me",
    response_model=UserResponse,
    tags=["Users"],
    summary="Update Current User Profile",
    response_description="Updated user profile",
    responses={
        200: {
            "description": "User profile updated successfully",
        },
        401: {"description": "Unauthorized"}
    }
)
async def update_user_profile(
    user_update: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update the profile of the currently authenticated user.
    
    **Partial Updates**: All fields are optional. Only provided fields will be updated.
    
    **Updatable Fields**:
    - `full_name`: User's full name
    - `address`: Physical address
    - `country`: Country of residence
    - `phone`: Contact phone number
    - `currency`: Preferred currency (e.g., "USD", "EUR", "GBP")
    - `timezone`: Timezone (e.g., "America/New_York", "Europe/London")
    
    **Immutable Fields** (cannot be changed):
    - `google_sub`: Google identifier
    - `google_email`: Email from Google
    - `created_at`: Account creation date
    
    **Auto-Updated**:
    - `updated_at`: Automatically set to current timestamp
    
    **Use Cases**:
    - User profile settings page
    - Onboarding flow
    - Contact information updates
    - Localization preferences
    
    **Authentication**: Required (Bearer token)
    """
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.address is not None:
        current_user.address = user_update.address
    if user_update.country is not None:
        current_user.country = user_update.country
    if user_update.phone is not None:
        current_user.phone = user_update.phone
    if user_update.currency is not None:
        current_user.currency = user_update.currency
    if user_update.timezone is not None:
        current_user.timezone = user_update.timezone
    
    current_user.updated_at = datetime.now(timezone.utc)
    
    db.commit()
    db.refresh(current_user)
    
    return UserResponse.model_validate(current_user)

@app.delete(
    "/api/users/me",
    response_model=DeleteResponse,
    tags=["Users"],
    summary="Delete Current User Account",
    response_description="Account deletion confirmation",
    responses={
        200: {
            "description": "User account deleted successfully",
            "content": {
                "application/json": {
                    "example": {
                        "message": "User deleted successfully"
                    }
                }
            }
        },
        401: {"description": "Unauthorized"}
    }
)
async def delete_current_user(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete the currently authenticated user account.
    
    **WARNING: This action is irreversible!**
    
    **What Gets Deleted**:
    - User profile and all personal information
    - Account permanently removed from database
    
    **What May Remain** (depending on microservices architecture):
    - Goals, time entries, and other data in separate services
    - Consider implementing cascade deletes across services
    - May want to anonymize rather than delete for data integrity
    
    **Recommendations**:
    - Implement a confirmation dialog in frontend
    - Consider a "soft delete" (mark as deleted) instead
    - Notify user via email before deletion
    - Provide data export before allowing deletion
    
    **Use Cases**:
    - GDPR "right to be forgotten" compliance
    - User-initiated account closure
    - Account cleanup
    
    **Authentication**: Required (Bearer token)
    """
    db.delete(current_user)
    db.commit()
    return DeleteResponse(message="User deleted successfully")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=HOST,
        port=PORT,
        reload=DEBUG
    )
