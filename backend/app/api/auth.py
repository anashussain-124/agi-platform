"""Authentication API endpoints — uses Repository pattern for dual-mode data access."""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.core.database import get_async_session
from app.core.repository import BaseRepository
from app.core.compat_models import row_to_obj
from app.core.security import (
    hash_password, verify_password, create_access_token, decode_access_token,
)
from app.models.user import User, UserRole
from app.models.brain import Brain, BrainStatus
from app.core.logging import logger

router = APIRouter(prefix="/api/auth", tags=["auth"])
security = HTTPBearer()


# ──────────────────────────────────────────────────────────
# Request / Response schemas
# ──────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────
# Repository
# ──────────────────────────────────────────────────────────

class UserRepository(BaseRepository):
    """Data access for users and brains — works on both Supabase and SQLAlchemy."""

    async def get_user_by_email(self, email: str) -> Optional[dict | User]:
        if self.use_supabase:
            rows = await self.supabase.get("users", filters={"email": email}, limit=1)
            return rows[0] if rows else None
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: str) -> Optional[dict | User]:
        if self.use_supabase:
            rows = await self.supabase.get("users", filters={"id": user_id}, limit=1)
            return rows[0] if rows else None
        result = await self.db.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()

    async def create_user(self, email: str, hashed_password: str, full_name: Optional[str] = None) -> dict | User:
        if self.use_supabase:
            return await self.supabase.create("users", {
                "email": email,
                "hashed_password": hashed_password,
                "full_name": full_name,
                "role": "FREE",
                "is_active": True,
            })
        user = User(email=email, hashed_password=hashed_password, full_name=full_name)
        self.db.add(user)
        await self.db.flush()
        return user

    async def create_brain(self, user_id: str, name: str) -> dict | Brain:
        if self.use_supabase:
            return await self.supabase.create("brains", {
                "user_id": user_id,
                "name": name,
                "status": "ACTIVE",
            })
        brain = Brain(user_id=uuid.UUID(user_id), name=name, status=BrainStatus.ACTIVE)
        self.db.add(brain)
        return brain


# ──────────────────────────────────────────────────────────
# Dependency: get current user from JWT
# ──────────────────────────────────────────────────────────

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

    repo = UserRepository(db)
    user = await repo.get_user_by_id(user_id)

    if not user:
        raise HTTPException(status_code=401, detail="User not found or inactive")

    # Handle both dict (Supabase) and ORM (SQLAlchemy) results
    if isinstance(user, dict):
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="User not found or inactive")
        return row_to_obj(user)

    if not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    return user


# ──────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest, db: AsyncSession = Depends(get_async_session)):
    """Register a new user and create their Brain."""
    try:
        repo = UserRepository(db)

        # Check if user exists
        existing = await repo.get_user_by_email(req.email)
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered")

        # Create user
        hashed = hash_password(req.password)
        user = await repo.create_user(req.email, hashed, req.full_name)

        user_id = user["id"] if isinstance(user, dict) else str(user.id)
        display_name = req.full_name or req.email

        # Create brain
        await repo.create_brain(user_id, f"{display_name}'s Brain")

        token = create_access_token({"sub": str(user_id)})

        if not repo.use_supabase:
            await db.commit()

        logger.info("New user registered: %s", req.email)
        return AuthResponse(
            token=token,
            user_id=str(user_id),
            email=req.email,
            full_name=req.full_name,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Registration failed: %s", str(e)[:200])
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)[:200]}")


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_async_session)):
    """Authenticate a user."""
    repo = UserRepository(db)
    user = await repo.get_user_by_email(req.email)

    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Handle both dict and ORM
    if isinstance(user, dict):
        if not verify_password(req.password, user.get("hashed_password", "")):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        if not user.get("is_active", True):
            raise HTTPException(status_code=401, detail="Account is inactive")
        token = create_access_token({"sub": str(user["id"])})
        return AuthResponse(
            token=token, user_id=str(user["id"]), email=user["email"],
            full_name=user.get("full_name"),
        )

    # SQLAlchemy ORM path
    if not verify_password(req.password, user.hashed_password or ""):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")
    token = create_access_token({"sub": str(user.id)})
    return AuthResponse(
        token=token, user_id=str(user.id), email=user.email, full_name=user.full_name,
    )


@router.get("/me")
async def get_me(current_user=Depends(get_current_user)):
    """Get current user profile."""
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "full_name": current_user.full_name,
        "role": current_user.role.value if hasattr(current_user.role, "value") else current_user.role,
        "is_mfa_enabled": current_user.is_mfa_enabled,
    }
