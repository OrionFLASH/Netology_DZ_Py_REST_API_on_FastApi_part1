"""
In-memory хранилище пользователей (логин, хеш пароля, роль).

Потокобезопасность — через RLock, как у объявлений.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from enum import Enum
from typing import Optional
from uuid import uuid4

from src.logging_setup import log_debug
from src.passwords import hash_password, verify_password

logger: logging.Logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Допустимые группы пользователей по заданию."""

    user = "user"
    admin = "admin"


@dataclass
class UserRecord:
    """
    Запись пользователя в памяти.

    Attributes:
        id: строковый UUID.
        username: уникальное имя для входа.
        password_hash: bcrypt-хеш пароля.
        role: группа `user` или `admin`.
    """

    id: str
    username: str
    password_hash: str
    role: UserRole


class UserStore:
    """Репозиторий пользователей в оперативной памяти процесса."""

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._by_id: dict[str, UserRecord] = {}
        self._by_username: dict[str, UserRecord] = {}

    def create(self, username: str, plain_password: str, role: UserRole) -> UserRecord:
        """
        Создаёт пользователя.

        Raises:
            ValueError: если имя пользователя уже занято.
        """
        normalized: str = username.strip()
        with self._lock:
            if normalized in self._by_username:
                raise ValueError("Имя пользователя уже занято")
            new_id: str = str(uuid4())
            record: UserRecord = UserRecord(
                id=new_id,
                username=normalized,
                password_hash=hash_password(plain_password),
                role=role,
            )
            self._by_id[new_id] = record
            self._by_username[normalized] = record
            log_debug(
                logger,
                f"Создан пользователь id={new_id} role={role.value}",
                class_name="UserStore",
                def_name="create",
            )
            logger.info("Создан пользователь username=%s", normalized)
            return record

    def get_by_id(self, user_id: str) -> Optional[UserRecord]:
        """Возвращает пользователя по id или None."""
        with self._lock:
            return self._by_id.get(user_id)

    def get_by_username(self, username: str) -> Optional[UserRecord]:
        """Возвращает пользователя по логину или None."""
        key: str = username.strip()
        with self._lock:
            return self._by_username.get(key)

    def verify_credentials(self, username: str, plain_password: str) -> Optional[UserRecord]:
        """
        Проверяет логин и пароль.

        Returns:
            Запись пользователя при успехе, иначе None.
        """
        record: Optional[UserRecord] = self.get_by_username(username)
        if record is None:
            return None
        if not verify_password(plain_password, record.password_hash):
            return None
        return record

    def update(
        self,
        user_id: str,
        *,
        plain_password: Optional[str] = None,
        role: Optional[UserRole] = None,
    ) -> Optional[UserRecord]:
        """Обновляет пароль и/или роль. Возвращает None, если пользователь не найден."""
        with self._lock:
            current: Optional[UserRecord] = self._by_id.get(user_id)
            if current is None:
                return None
            new_hash: str = (
                hash_password(plain_password)
                if plain_password is not None
                else current.password_hash
            )
            new_role: UserRole = role if role is not None else current.role
            updated: UserRecord = UserRecord(
                id=current.id,
                username=current.username,
                password_hash=new_hash,
                role=new_role,
            )
            self._by_id[user_id] = updated
            self._by_username[current.username] = updated
            log_debug(
                logger,
                f"Обновлён пользователь id={user_id}",
                class_name="UserStore",
                def_name="update",
            )
            logger.info("Обновлён пользователь id=%s", user_id)
            return updated

    def delete(self, user_id: str) -> bool:
        """Удаляет пользователя. Возвращает True, если запись существовала."""
        with self._lock:
            record: Optional[UserRecord] = self._by_id.pop(user_id, None)
            if record is None:
                return False
            del self._by_username[record.username]
            log_debug(
                logger,
                f"Удалён пользователь id={user_id}",
                class_name="UserStore",
                def_name="delete",
            )
            logger.info("Удалён пользователь id=%s", user_id)
            return True


# Глобальный экземпляр на процесс (подменяется в тестах через Depends)
user_store: UserStore = UserStore()
