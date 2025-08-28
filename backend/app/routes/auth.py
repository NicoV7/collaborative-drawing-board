"""
Authentication routes: signup, login, protected endpoints.
Optimized for performance targets (<50ms signup, <30ms login).
"""

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import ValidationError

from ..database import get_db, User
from ..auth import (
    UserCreate, UserLogin, UserResponse, Token,
    create_user, authenticate_user, create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ..auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """
    Create new user account.
    Performance target: <50ms
    """
    try:
        # Validate input (FastAPI/Pydantic handles most validation)
        db_user = create_user(db, user)
        return UserResponse.model_validate(db_user)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Login user and return JWT token.
    Performance target: <30ms for valid credentials, <10ms for invalid.
    """
    # Fast fail for invalid credentials (performance optimization)
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "email": user.email, "username": user.username},
        expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user info (protected endpoint).
    Requires valid JWT token in Authorization header.
    """
    return UserResponse.model_validate(current_user)