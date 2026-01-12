"""Pydantic schemas for request/response validation"""

from pydantic import BaseModel, EmailStr, Field
from datetime import datetime
from typing import Optional

class UserCreate(BaseModel):
    """Schema for creating a user"""
    google_email: EmailStr
    full_name: str
    address: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "google_email": "user@gmail.com",
                "full_name": "John Doe",
                "address": "123 Main St",
                "country": "US",
                "phone": "+1234567890",
                "currency": "USD",
                "timezone": "America/New_York"
            }
        }

class UserUpdate(BaseModel):
    """Schema for updating user information"""
    full_name: Optional[str] = None
    address: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    currency: Optional[str] = None
    timezone: Optional[str] = None

    class Config:
        extra = "forbid"  
        json_schema_extra = {
            "example": {
                "full_name": "Jane Smith",
                "address": "456 Oak Ave",
                "country": "UK",
                "phone": "+4401234567",
                "currency": "GBP",
                "timezone": "Europe/London"
            }
        }

class UserResponse(BaseModel):
    """Schema for user response"""
    google_sub: str
    google_email: str
    full_name: str
    address: Optional[str]
    country: Optional[str]
    phone: Optional[str]
    currency: Optional[str]
    timezone: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for authentication token response"""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class GoogleAuthRequest(BaseModel):
    """Schema for Google authentication request"""
    token: str = Field(..., description="Google ID token from frontend")

    class Config:
        json_schema_extra = {
            "example": {
                "token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ..."
            }
        }

class GoogleCallbackRequest(BaseModel):
    """Schema for Google OAuth callback request"""
    code: str = Field(..., description="Authorization code from Google")
    redirect_uri: str = Field(..., description="Redirect URI used in authorization request")

    class Config:
        json_schema_extra = {
            "example": {
                "code": "4/0AY0e-g...",
                "redirect_uri": "http://localhost:8080/api/auth/google/callback"
            }
        }

class TokenVerifyResponse(BaseModel):
    """Schema for token verification response"""
    user_id: str
    valid: bool

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str

class DeleteResponse(BaseModel):
    """Schema for delete response"""
    message: str
