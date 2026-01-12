"""Pydantic schemas for Mailer Service"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from uuid import UUID
from typing import Optional
import re

class EmailSettingsCreate(BaseModel):
    """Schema for creating/updating email settings for a goal"""
    goal_id: UUID
    recipient_email: str  
    enabled: bool = False
    send_day: int = Field(default=1, ge=1, le=31)
    
    @field_validator('recipient_email')
    @classmethod
    def validate_emails(cls, v: str) -> str:
        """Validate comma-separated email addresses"""
        if not v or not v.strip():
            raise ValueError('At least one email address is required')
        
        emails = [email.strip() for email in v.split(',')]
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in emails:
            if not email:
                continue
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email address: {email}')
        
        return ', '.join(emails)

class EmailSettingsUpdate(BaseModel):
    """Schema for updating email settings"""
    recipient_email: Optional[str] = None  
    enabled: Optional[bool] = None
    send_day: Optional[int] = Field(None, ge=1, le=31)
    
    @field_validator('recipient_email')
    @classmethod
    def validate_emails(cls, v: Optional[str]) -> Optional[str]:
        """Validate comma-separated email addresses"""
        if v is None:
            return v
        if not v.strip():
            raise ValueError('At least one email address is required')
        
        emails = [email.strip() for email in v.split(',')]
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in emails:
            if not email:
                continue
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email address: {email}')
        
        return ', '.join(emails)

class EmailSettingsResponse(BaseModel):
    """Schema for email settings response"""
    mail_id: UUID
    goal_id: Optional[UUID] = Field(alias='related_goal_id')  
    owner_user_id: str
    recipient_email: str = Field(alias='recipient')  
    enabled: bool
    send_day: Optional[int] = Field(alias='sent_when')  
    last_sent_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        populate_by_name = True  

class SendNowRequest(BaseModel):
    """Schema for sending email now"""
    goal_id: UUID

class MailCreate(BaseModel):
    """Schema for creating a new mail"""
    recipient: str  
    subject: str = Field(..., min_length=1, max_length=500)
    body: str = Field(..., min_length=1)
    related_goal_id: Optional[UUID] = None
    include_pdf: bool = False  
    pdf_goal_id: Optional[UUID] = None  
    
    @field_validator('recipient')
    @classmethod
    def validate_emails(cls, v: str) -> str:
        """Validate comma-separated email addresses"""
        if not v or not v.strip():
            raise ValueError('At least one email address is required')
        
        emails = [email.strip() for email in v.split(',')]
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in emails:
            if not email:
                continue
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email address: {email}')
        
        return ', '.join(emails)

class MailUpdate(BaseModel):
    """Schema for updating mail"""
    recipient: Optional[str] = None  
    subject: Optional[str] = None
    body: Optional[str] = None
    sent_when: Optional[float] = None
    
    @field_validator('recipient')
    @classmethod
    def validate_emails(cls, v: Optional[str]) -> Optional[str]:
        """Validate comma-separated email addresses"""
        if v is None:
            return v
        if not v.strip():
            raise ValueError('At least one email address is required')
        
        emails = [email.strip() for email in v.split(',')]
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        
        for email in emails:
            if not email:
                continue
            if not re.match(email_regex, email):
                raise ValueError(f'Invalid email address: {email}')
        
        return ', '.join(emails)

class MailResponse(BaseModel):
    """Schema for mail response"""
    mail_id: UUID
    owner_user_id: str  
    related_goal_id: Optional[UUID]
    recipient: str
    subject: str
    body: str
    pdf_url: Optional[str]
    status: str
    sent_when: Optional[float]
    created_at: datetime
    sent_at: Optional[datetime]
    updated_at: datetime

    class Config:
        from_attributes = True

class MailListResponse(BaseModel):
    """Schema for mail list response"""
    mails: list[MailResponse]
    total: int
    page: int
    page_size: int

class SendMailRequest(BaseModel):
    """Schema for sending mail request"""
    mail_id: UUID

class SendMailResponse(BaseModel):
    """Schema for send mail response"""
    mail_id: UUID
    status: str
    message: str
    sent_at: Optional[datetime]

class HealthResponse(BaseModel):
    """Schema for health check response"""
    status: str
    service: str = "Mailer Service"
    version: str = "0.1.0"
