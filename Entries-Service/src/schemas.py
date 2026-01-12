"""Pydantic schemas for Entries Service"""

from pydantic import BaseModel, Field
from datetime import datetime, time, date
from uuid import UUID
from typing import Optional
from decimal import Decimal

class TimeEntryCreate(BaseModel):
    """Schema for creating a new time entry"""
    related_goal_id: Optional[UUID] = None
    work_date: Optional[date] = None  
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    minutes: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

class TimeEntryUpdate(BaseModel):
    """Schema for updating a time entry"""
    related_goal_id: Optional[UUID] = None
    work_date: Optional[date] = None  
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    minutes: Optional[Decimal] = Field(None, ge=0)
    description: Optional[str] = None

class TimeEntryResponse(BaseModel):
    """Schema for time entry response"""
    entry_id: UUID
    owner_user_id: str  
    related_goal_id: Optional[UUID]
    work_date: Optional[date] 
    start_time: Optional[time]
    end_time: Optional[time]
    minutes: Optional[Decimal]
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class TimeEntryListResponse(BaseModel):
    """Schema for time entry list response"""
    entries: list[TimeEntryResponse]
    total: int
    page: int
    page_size: int

class TimeEntrySummaryResponse(BaseModel):
    """Schema for time entry summary"""
    goal_id: Optional[UUID]
    total_entries: int
    total_minutes: Decimal
    total_hours: Decimal

class GoalTimeStatsResponse(BaseModel):
    """Schema for goal time statistics"""
    goal_id: UUID
    total_minutes: Decimal
    total_hours: Decimal
    entry_count: int

class UserTimeStatsResponse(BaseModel):
    """Schema for user time statistics"""
    user_id: UUID
    total_minutes: Decimal
    total_hours: Decimal
    total_entries: int
    by_goal: list[GoalTimeStatsResponse]

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    service: str = "Entries Service"
    version: str = "0.1.0"
