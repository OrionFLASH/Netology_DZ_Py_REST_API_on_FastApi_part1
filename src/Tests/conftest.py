"""
Фикстуры pytest: изолированные хранилища и фиксированные настройки JWT для тестов.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.config import Settings, get_settings
from src.deps import get_advertisement_store, get_user_store
from src.main import app
from src.storage import AdvertisementStore
from src.user_storage import UserRole, UserStore


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """
    TestClient с пустыми in-memory хранилищами объявлений и пользователей.

    Подменяются зависимости `get_advertisement_store`, `get_user_store` и
    `get_settings`, чтобы токены выдавались предсказуемым секретом.
    """
    fresh_ads: AdvertisementStore = AdvertisementStore()
    fresh_users: UserStore = UserStore()
    # Первого admin по API без уже существующего admin создать нельзя — сид для тестов прав.
    fresh_users.create("seed_admin", "seed_secret", UserRole.admin)
    test_settings: Settings = Settings(
        jwt_secret="unit-test-jwt-secret-key-at-least-32-characters-long!",
        access_token_expire_hours=48,
        bootstrap_admin_username=None,
        bootstrap_admin_password=None,
    )

    def _override_ads() -> AdvertisementStore:
        return fresh_ads

    def _override_users() -> UserStore:
        return fresh_users

    def _override_settings() -> Settings:
        return test_settings

    app.dependency_overrides[get_advertisement_store] = _override_ads
    app.dependency_overrides[get_user_store] = _override_users
    app.dependency_overrides[get_settings] = _override_settings
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
