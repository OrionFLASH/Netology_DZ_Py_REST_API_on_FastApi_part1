"""
Pydantic-схемы для тел запросов и ответов API (объявления, пользователи, токен).

Объявления: поля из части 1 задания. Пользователи и JWT — из части 2.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator

from src.user_storage import UserRole


class AdvertisementCreate(BaseModel):
    """
    Данные для создания объявления (POST /advertisement).

    Поле `author` опционально: для обычного пользователя подставляется его логин;
    администратор может указать отображаемое имя автора явно.
    """

    title: str = Field(..., min_length=1, max_length=500, description="Заголовок объявления")
    description: str = Field(
        ..., min_length=1, max_length=8000, description="Текстовое описание"
    )
    price: float = Field(..., ge=0, description="Цена (неотрицательное число)")
    author: Optional[str] = Field(
        None,
        min_length=1,
        max_length=200,
        description="Отображаемый автор (опционально; по умолчанию — логин создателя)",
    )

    @field_validator("title", "description", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        """Убирает лишние пробелы по краям строковых полей."""
        if isinstance(value, str):
            return value.strip()
        return value

    @field_validator("author", mode="before")
    @classmethod
    def strip_author(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            s: str = value.strip()
            return s if s else None
        return value


class AdvertisementUpdate(BaseModel):
    """
    Частичное обновление объявления (PATCH /advertisement/{id}).

    Изменение поля `author` разрешено только администратору (проверка в роутере).
    """

    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, min_length=1, max_length=8000)
    price: Optional[float] = Field(None, ge=0)
    author: Optional[str] = Field(None, min_length=1, max_length=200)

    @field_validator("title", "description", "author", mode="before")
    @classmethod
    def strip_optional_strings(cls, value: object) -> object:
        if value is None:
            return None
        if isinstance(value, str):
            return value.strip()
        return value


class AdvertisementRead(BaseModel):
    """Представление объявления в ответах API (включая id и дату создания)."""

    model_config = {"from_attributes": True}

    id: str = Field(..., description="Уникальный идентификатор объявления")
    title: str
    description: str
    price: float
    author: str
    created_at: datetime = Field(..., description="Дата и время создания (UTC)")


class AdvertisementListResponse(BaseModel):
    """Обёртка для списка объявлений при поиске (GET /advertisement)."""

    items: list[AdvertisementRead] = Field(default_factory=list)
    total: int = Field(..., ge=0, description="Количество найденных записей")


class UserCreate(BaseModel):
    """Регистрация пользователя (POST /user)."""

    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)
    role: UserRole = Field(
        default=UserRole.user,
        description="Роль: задать `admin` может только действующий администратор",
    )

    @field_validator("username", mode="before")
    @classmethod
    def strip_username(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class UserUpdate(BaseModel):
    """Частичное обновление пользователя (PATCH /user/{user_id})."""

    password: Optional[str] = Field(None, min_length=1, max_length=200)
    role: Optional[UserRole] = None


class UserRead(BaseModel):
    """Пользователь в ответах API (без пароля)."""

    id: str
    username: str
    role: UserRole


class LoginRequest(BaseModel):
    """Тело запроса входа (POST /login)."""

    username: str
    password: str

    @field_validator("username", mode="before")
    @classmethod
    def strip_login(cls, value: object) -> object:
        if isinstance(value, str):
            return value.strip()
        return value


class TokenResponse(BaseModel):
    """Ответ с JWT после успешного входа."""

    access_token: str = Field(..., description="JWT, срок действия задаётся на сервере (48 ч)")
    token_type: str = Field(default="bearer")
