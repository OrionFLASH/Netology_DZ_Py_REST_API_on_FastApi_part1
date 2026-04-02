"""
Точка входа FastAPI-приложения «Сервис объявлений» с JWT и пользователями (часть 2).

При старте настраивается логирование и при необходимости создаётся администратор из `.env`.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.logging_setup import log_debug, setup_logging
from src.router_advertisement import router as advertisement_router
from src.router_login import router as login_router
from src.router_user import router as user_router
from src.user_storage import UserRole, user_store

logger: logging.Logger = logging.getLogger(__name__)


def ensure_bootstrap_admin() -> None:
    """
    Создаёт учётную запись администратора из переменных окружения, если она задана
    и пользователь с таким логином ещё не существует.

    Удобно для первого запуска без отдельного скрипта регистрации.
    """
    settings = get_settings()
    if not settings.bootstrap_admin_username or not settings.bootstrap_admin_password:
        return
    if user_store.get_by_username(settings.bootstrap_admin_username) is not None:
        return
    user_store.create(
        settings.bootstrap_admin_username,
        settings.bootstrap_admin_password,
        UserRole.admin,
    )
    logger.info(
        "Создан начальный администратор (логин из BOOTSTRAP_ADMIN_USERNAME)"
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Жизненный цикл приложения: логирование и опциональный bootstrap-админ.

    Args:
        app: экземпляр FastAPI.

    Yields:
        Управление передаётся серверу на время работы приложения.
    """
    settings = get_settings()
    setup_logging(console_level=settings.log_level)
    ensure_bootstrap_admin()
    log_debug(
        logger,
        "Приложение запущено, логирование инициализировано",
        class_name="main",
        def_name="lifespan",
    )
    logger.info("Сервис объявлений готов к приёму запросов")
    yield


app: FastAPI = FastAPI(
    title="Сервис объявлений (купля/продажа)",
    description=(
        "Учебный REST API на FastAPI: объявления, пользователи, JWT (Netology 3.1–3.2)."
    ),
    version="2.0.0",
    lifespan=lifespan,
)

app.include_router(login_router)
app.include_router(user_router)
app.include_router(advertisement_router)
