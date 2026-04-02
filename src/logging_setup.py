"""
Настройка логирования в файлы и консоль.

Требования к проекту:
- отдельный поток событий уровня INFO (основные события);
- отдельный файл DEBUG со строгим форматом строки с указанием класса и функции.
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Final

# Корень репозитория
_PROJECT_ROOT: Final[Path] = Path(__file__).resolve().parent.parent
_LOG_DIR: Final[Path] = _PROJECT_ROOT / "log"

# Шаблон имени файла: Уровень_(тема)_годмесяцдень_час.log
_SAFE_TOPIC_PATTERN: Final[re.Pattern[str]] = re.compile(r"[^a-zA-Z0-9_]+")


class _OnlyDebugFilter(logging.Filter):
    """Пропускает только записи уровня DEBUG в отдельный DEBUG-файл."""

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno == logging.DEBUG


class _DebugStructuredFormatter(logging.Formatter):
    """
    Форматтер для DEBUG: дата время - [DEBUG] - сообщение [class: X | def: Y].

    Поля `class_name` и `def_name` передаются через `logger.debug(..., extra={...})`.
    """

    def format(self, record: logging.LogRecord) -> str:
        class_name: str = getattr(record, "class_name", "-")
        def_name: str = getattr(record, "def_name", record.funcName)
        record.message = record.getMessage()
        # asctime задаётся через datefmt в базовом Formatter
        return (
            f"{self.formatTime(record, self.datefmt)} - [DEBUG] - {record.message} "
            f"[class: {class_name} | def: {def_name}]"
        )


class _InfoFormatter(logging.Formatter):
    """Краткий формат для INFO-файла и консоли."""

    def __init__(self) -> None:
        super().__init__(
            fmt="%(asctime)s - [%(levelname)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def _sanitize_topic(topic: str) -> str:
    """Приводит тему к безопасному фрагменту имени файла."""
    cleaned: str = _SAFE_TOPIC_PATTERN.sub("_", topic).strip("_")
    return cleaned or "app"


def _timestamp_for_filename() -> str:
    """Возвращает метку времени для имени лог-файла: ГГГГММДД_ЧЧ."""
    return datetime.now().strftime("%Y%m%d_%H")


def setup_logging(console_level: str = "INFO") -> None:
    """
    Инициализирует корневой логгер: консоль + файлы INFO и DEBUG в каталоге `log/`.

    Args:
        console_level: минимальный уровень для вывода в stderr (например, INFO или DEBUG).
    """
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    topic: str = _sanitize_topic("advertisement_api")
    ts: str = _timestamp_for_filename()

    info_path: Path = _LOG_DIR / f"INFO_{topic}_{ts}.log"
    debug_path: Path = _LOG_DIR / f"DEBUG_{topic}_{ts}.log"

    root: logging.Logger = logging.getLogger()
    root.handlers.clear()
    root.setLevel(logging.DEBUG)

    info_handler: logging.FileHandler = logging.FileHandler(
        info_path, encoding="utf-8"
    )
    info_handler.setLevel(logging.INFO)
    info_handler.setFormatter(_InfoFormatter())

    debug_handler: logging.FileHandler = logging.FileHandler(
        debug_path, encoding="utf-8"
    )
    debug_handler.setLevel(logging.DEBUG)
    debug_fmt: _DebugStructuredFormatter = _DebugStructuredFormatter()
    debug_fmt.datefmt = "%Y-%m-%d %H:%M:%S"
    debug_handler.setFormatter(debug_fmt)
    debug_handler.addFilter(_OnlyDebugFilter())

    console: logging.StreamHandler = logging.StreamHandler()
    console.setLevel(getattr(logging, console_level.upper(), logging.INFO))
    console.setFormatter(_InfoFormatter())

    root.addHandler(info_handler)
    root.addHandler(debug_handler)
    root.addHandler(console)


def log_debug(
    logger: logging.Logger,
    message: str,
    *,
    class_name: str,
    def_name: str,
) -> None:
    """
    Пишет строку в DEBUG-лог в требуемом формате (через extra).

    Args:
        logger: логгер модуля.
        message: текст сообщения.
        class_name: имя класса для суффикса записи.
        def_name: имя функции/метода.
    """
    logger.debug(message, extra={"class_name": class_name, "def_name": def_name})
