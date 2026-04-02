"""
Модуль настроек приложения.

Загружает переменные из окружения и файла `.env` (через pydantic-settings),
чтобы хост, порт, уровень логирования, секрет JWT и начальный администратор
задавались без правки кода.
"""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Корень репозитория: родитель каталога `src`
_PROJECT_ROOT: Path = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """
    Конфигурация сервиса, считываемая из переменных окружения.

    Атрибуты:
        app_host: интерфейс прослушивания uvicorn.
        app_port: порт HTTP-сервера.
        log_level: уровень логов в консоль (файлы INFO/DEBUG настраиваются отдельно).
        jwt_secret: секрет для подписи JWT (в продакшене — длинная случайная строка).
        jwt_algorithm: алгоритм подписи (по умолчанию HS256).
        access_token_expire_hours: срок жизни токена в часах (по заданию — 48).
        bootstrap_admin_username / bootstrap_admin_password: при старте создаётся
            администратор с этими учётными данными, если пользователь ещё не существует.
    """

    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"

    jwt_secret: str = Field(
        default="dev-only-change-me-use-long-random-string-in-env",
        description="Секрет для JWT",
    )
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 48

    bootstrap_admin_username: str | None = None
    bootstrap_admin_password: str | None = None


def get_settings() -> Settings:
    """
    Возвращает экземпляр настроек (удобно для тестов и переопределения).

    Returns:
        Объект Settings с актуальными значениями из окружения.
    """
    return Settings()
