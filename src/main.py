"""
Точка входа FastAPI-приложения «Сервис объявлений».

При старте настраивается логирование в каталог `log/` и консоль.
"""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.logging_setup import log_debug, setup_logging
from src.router_advertisement import router as advertisement_router

logger: logging.Logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """
    Жизненный цикл приложения: инициализация логирования до приёма запросов.

    Args:
        app: экземпляр FastAPI (зарезервирован для возможных будущих хуков).

    Yields:
        Управление передаётся серверу на время работы приложения.
    """
    settings = get_settings()
    setup_logging(console_level=settings.log_level)
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
        "Учебный REST API на FastAPI по заданию Netology: объявления без авторизации."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(advertisement_router)
