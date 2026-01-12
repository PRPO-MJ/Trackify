"""Pydantic schemas for PDF Service"""

from pydantic import BaseModel
from datetime import datetime
from uuid import UUID
from typing import Optional

class PDFGenerateRequest(BaseModel):
    """Schema for PDF generation request"""
    goal_id: Optional[UUID] = None
    include_user_data: bool = True
    include_all_goals: bool = True
    include_statistics: bool = True

class PDFResponse(BaseModel):
    """Schema for PDF response"""
    pdf_url: str
    file_size: Optional[str]
    generated_at: datetime
    message: str

class GoalPDFResponse(BaseModel):
    """Schema for goal-specific PDF response"""
    pdf_url: str
    goal_id: UUID
    file_size: Optional[str]
    generated_at: datetime

class UserSummaryPDFResponse(BaseModel):
    """Schema for user summary PDF response"""
    pdf_url: str
    user_id: UUID
    file_size: Optional[str]
    generated_at: datetime
    includes_goals: int

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    service: str = "PDF Service"
    version: str = "0.1.0"
