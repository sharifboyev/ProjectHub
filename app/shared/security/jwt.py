import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import jwt

from app.shared.config.settings import settings


def create_access_token(subject: str | uuid.UUID, expires_delta: Optional[timedelta] = None) -> str:
    """Создает JWT Access Token сроком действия 1 час."""
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: Dict[str, Any] = {
        "sub": str(subject),
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Декодирует и проверяет JWT токен."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None