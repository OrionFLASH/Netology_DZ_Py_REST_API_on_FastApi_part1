"""
Модуль настроек приложения.

Загружает переменные из окружения и файла `.env` (через pydantic-settings),
чтобы хост, порт и уровень логирования можно было задавать без правки кода.
"""

from pathlib import Path

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
    """

    model_config = SettingsConfigDict(
        env_file=_PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"


def get_settings() -> Settings:
    """
    Возвращает экземпляр настроек (удобно для тестов и переопределения).

    Returns:
        Объект Settings с актуальными значениями из окружения.
    """
    return Settings()
