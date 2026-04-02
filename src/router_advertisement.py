"""
HTTP-маршруты объявлений: CRUD и поиск по query string.

Пути и методы соответствуют формулировке задания Netology (без аутентификации).
"""

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.logging_setup import log_debug
from src.schemas import (
    AdvertisementCreate,
    AdvertisementListResponse,
    AdvertisementRead,
    AdvertisementUpdate,
)
from src.storage import AdvertisementRecord, AdvertisementStore, store

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


def get_store() -> AdvertisementStore:
    """Зависимость FastAPI: возвращает общее хранилище объявлений."""
    return store


def _to_read(record: AdvertisementRecord) -> AdvertisementRead:
    """Преобразует внутреннюю запись в схему ответа API."""
    return AdvertisementRead(
        id=record.id,
        title=record.title,
        description=record.description,
        price=record.price,
        author=record.author,
        created_at=record.created_at,
    )


@router.post(
    "/advertisement",
    response_model=AdvertisementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать объявление",
)
def create_advertisement(
    body: AdvertisementCreate,
    repo: Annotated[AdvertisementStore, Depends(get_store)],
) -> AdvertisementRead:
    """Создаёт объявление; дата создания и id назначаются сервером."""
    log_debug(
        logger,
        "Запрос POST /advertisement",
        class_name="router_advertisement",
        def_name="create_advertisement",
    )
    created: AdvertisementRecord = repo.create(body)
    return _to_read(created)


@router.patch(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementRead,
    summary="Обновить объявление",
)
def patch_advertisement(
    advertisement_id: str,
    body: AdvertisementUpdate,
    repo: Annotated[AdvertisementStore, Depends(get_store)],
) -> AdvertisementRead:
    """Частичное обновление полей объявления по идентификатору."""
    log_debug(
        logger,
        f"Запрос PATCH /advertisement/{advertisement_id}",
        class_name="router_advertisement",
        def_name="patch_advertisement",
    )
    updated: Optional[AdvertisementRecord] = repo.update(advertisement_id, body)
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено",
        )
    return _to_read(updated)


@router.delete(
    "/advertisement/{advertisement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить объявление",
)
def delete_advertisement(
    advertisement_id: str,
    repo: Annotated[AdvertisementStore, Depends(get_store)],
) -> None:
    """Удаляет объявление по идентификатору."""
    log_debug(
        logger,
        f"Запрос DELETE /advertisement/{advertisement_id}",
        class_name="router_advertisement",
        def_name="delete_advertisement",
    )
    if not repo.delete(advertisement_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено",
        )


@router.get(
    "/advertisement",
    response_model=AdvertisementListResponse,
    summary="Поиск объявлений",
)
def search_advertisements(
    repo: Annotated[AdvertisementStore, Depends(get_store)],
    title: Annotated[
        Optional[str],
        Query(description="Подстрока в заголовке (без учёта регистра)"),
    ] = None,
    description: Annotated[
        Optional[str],
        Query(description="Подстрока в описании (без учёта регистра)"),
    ] = None,
    author: Annotated[
        Optional[str],
        Query(description="Подстрока в имени автора (без учёта регистра)"),
    ] = None,
    price_min: Annotated[
        Optional[float],
        Query(description="Минимальная цена (включительно)", ge=0),
    ] = None,
    price_max: Annotated[
        Optional[float],
        Query(description="Максимальная цена (включительно)", ge=0),
    ] = None,
    created_from: Annotated[
        Optional[datetime],
        Query(description="Нижняя граница даты создания (ISO 8601, UTC)"),
    ] = None,
    created_to: Annotated[
        Optional[datetime],
        Query(description="Верхняя граница даты создания (ISO 8601, UTC)"),
    ] = None,
) -> AdvertisementListResponse:
    """
    Поиск по полям через query string.

    Указанные фильтры объединяются по логике «И». Без параметров возвращаются
    все объявления, имеющиеся в хранилище.
    """
    log_debug(
        logger,
        "Запрос GET /advertisement (поиск)",
        class_name="router_advertisement",
        def_name="search_advertisements",
    )
    rows: list[AdvertisementRecord] = repo.search(
        title_substring=title,
        description_substring=description,
        author_substring=author,
        price_min=price_min,
        price_max=price_max,
        created_from=created_from,
        created_to=created_to,
    )
    items: list[AdvertisementRead] = [_to_read(r) for r in rows]
    return AdvertisementListResponse(items=items, total=len(items))


@router.get(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementRead,
    summary="Получить объявление по id",
)
def get_advertisement(
    advertisement_id: str,
    repo: Annotated[AdvertisementStore, Depends(get_store)],
) -> AdvertisementRead:
    """Возвращает одно объявление по идентификатору."""
    log_debug(
        logger,
        f"Запрос GET /advertisement/{advertisement_id}",
        class_name="router_advertisement",
        def_name="get_advertisement",
    )
    record: Optional[AdvertisementRecord] = repo.get(advertisement_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено",
        )
    return _to_read(record)
