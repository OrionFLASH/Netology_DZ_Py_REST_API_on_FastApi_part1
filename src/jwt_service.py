"""
Выпуск и разбор JWT для авторизации (срок жизни задаётся в настройках, по умолчанию 48 ч).
"""

from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from src.config import Settings


def create_access_token(
    *,
    user_id: str,
    role: str,
    settings: Settings,
) -> str:
    """
    Формирует подписанный JWT с идентификатором пользователя и ролью.

    Args:
        user_id: первичный ключ пользователя (строка UUID).
        role: роль в системе: `user` или `admin`.
        settings: настройки (секрет, алгоритм, срок действия).

    Returns:
        Закодированный токен для заголовка Authorization: Bearer.
    """
    expire: datetime = datetime.now(timezone.utc) + timedelta(
        hours=settings.access_token_expire_hours
    )
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": expire,
    }
    token: str = jwt.encode(
        payload,
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    # PyJWT 2 возвращает str для алгоритмов вроде HS256
    return str(token)


def decode_access_token(token: str, settings: Settings) -> dict[str, Any]:
    """
    Декодирует и проверяет подпись и срок действия токена.

    Args:
        token: строка JWT без префикса Bearer.
        settings: настройки с секретом и алгоритмом.

    Returns:
        Полезная нагрузка (claims), включая `sub` и `role`.

    Raises:
        jwt.PyJWTError: неверная подпись, истёк срок и т. п.
    """
    return jwt.decode(
        token,
        settings.jwt_secret,
        algorithms=[settings.jwt_algorithm],
    )
