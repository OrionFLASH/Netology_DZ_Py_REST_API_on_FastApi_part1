"""
Роут входа: выдача JWT при корректных учётных данных.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.config import Settings, get_settings
from src.jwt_service import create_access_token
from src.logging_setup import log_debug
from src.schemas import LoginRequest, TokenResponse
from src.deps import get_user_store
from src.user_storage import UserStore

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter(tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Вход и получение токена",
)
def login(
    body: LoginRequest,
    users: Annotated[UserStore, Depends(get_user_store)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """
    Принимает JSON с именем пользователя и паролем.

    При неверной паре логин/пароль возвращает 401. При успехе — JWT со сроком
    действия из настроек (по заданию — 48 часов).
    """
    log_debug(
        logger,
        "Запрос POST /login",
        class_name="router_login",
        def_name="login",
    )
    record = users.verify_credentials(body.username, body.password)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
        )
    token: str = create_access_token(
        user_id=record.id,
        role=record.role.value,
        settings=settings,
    )
    logger.info("Успешный вход пользователя username=%s", record.username)
    return TokenResponse(access_token=token)
