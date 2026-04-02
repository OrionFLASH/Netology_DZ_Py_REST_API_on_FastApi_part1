"""
Роуты управления пользователями и проверка прав по заданию части 2.
"""

import logging
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.deps import (
    CurrentUser,
    get_advertisement_store,
    get_current_user_optional,
    get_user_store,
    require_current_user,
)
from src.logging_setup import log_debug
from src.schemas import UserCreate, UserRead, UserUpdate
from src.storage import AdvertisementStore
from src.user_storage import UserRole, UserStore

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter(tags=["users"])


def _resolve_role_for_create(body: UserCreate, current: Optional[CurrentUser]) -> UserRole:
    """
    Определяет роль нового пользователя.

    Создать учётную запись с ролью `admin` может только действующий администратор;
    без авторизации или под обычным пользователем создаётся только `user`.
    """
    if current is not None and current.role == UserRole.admin:
        return body.role
    if body.role == UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Создание администратора доступно только существующему admin",
        )
    return UserRole.user


@router.get(
    "/user/{user_id}",
    response_model=UserRead,
    summary="Получить пользователя по id",
)
def get_user(
    user_id: str,
    users: Annotated[UserStore, Depends(get_user_store)],
) -> UserRead:
    """
    Доступно без токена (по заданию — в числе прав неавторизованного клиента).
    """
    log_debug(
        logger,
        f"Запрос GET /user/{user_id}",
        class_name="router_user",
        def_name="get_user",
    )
    record = users.get_by_id(user_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return UserRead(id=record.id, username=record.username, role=record.role)


@router.post(
    "/user",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
    summary="Создать пользователя",
)
def create_user(
    body: UserCreate,
    users: Annotated[UserStore, Depends(get_user_store)],
    current: Annotated[Optional[CurrentUser], Depends(get_current_user_optional)],
) -> UserRead:
    """
    Без авторизации можно создать только пользователя с ролью `user`.
    Администратор может назначить роль `admin` или `user`.
    """
    log_debug(
        logger,
        "Запрос POST /user",
        class_name="router_user",
        def_name="create_user",
    )
    role: UserRole = _resolve_role_for_create(body, current)
    try:
        record = users.create(body.username, body.password, role)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    return UserRead(id=record.id, username=record.username, role=record.role)


@router.patch(
    "/user/{user_id}",
    response_model=UserRead,
    summary="Обновить пользователя",
)
def patch_user(
    user_id: str,
    body: UserUpdate,
    users: Annotated[UserStore, Depends(get_user_store)],
    current: Annotated[CurrentUser, Depends(require_current_user)],
) -> UserRead:
    """
    Обычный пользователь может менять только себя; администратор — любого.
    Смена роли — только у администратора.
    """
    log_debug(
        logger,
        f"Запрос PATCH /user/{user_id}",
        class_name="router_user",
        def_name="patch_user",
    )
    if current.role != UserRole.admin and current.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для изменения этого пользователя",
        )
    if body.role is not None and current.role != UserRole.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для смены роли",
        )
    updated = users.update(
        user_id,
        plain_password=body.password,
        role=body.role,
    )
    if updated is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    return UserRead(id=updated.id, username=updated.username, role=updated.role)


@router.delete(
    "/user/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Удалить пользователя",
)
def delete_user(
    user_id: str,
    users: Annotated[UserStore, Depends(get_user_store)],
    ads: Annotated[AdvertisementStore, Depends(get_advertisement_store)],
    current: Annotated[CurrentUser, Depends(require_current_user)],
) -> None:
    """
    Пользователь может удалить только себя; администратор — любого.
    Объявления удалённого владельца удаляются каскадно из in-memory хранилища.
    """
    log_debug(
        logger,
        f"Запрос DELETE /user/{user_id}",
        class_name="router_user",
        def_name="delete_user",
    )
    if current.role != UserRole.admin and current.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав для удаления этого пользователя",
        )
    if users.get_by_id(user_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден",
        )
    ads.delete_by_owner(user_id)
    users.delete(user_id)
