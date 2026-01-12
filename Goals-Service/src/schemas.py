"""Pydantic schemas for Goals Service"""

from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import UUID
from typing import Optional
from decimal import Decimal

class GoalCreate(BaseModel):
    """Schema for creating a new goal"""
    title: str = Field(..., min_length=1, max_length=500)
    target_hours: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

class GoalUpdate(BaseModel):
    """Schema for updating a goal"""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    target_hours: Optional[Decimal] = Field(None, ge=0)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    hourly_rate: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

class GoalResponse(BaseModel):
    """Schema for goal response"""
    goal_id: UUID
    owner_user_id: str  
    title: str
    target_hours: Optional[Decimal]
    start_date: Optional[date]
    end_date: Optional[date]
    hourly_rate: Optional[Decimal]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class GoalListResponse(BaseModel):
    """Schema for goal list response"""
    goals: list[GoalResponse]
    total: int
    page: int
    page_size: int

class GoalStatsResponse(BaseModel):
    """Schema for goal statistics"""
    goal_id: UUID
    total_hours: Optional[Decimal]
    remaining_hours: Optional[Decimal]
    target_hours: Optional[Decimal]
    progress_percentage: Optional[float]
    entries_count: int
    owner_user_id: Optional[str] = None 

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    service: str = "Goals Service"
    version: str = "0.1.0"
