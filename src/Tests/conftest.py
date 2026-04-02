"""
Фикстуры pytest: изолированное хранилище для каждого теста через dependency_overrides.
"""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.router_advertisement import get_store
from src.storage import AdvertisementStore


@pytest.fixture()
def client() -> Generator[TestClient, None, None]:
    """TestClient с пустым in-memory хранилищем на время теста."""
    fresh_store: AdvertisementStore = AdvertisementStore()

    def _override_store() -> AdvertisementStore:
        return fresh_store

    app.dependency_overrides[get_store] = _override_store
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
