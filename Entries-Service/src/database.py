"""Database configuration and models for Entries Service"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Time, Date, Numeric, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class TimeEntry(Base):
    __tablename__ = "time_entries"

    entry_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(Text, nullable=False, index=True) 
    related_goal_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    work_date = Column(Date, nullable=True)  
    start_time = Column(Time, nullable=True)  
    end_time = Column(Time, nullable=True)  
    minutes = Column(Numeric, nullable=True)  
    description = Column(Text, nullable=True) 
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_time_entries_owner', 'owner_user_id'),
        Index('idx_time_entries_goal', 'related_goal_id'),
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
