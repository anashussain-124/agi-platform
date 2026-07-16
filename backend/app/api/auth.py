"""Authentication API endpoints."""
from datetime import timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_async_session
from app.core.security import (
    hash_password, verify_password, create_access_token, decode_access_token,
    generate_api_key,
)
from app.models.user import User, UserRole, APIKey, UserSession
from app.models.brain import Brain, BrainStatus
from app.core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    token: str
    user_id: str
    email: str
    full_name: Optional[str] = None


class APIKeyResponse(BaseModel):
    key: str
    key_prefix: str
    name: str


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_async_session),
) -> User:
    """Get the current authenticated user from JWT token."""
    payload = decode_access_token(credentials.credentials)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    return user


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_async_session)):
    """Register a new user and create their Brain."""
    # Check existing user
    result = await db.execute(select(User).where(User.email == req.email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # Create user
    user = User(
        email=req.email,
        hashed_password=hash_password(req.password),
        full_name=req.full_name,
    )
    db.add(user)
    await db.flush()

    # Create their Brain
    brain = Brain(
        user_id=user.id,
        name=f"{req.full_name or user.email}'s Brain",
        status=BrainStatus.ACTIVE,
    )
    db.add(brain)

    # Generate tokens
    token = create_access_token({"sub": str(user.id)})

    return AuthResponse(
        token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
    )


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    """Authenticate a user."""
    result = await db.execute(select(User).where(User.email == req.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not user.is_active:
        raise HTTPException(status_code=403, detail="Account is disabled")

    token = create_access_token({"sub": str(user.id)})

    return AuthResponse(
        token=token,
        user_id=str(user.id),
        email=user.email,
        full_name=user.full_name,
    )


@router.get("/me")
async def get_me(user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": str(user.id),
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role.value,
        "is_mfa_enabled": user.is_mfa_enabled,
        "created_at": user.created_at.isoformat(),
    }


@router.post("/api-key")
async def create_api_key(
    name: str,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_session),
):
    """Generate a new API key."""
    key = generate_api_key()
    key_prefix = key[:8]

    api_key = APIKey(
        user_id=user.id,
        name=name,
        key_hash=hash_password(key),
        key_prefix=key_prefix,
    )
    db.add(api_key)

    return APIKeyResponse(key=key, key_prefix=key_prefix, name=name)
