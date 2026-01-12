"""Database configuration for PDF Service"""

from sqlalchemy import create_engine, Column, String, DateTime, LargeBinary, Index
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import uuid
from config import DATABASE_URL

if DATABASE_URL:
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
else:
    engine = None
    SessionLocal = None

Base = declarative_base()

class PDFDocument(Base):
    """Store generated PDFs for caching"""
    __tablename__ = "pdf_documents"

    pdf_id = Column(PG_UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    owner_user_id = Column(PG_UUID(as_uuid=True), nullable=False, index=True)
    related_goal_id = Column(PG_UUID(as_uuid=True), nullable=True, index=True)
    document_type = Column(String(50), nullable=False)  
    file_path = Column(String(500), nullable=True)
    file_size = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        Index('idx_pdf_owner', 'owner_user_id'),
        Index('idx_pdf_goal', 'related_goal_id'),
        Index('idx_pdf_type', 'document_type'),
    )

def get_db():
    """Database dependency for FastAPI"""
    if SessionLocal is None:
        return None
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables"""
    if engine is not None:
        Base.metadata.create_all(bind=engine)
