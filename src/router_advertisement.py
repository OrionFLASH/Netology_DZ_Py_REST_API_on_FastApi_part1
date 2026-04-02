"""
HTTP-маршруты объявлений: чтение и поиск без токена; создание/изменение/удаление с JWT.

Права по заданию Netology часть 2: владелец или admin для изменения объявлений.
"""

import logging
from datetime import datetime
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.deps import CurrentUser, get_advertisement_store, require_current_user
from src.logging_setup import log_debug
from src.schemas import (
    AdvertisementCreate,
    AdvertisementListResponse,
    AdvertisementRead,
    AdvertisementUpdate,
)
from src.storage import AdvertisementRecord, AdvertisementStore
from src.user_storage import UserRole

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter()


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


def _ensure_ad_owner_or_admin(
    record: AdvertisementRecord,
    current: CurrentUser,
) -> None:
    """Проверяет право менять/удалять объявление (владелец или admin)."""
    if current.role == UserRole.admin:
        return
    if record.owner_user_id != current.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для операции с этим объявлением",
        )


@router.post(
    "/advertisement",
    response_model=AdvertisementRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать объявление",
)
def create_advertisement(
    body: AdvertisementCreate,
    repo: Annotated[AdvertisementStore, Depends(get_advertisement_store)],
    current: Annotated[CurrentUser, Depends(require_current_user)],
) -> AdvertisementRead:
    """
    Только для авторизованных пользователей (группа user или admin).

    Отображаемый автор: по умолчанию логин текущего пользователя; администратор
    может передать поле `author` явно.
    """
    log_debug(
        logger,
        "Запрос POST /advertisement",
        class_name="router_advertisement",
        def_name="create_advertisement",
    )
    author_display: str
    if current.role == UserRole.admin and body.author:
        author_display = body.author
    else:
        author_display = current.username

    created: AdvertisementRecord = repo.create(
        title=body.title,
        description=body.description,
        price=body.price,
        author_display=author_display,
        owner_user_id=current.id,
    )
    return _to_read(created)


@router.patch(
    "/advertisement/{advertisement_id}",
    response_model=AdvertisementRead,
    summary="Обновить объявление",
)
def patch_advertisement(
    advertisement_id: str,
    body: AdvertisementUpdate,
    repo: Annotated[AdvertisementStore, Depends(get_advertisement_store)],
    current: Annotated[CurrentUser, Depends(require_current_user)],
) -> AdvertisementRead:
    """Владелец объявления или администратор; смена `author` — только admin."""
    log_debug(
        logger,
        f"Запрос PATCH /advertisement/{advertisement_id}",
        class_name="router_advertisement",
        def_name="patch_advertisement",
    )
    record: Optional[AdvertisementRecord] = repo.get(advertisement_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено",
        )
    _ensure_ad_owner_or_admin(record, current)
    if body.author is not None and body.author != record.author:
        if current.role != UserRole.admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Недостаточно прав для смены автора объявления",
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
    repo: Annotated[AdvertisementStore, Depends(get_advertisement_store)],
    current: Annotated[CurrentUser, Depends(require_current_user)],
) -> None:
    """Владелец объявления или администратор."""
    log_debug(
        logger,
        f"Запрос DELETE /advertisement/{advertisement_id}",
        class_name="router_advertisement",
        def_name="delete_advertisement",
    )
    record: Optional[AdvertisementRecord] = repo.get(advertisement_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Объявление не найдено",
        )
    _ensure_ad_owner_or_admin(record, current)
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
    repo: Annotated[AdvertisementStore, Depends(get_advertisement_store)],
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
    Поиск по полям через query string (доступно без токена).

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
    repo: Annotated[AdvertisementStore, Depends(get_advertisement_store)],
) -> AdvertisementRead:
    """Доступно без токена."""
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
