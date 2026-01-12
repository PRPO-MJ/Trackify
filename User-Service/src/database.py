"""Database configuration and models"""

from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    google_sub = Column(Text, primary_key=True) 
    google_email = Column(Text, nullable=False)  
    full_name = Column(Text, nullable=False)  
    address = Column(Text, nullable=True)
    country = Column(Text, nullable=True)
    phone = Column(Text, nullable=True)
    currency = Column(Text, nullable=True)  
    timezone = Column(Text, nullable=True)  
    created_at = Column(DateTime(timezone=True), nullable=False, server_default="now()")
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default="now()", onupdate=datetime.now)

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

