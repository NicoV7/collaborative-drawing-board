"""
Authentication utilities: JWT, password hashing, user management.
Optimized for low latency performance targets.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr

from .database import User

# Security configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context - optimized for low latency
# Using 4 rounds for development/testing (vs default 12)
# Production should use environment variable: BCRYPT_ROUNDS=10
import os
bcrypt_rounds = int(os.getenv("BCRYPT_ROUNDS", "4"))
pwd_context = CryptContext(
    schemes=["bcrypt"], 
    deprecated="auto",
    bcrypt__rounds=bcrypt_rounds
)


class UserCreate(BaseModel):
    """User creation schema."""
    email: EmailStr
    username: str
    password: str
    
    model_config = {"str_min_length": 1}
        
    def model_post_init(self, __context):
        if len(self.password) < 8:
            raise ValueError("Password must be at least 8 characters long")


class UserLogin(BaseModel):
    """User login schema."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User response schema (no sensitive data)."""
    id: int
    email: str
    username: str
    created_at: datetime
    is_active: bool
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plaintext password against hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password using bcrypt."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Create JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Get user by username."""
    return db.query(User).filter(User.username == username).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user with hashed password."""
    # Check if user exists
    existing_user = get_user_by_email(db, user.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    existing_username = get_user_by_username(db, user.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already taken"
        )
    
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        username=user.username,
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user credentials."""
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user