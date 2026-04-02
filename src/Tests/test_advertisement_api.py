"""
Автотесты REST API объявлений (основные сценарии из задания).
"""

from typing import Any

from fastapi.testclient import TestClient


def _create_sample(client: TestClient) -> dict[str, Any]:
    """Создаёт тестовое объявление и возвращает JSON-ответ."""
    payload: dict[str, Any] = {
        "title": "Велосипед",
        "description": "Горный, почти новый",
        "price": 15000.0,
        "author": "Иван",
    }
    response = client.post("/advertisement", json=payload)
    assert response.status_code == 201
    return response.json()


def test_create_and_get_by_id(client: TestClient) -> None:
    created: dict[str, Any] = _create_sample(client)
    adv_id: str = created["id"]
    get_resp = client.get(f"/advertisement/{adv_id}")
    assert get_resp.status_code == 200
    body: dict[str, Any] = get_resp.json()
    assert body["title"] == "Велосипед"
    assert body["author"] == "Иван"
    assert "created_at" in body


def test_get_404(client: TestClient) -> None:
    response = client.get("/advertisement/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_patch_and_delete(client: TestClient) -> None:
    created: dict[str, Any] = _create_sample(client)
    adv_id: str = created["id"]
    patch_resp = client.patch(
        f"/advertisement/{adv_id}",
        json={"price": 12000.0, "title": "Велосипед горный"},
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["price"] == 12000.0
    assert patch_resp.json()["title"] == "Велосипед горный"

    del_resp = client.delete(f"/advertisement/{adv_id}")
    assert del_resp.status_code == 204
    assert client.get(f"/advertisement/{adv_id}").status_code == 404


def test_search_by_query_params(client: TestClient) -> None:
    client.post(
        "/advertisement",
        json={
            "title": "Телефон",
            "description": "Смартфон Android",
            "price": 20000.0,
            "author": "Мария",
        },
    )
    client.post(
        "/advertisement",
        json={
            "title": "Ноутбук",
            "description": "Для работы",
            "price": 45000.0,
            "author": "Пётр",
        },
    )
    resp = client.get("/advertisement", params={"author": "мария"})
    assert resp.status_code == 200
    data: dict[str, Any] = resp.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Телефон"

    resp_price = client.get(
        "/advertisement", params={"price_min": 30000.0, "price_max": 50000.0}
    )
    assert resp_price.json()["total"] == 1
    assert resp_price.json()["items"][0]["title"] == "Ноутбук"


def test_list_all_without_filters(client: TestClient) -> None:
    _create_sample(client)
    resp = client.get("/advertisement")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1
