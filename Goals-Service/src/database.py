"""Database configuration and models for Goals Service"""

from sqlalchemy import create_engine, Column, String, Text, DateTime, Numeric, Date, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Goal(Base):
    __tablename__ = "goals"

    goal_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(Text, nullable=False, index=True)  
    title = Column(Text, nullable=False)
    target_hours = Column(Numeric, nullable=True)  
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)
    hourly_rate = Column(Numeric, nullable=True)  
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_goals_owner', 'owner_user_id'),
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
