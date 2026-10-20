from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from app.infrastructure.config.settings import get_settings

settings = get_settings()

ALGORITHM = settings.JWT_ALGORITHM
SECRET_KEY = settings.JWT_SECRET
ACCESS_TOKEN_EXPIRE_MINUTES = settings.JWT_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.JWT_REFRESH_EXPIRE_DAYS


def create_access_token(payload: dict) -> str:
    """Create a signed JWT access token."""
    data = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    data.update({"exp": expire, "type": "access"})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(payload: dict) -> str:
    """Create a signed JWT refresh token."""
    data = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    data.update({"exp": expire, "type": "refresh"})
    return jwt.encode(data, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        print("PAYLOAD:", payload)
        return payload

    except Exception as e:
        print("JWT ERROR:", type(e).__name__, str(e))
        return None

def get_token_expiry_seconds(token_type: str = "access") -> int:
    if token_type == "refresh":
        return REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600
    return ACCESS_TOKEN_EXPIRE_MINUTES * 60
