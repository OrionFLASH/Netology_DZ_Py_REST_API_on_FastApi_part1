"""
Pydantic-схемы для тела запросов и ответов API объявлений.

Соответствуют полям из задания: заголовок, описание, цена, автор, дата создания.
Идентификатор объявления генерируется на сервере при создании.
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, field_validator


class AdvertisementCreate(BaseModel):
    """
    Данные для создания объявления (POST /advertisement).

    Поля `created_at` и идентификатор в запрос не входят — задаются сервером.
    """

    title: str = Field(..., min_length=1, max_length=500, description="Заголовок объявления")
    description: str = Field(
        ..., min_length=1, max_length=8000, description="Текстовое описание"
    )
    price: float = Field(..., ge=0, description="Цена (неотрицательное число)")
    author: str = Field(..., min_length=1, max_length=200, description="Автор объявления")

    @field_validator("title", "description", "author", mode="before")
    @classmethod
    def strip_strings(cls, value: object) -> object:
        """Убирает лишние пробелы по краям строковых полей."""
        if isinstance(value, str):
            return value.strip()
        return value


class AdvertisementUpdate(BaseModel):
    """
    Частичное обновление объявления (PATCH /advertisement/{id}).

    Все поля необязательны: передаются только изменяемые атрибуты.
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
