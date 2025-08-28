"""
Database configuration and models for collaborative drawing board.
Uses SQLAlchemy with in-memory SQLite for testing and performance.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime, timezone
import os

# Use SQLite file for persistence during testing
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test_db.sqlite")

# Performance optimizations for low latency
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
}

if "sqlite" in DATABASE_URL:
    engine_kwargs.update({
        "connect_args": {
            "check_same_thread": False,
            "isolation_level": None  # Autocommit mode for faster writes
        }
    })

engine = create_engine(DATABASE_URL, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    """User model for authentication."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)


def get_db():
    """Dependency to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    """Create database tables."""
    Base.metadata.create_all(bind=engine)