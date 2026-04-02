"""
In-memory хранилище объявлений с блокировкой для потокобезопасности.

Для учебного задания достаточно оперативной памяти; при перезапуске процесса
данные не сохраняются. Структура изолирована, чтобы при необходимости заменить
реализацию на БД без изменения контрактов HTTP.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterator, Optional
from uuid import uuid4

from src.logging_setup import log_debug
from src.schemas import AdvertisementCreate, AdvertisementUpdate

logger: logging.Logger = logging.getLogger(__name__)


def _utc_now() -> datetime:
    """Текущий момент в UTC (наивная или aware — единообразно aware)."""
    return datetime.now(timezone.utc)


@dataclass
class AdvertisementRecord:
    """
    Внутренняя модель записи объявления в хранилище.

    Attributes:
        id: строковый UUID.
        title: заголовок.
        description: описание.
        price: цена.
        author: автор.
        created_at: момент создания в UTC.
    """

    id: str
    title: str
    description: str
    price: float
    author: str
    created_at: datetime


class AdvertisementStore:
    """
    Репозиторий объявлений в памяти процесса.

    Все публичные методы защищены одной блокировкой `threading.RLock`, чтобы
    корректно работать при конкурентных запросах к uvicorn с несколькими воркерами
    важно помнить: у каждого воркера будет свой экземпляр памяти.
    """

    def __init__(self) -> None:
        self._lock: threading.RLock = threading.RLock()
        self._by_id: dict[str, AdvertisementRecord] = {}

    def create(self, payload: AdvertisementCreate) -> AdvertisementRecord:
        """Создаёт новое объявление и возвращает полную запись."""
        with self._lock:
            new_id: str = str(uuid4())
            record: AdvertisementRecord = AdvertisementRecord(
                id=new_id,
                title=payload.title,
                description=payload.description,
                price=payload.price,
                author=payload.author,
                created_at=_utc_now(),
            )
            self._by_id[new_id] = record
            log_debug(
                logger,
                f"Создано объявление id={new_id}",
                class_name="AdvertisementStore",
                def_name="create",
            )
            logger.info("Создано объявление id=%s", new_id)
            return record

    def get(self, advertisement_id: str) -> Optional[AdvertisementRecord]:
        """Возвращает запись по идентификатору или None."""
        with self._lock:
            return self._by_id.get(advertisement_id)

    def update(
        self, advertisement_id: str, payload: AdvertisementUpdate
    ) -> Optional[AdvertisementRecord]:
        """
        Частично обновляет поля объявления.

        Пустой PATCH (все поля None) оставляет запись без изменений.
        """
        with self._lock:
            current: Optional[AdvertisementRecord] = self._by_id.get(advertisement_id)
            if current is None:
                return None
            data: dict[str, object] = {
                "title": payload.title if payload.title is not None else current.title,
                "description": (
                    payload.description
                    if payload.description is not None
                    else current.description
                ),
                "price": payload.price if payload.price is not None else current.price,
                "author": payload.author if payload.author is not None else current.author,
            }
            updated: AdvertisementRecord = AdvertisementRecord(
                id=current.id,
                title=str(data["title"]),
                description=str(data["description"]),
                price=float(data["price"]),
                author=str(data["author"]),
                created_at=current.created_at,
            )
            self._by_id[advertisement_id] = updated
            log_debug(
                logger,
                f"Обновлено объявление id={advertisement_id}",
                class_name="AdvertisementStore",
                def_name="update",
            )
            logger.info("Обновлено объявление id=%s", advertisement_id)
            return updated

    def delete(self, advertisement_id: str) -> bool:
        """Удаляет объявление. Возвращает True, если запись существовала."""
        with self._lock:
            if advertisement_id not in self._by_id:
                return False
            del self._by_id[advertisement_id]
            log_debug(
                logger,
                f"Удалено объявление id={advertisement_id}",
                class_name="AdvertisementStore",
                def_name="delete",
            )
            logger.info("Удалено объявление id=%s", advertisement_id)
            return True

    def search(
        self,
        *,
        title_substring: Optional[str] = None,
        description_substring: Optional[str] = None,
        author_substring: Optional[str] = None,
        price_min: Optional[float] = None,
        price_max: Optional[float] = None,
        created_from: Optional[datetime] = None,
        created_to: Optional[datetime] = None,
    ) -> list[AdvertisementRecord]:
        """
        Отбор объявлений по переданным полям (логика AND).

        Строковые фильтры — без учёта регистра, подстрока в соответствующем поле.
        Диапазоны цены и дат задаются включительно на уровне сравнения в коде.
        """
        with self._lock:
            result: list[AdvertisementRecord] = []
            for rec in self._by_id.values():
                if title_substring is not None:
                    if title_substring.lower() not in rec.title.lower():
                        continue
                if description_substring is not None:
                    if description_substring.lower() not in rec.description.lower():
                        continue
                if author_substring is not None:
                    if author_substring.lower() not in rec.author.lower():
                        continue
                if price_min is not None and rec.price < price_min:
                    continue
                if price_max is not None and rec.price > price_max:
                    continue
                if created_from is not None and rec.created_at < created_from:
                    continue
                if created_to is not None and rec.created_at > created_to:
                    continue
                result.append(rec)
            log_debug(
                logger,
                f"Поиск вернул {len(result)} записей",
                class_name="AdvertisementStore",
                def_name="search",
            )
            logger.info("Поиск объявлений: найдено %s записей", len(result))
            return result

    def iter_all(self) -> Iterator[AdvertisementRecord]:
        """Итератор по всем записям (снимок под блокировкой)."""
        with self._lock:
            for r in list(self._by_id.values()):
                yield r


# Единственный экземпляр хранилища на процесс (dependency в FastAPI)
store: AdvertisementStore = AdvertisementStore()
