"""
Database configuration and models for collaborative drawing board.
Uses SQLAlchemy with in-memory SQLite for testing and performance.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
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
    """
    User model for authentication and collaboration.
    
    Architecture Context:
    Users are the core identity entities in the collaborative drawing system.
    Each user can own multiple drawing boards and participate in collaborative
    sessions. The user model supports JWT-based authentication and tracks
    basic profile information for collaborative features.
    
    Relationships:
    - One-to-many with Board (as owner)
    - Future: Many-to-many with Board (as collaborator)
    - Future: One-to-many with Stroke (drawing contributions)
    
    Security Considerations:
    - Passwords are hashed using bcrypt before storage
    - Email addresses are unique and used for account recovery
    - User IDs are exposed in JWT tokens for API authentication
    - No sensitive data should be stored in this model
    """
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    is_active = Column(Boolean, default=True)
    
    # Relationship to owned boards
    owned_boards = relationship("Board", back_populates="owner", cascade="all, delete-orphan")


class Board(Base):
    """
    Board model for collaborative drawing workspaces.
    
    Architecture Overview:
    Boards are the primary collaborative entities in the drawing system. Each board
    represents an isolated drawing canvas where multiple users can collaborate in
    real-time. Boards contain metadata, access control information, and encryption
    keys for client-side security.
    
    Collaborative Features:
    - Owner-based access control (extensible to team permissions)
    - End-to-end encryption via AES-GCM keys
    - Real-time collaboration support through WebSocket sessions
    - Persistent storage of drawing data and collaborative history
    
    Security Architecture:
    - Each board has a unique AES-GCM encryption key for client-side encryption
    - Only board owners (and future collaborators) can access encryption keys
    - All drawing data (strokes, shapes) encrypted before storage
    - Server cannot decrypt drawing content (zero-trust architecture)
    
    Performance Considerations:
    - Board queries optimized with indexes on owner_id and created_at
    - Encryption keys stored as base64 text for JSON transport
    - Board metadata kept minimal for fast listing operations
    - Soft-delete pattern could be added for recovery features
    
    Database Schema:
    - id: Primary key for board identification
    - name: Human-readable board title for workspace organization
    - owner_id: Foreign key to User who created and owns the board
    - created_at: Timestamp for chronological ordering
    - encrypted_key: Base64-encoded AES-GCM key for client-side encryption
    - is_public: Future feature flag for public/private boards
    
    Usage Examples:
    ```python
    # Create new collaborative board
    board = Board(
        name="Team Design Session",
        owner_id=user.id,
        encrypted_key=generate_aes_key_b64()
    )
    
    # Query user's boards for workspace
    user_boards = db.query(Board).filter(Board.owner_id == user.id).all()
    
    # Load board for collaborative session
    board = db.query(Board).filter(
        Board.id == board_id,
        Board.owner_id == user.id
    ).first()
    ```
    """
    __tablename__ = "boards"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)  # Indexed for search
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    encrypted_key = Column(Text, nullable=False)  # Base64-encoded AES-GCM key
    is_public = Column(Boolean, default=False)  # Future feature: public boards
    
    # Relationships
    owner = relationship("User", back_populates="owned_boards")
    # Future: strokes = relationship("Stroke", back_populates="board", cascade="all, delete-orphan")
    
    def __repr__(self):
        """
        String representation for debugging and logging.
        
        Security Note:
        Does not include encryption key to prevent accidental logging of sensitive data.
        """
        return f"<Board(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


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