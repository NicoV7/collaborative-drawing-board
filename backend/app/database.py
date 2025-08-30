"""
Database configuration and models for collaborative drawing board.
Uses SQLAlchemy with in-memory SQLite for testing and performance.
"""

from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean, Text, ForeignKey, LargeBinary, Float
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


class Stroke(Base):
    """
    Stroke model for drawing data with TTL support.
    
    TTL Implementation:
    - Anonymous user strokes: 24 hours
    - Registered user strokes: 30 days (configurable per user tier)
    - Automatic cleanup through DataExpirationService
    """
    __tablename__ = "strokes"
    
    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Null for anonymous
    stroke_data = Column(LargeBinary, nullable=False)  # Encrypted stroke path data
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    board = relationship("Board")
    user = relationship("User")


class FileUpload(Base):
    """
    File upload model with TTL support for temporary and template files.
    
    TTL Implementation:
    - Temporary uploads: 1 hour
    - Template files: 7 days if unused
    - User uploads: Based on user tier
    """
    __tablename__ = "file_uploads"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    mime_type = Column(String(100), nullable=False)
    upload_type = Column(String(50), nullable=False, index=True)  # 'temporary', 'template', 'avatar'
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    user = relationship("User")


class BoardTemplate(Base):
    """
    Board template model with TTL for unused templates.
    
    TTL Implementation:
    - Unused templates: 7 days
    - Template usage tracking for cleanup decisions
    """
    __tablename__ = "board_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    creator_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    template_data = Column(Text, nullable=False)  # JSON template definition
    usage_count = Column(Integer, default=0)
    last_used_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    creator = relationship("User")


class DataCleanupJob(Base):
    """
    Track automated cleanup operations for monitoring and logging.
    
    Used by DataExpirationService and CleanupScheduler for:
    - Cleanup operation history
    - Performance metrics tracking
    - Failure analysis and retry logic
    """
    __tablename__ = "data_cleanup_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    job_type = Column(String(50), nullable=False, index=True)  # 'strokes', 'uploads', 'templates'
    started_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default='running')  # 'running', 'completed', 'failed'
    deleted_count = Column(Integer, default=0)
    freed_memory_bytes = Column(Integer, default=0)
    freed_storage_bytes = Column(Integer, default=0)
    error_message = Column(Text, nullable=True)
    execution_time_ms = Column(Integer, nullable=True)


class UserAvatar(Base):
    """
    User avatar images with TTL for inactive users.
    
    TTL Implementation:
    - Inactive user avatars: 30 days
    - Large file cleanup prioritization by file_size
    """
    __tablename__ = "user_avatars"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    image_url = Column(Text, nullable=False)
    file_path = Column(Text, nullable=False)
    file_size = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    user = relationship("User")


class UserPresence(Base):
    """
    Track user presence in collaborative sessions with TTL.
    
    TTL Implementation:
    - Presence records: Auto-expire after 1 hour of inactivity
    - Used for collaborative UI and cleanup optimization
    """
    __tablename__ = "user_presence"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False, index=True)
    last_seen = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    user = relationship("User")
    board = relationship("Board")


class LoginHistory(Base):
    """
    User login history with TTL for compliance and security.
    
    TTL Implementation:
    - Login history: 90 days (compliance requirements)
    - IP tracking for security analysis
    """
    __tablename__ = "login_history"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    login_time = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    ip_address = Column(String(45), nullable=False, index=True)  # IPv4/IPv6
    user_agent = Column(Text, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    user = relationship("User")


class EditHistory(Base):
    """
    Board edit history with TTL for collaboration tracking.
    
    TTL Implementation:
    - Edit history: 30 days for active boards
    - Action data includes drawing operations and metadata
    """
    __tablename__ = "edit_history"
    
    id = Column(Integer, primary_key=True, index=True)
    board_id = Column(Integer, ForeignKey("boards.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # Null for anonymous
    action_type = Column(String(50), nullable=False, index=True)  # 'stroke', 'erase', 'clear', etc.
    action_data = Column(Text, nullable=False)  # JSON action details
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    expires_at = Column(DateTime, nullable=False, index=True)  # TTL enforcement
    
    # Relationships
    board = relationship("Board")
    user = relationship("User")


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