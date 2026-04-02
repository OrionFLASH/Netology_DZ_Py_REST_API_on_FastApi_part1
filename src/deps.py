"""
Зависимости FastAPI: хранилища, настройки, извлечение текущего пользователя из JWT.
"""

from dataclasses import dataclass
from typing import Annotated, Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.config import Settings, get_settings
from src.jwt_service import decode_access_token
from src.storage import AdvertisementStore, store as _advertisement_store
from src.user_storage import UserRole, UserStore, user_store

# Bearer-токен необязателен: для публичных маршрутов вернётся None
_http_bearer: HTTPBearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class CurrentUser:
    """Данные аутентифицированного пользователя (из БД, не только из токена)."""

    id: str
    username: str
    role: UserRole


def get_user_store() -> UserStore:
    """Возвращает хранилище пользователей (подменяется в тестах)."""
    return user_store


def get_advertisement_store() -> AdvertisementStore:
    """Возвращает хранилище объявлений (подменяется в тестах)."""
    return _advertisement_store


def get_current_user_optional(
    credentials: Annotated[
        Optional[HTTPAuthorizationCredentials],
        Depends(_http_bearer),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
    users: Annotated[UserStore, Depends(get_user_store)],
) -> Optional[CurrentUser]:
    """
    Достаёт пользователя из JWT, если заголовок Authorization передан и валиден.

    Raises:
        HTTPException 401: токен битый/просрочен (клиент передал заголовок, но он невалиден).
    """
    if credentials is None:
        return None
    raw_token: str = credentials.credentials
    try:
        payload: dict[str, object] = decode_access_token(raw_token, settings)
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Недействительный или просроченный токен",
        )
    sub_raw: object | None = payload.get("sub")
    if not isinstance(sub_raw, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный формат токена",
        )
    record = users.get_by_id(sub_raw)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
        )
    # Роль берётся из актуальной записи, а не только из токена
    return CurrentUser(id=record.id, username=record.username, role=record.role)


def require_current_user(
    current: Annotated[
        Optional[CurrentUser],
        Depends(get_current_user_optional),
    ],
) -> CurrentUser:
    """Требует заголовок Authorization с валидным JWT."""
    if current is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Требуется авторизация",
        )
    return current
