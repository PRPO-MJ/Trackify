"""Database configuration and models for Mailer Service"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Numeric, Index, Boolean
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Mail(Base):
    __tablename__ = "mails"

    mail_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(Text, nullable=False, index=True)
    related_goal_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    recipient = Column(Text, nullable=False)
    subject = Column(Text, nullable=True)
    body = Column(Text, nullable=True)
    pdf_url = Column(Text, nullable=True)
    sent_when = Column(Numeric, nullable=True)  
    enabled = Column(Boolean, default=False, nullable=False)  
    status = Column(String(20), default="pending", nullable=False)  
    error_message = Column(Text, nullable=True)
    last_sent_at = Column(DateTime(timezone=True), nullable=True)  
    sent_at = Column(DateTime(timezone=True), nullable=True)  
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_mails_owner', 'owner_user_id'),
        Index('idx_mails_goal', 'related_goal_id'),
        Index('idx_mails_status', 'status'),
        Index('idx_mails_enabled', 'enabled'),
        Index('idx_mails_sent_when', 'sent_when'),
    )

def get_db():
    """Database dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
