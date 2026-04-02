"""
Автотесты REST API объявлений (часть 1 + авторизация для изменений из части 2).
"""

from typing import Any

from fastapi.testclient import TestClient


def _auth_headers(token: str) -> dict[str, str]:
    """Заголовок Authorization: Bearer для запросов с JWT."""
    return {"Authorization": f"Bearer {token}"}


def _register(client: TestClient, username: str, password: str, role: str = "user") -> dict[str, Any]:
    """Регистрирует пользователя и возвращает JSON ответа."""
    response = client.post(
        "/user",
        json={"username": username, "password": password, "role": role},
    )
    assert response.status_code == 201, response.text
    return response.json()


def _login(client: TestClient, username: str, password: str) -> str:
    """Возвращает access_token."""
    response = client.post("/login", json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return str(response.json()["access_token"])


def _create_sample(client: TestClient, token: str) -> dict[str, Any]:
    """Создаёт тестовое объявление от имени пользователя с токеном."""
    payload: dict[str, Any] = {
        "title": "Велосипед",
        "description": "Горный, почти новый",
        "price": 15000.0,
    }
    response = client.post(
        "/advertisement",
        json=payload,
        headers=_auth_headers(token),
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_post_advertisement_without_token_401(client: TestClient) -> None:
    """Без JWT создание объявления запрещено (401)."""
    response = client.post(
        "/advertisement",
        json={
            "title": "X",
            "description": "Y",
            "price": 1.0,
        },
    )
    assert response.status_code == 401


def test_create_and_get_by_id(client: TestClient) -> None:
    _register(client, "ivan", "pass123")
    token: str = _login(client, "ivan", "pass123")
    created: dict[str, Any] = _create_sample(client, token)
    adv_id: str = created["id"]
    get_resp = client.get(f"/advertisement/{adv_id}")
    assert get_resp.status_code == 200
    body: dict[str, Any] = get_resp.json()
    assert body["title"] == "Велосипед"
    assert body["author"] == "ivan"
    assert "created_at" in body


def test_get_404(client: TestClient) -> None:
    response = client.get("/advertisement/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_patch_and_delete(client: TestClient) -> None:
    _register(client, "owner", "secret")
    token: str = _login(client, "owner", "secret")
    created: dict[str, Any] = _create_sample(client, token)
    adv_id: str = created["id"]
    patch_resp = client.patch(
        f"/advertisement/{adv_id}",
        json={"price": 12000.0, "title": "Велосипед горный"},
        headers=_auth_headers(token),
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["price"] == 12000.0
    assert patch_resp.json()["title"] == "Велосипед горный"

    del_resp = client.delete(
        f"/advertisement/{adv_id}",
        headers=_auth_headers(token),
    )
    assert del_resp.status_code == 204
    assert client.get(f"/advertisement/{adv_id}").status_code == 404


def test_search_by_query_params(client: TestClient) -> None:
    _register(client, "maria", "p1")
    _register(client, "petr", "p2")
    t1: str = _login(client, "maria", "p1")
    t2: str = _login(client, "petr", "p2")
    client.post(
        "/advertisement",
        json={
            "title": "Телефон",
            "description": "Смартфон Android",
            "price": 20000.0,
        },
        headers=_auth_headers(t1),
    )
    client.post(
        "/advertisement",
        json={
            "title": "Ноутбук",
            "description": "Для работы",
            "price": 45000.0,
        },
        headers=_auth_headers(t2),
    )
    resp = client.get("/advertisement", params={"author": "maria"})
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
    _register(client, "u1", "p")
    tok: str = _login(client, "u1", "p")
    _create_sample(client, tok)
    resp = client.get("/advertisement")
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


def test_cannot_patch_other_users_advertisement_403(client: TestClient) -> None:
    _register(client, "a", "p")
    _register(client, "b", "p")
    ta: str = _login(client, "a", "p")
    tb: str = _login(client, "b", "p")
    ad: dict[str, Any] = _create_sample(client, ta)
    patch = client.patch(
        f"/advertisement/{ad['id']}",
        json={"price": 1.0},
        headers=_auth_headers(tb),
    )
    assert patch.status_code == 403
