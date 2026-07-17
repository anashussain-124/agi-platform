"""Security utilities: JWT, encryption, password hashing."""
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt as pyjwt
from cryptography.fernet import Fernet
import base64
import hashlib
import os
import bcrypt

from app.core.config import settings


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.JWT_EXPIRATION_HOURS)
    )
    to_encode.update({"exp": expire})
    return pyjwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return payload
    except pyjwt.PyJWTError:
        return None


def decode_access_token_debug(token: str) -> str:
    """Like decode_access_token but returns error message instead of None."""
    try:
        payload = pyjwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
        return f"OK sub={payload.get('sub')}"
    except Exception as e:
        return f"ERROR: {e}"


def get_fernet() -> Fernet:
    """Get or create a Fernet encryption instance for secret encryption."""
    key = settings.ENCRYPTION_KEY
    if not key:
        # Derive from secret key if no separate encryption key set
        derived = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
        key = base64.urlsafe_b64encode(derived)
    return Fernet(key)


def encrypt_secret(value: str) -> str:
    f = get_fernet()
    return f.encrypt(value.encode()).decode()


def decrypt_secret(encrypted: str) -> str:
    f = get_fernet()
    return f.decrypt(encrypted.encode()).decode()


def generate_api_key() -> str:
    return os.urandom(32).hex()
