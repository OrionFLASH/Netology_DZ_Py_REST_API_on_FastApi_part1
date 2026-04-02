"""
Тесты входа, пользователей и прав администратора (Netology FastAPI часть 2).
"""

from typing import Any

from fastapi.testclient import TestClient


def _bearer(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_login_invalid_401(client: TestClient) -> None:
    client.post("/user", json={"username": "u", "password": "ok"})
    response = client.post("/login", json={"username": "u", "password": "wrong"})
    assert response.status_code == 401


def test_create_admin_without_existing_admin_403(client: TestClient) -> None:
    """Без токена администратора создать роль admin нельзя (даже если в сторе уже есть сид-админ)."""
    response = client.post(
        "/user",
        json={"username": "hacker", "password": "x", "role": "admin"},
    )
    assert response.status_code == 403


def test_admin_can_create_another_admin(client: TestClient) -> None:
    """Под сид-админом из conftest создаётся второй admin."""
    login_r = client.post(
        "/login", json={"username": "seed_admin", "password": "seed_secret"}
    )
    assert login_r.status_code == 200
    admin_token: str = login_r.json()["access_token"]
    r2 = client.post(
        "/user",
        json={"username": "subadmin", "password": "p", "role": "admin"},
        headers=_bearer(admin_token),
    )
    assert r2.status_code == 201
    assert r2.json()["role"] == "admin"


def test_user_cannot_patch_another_user_403(client: TestClient) -> None:
    client.post("/user", json={"username": "alice", "password": "a"})
    carol: dict[str, Any] = client.post(
        "/user", json={"username": "carol", "password": "c"}
    ).json()
    carol_id: str = carol["id"]
    alice_login = client.post("/login", json={"username": "alice", "password": "a"})
    alice_token: str = alice_login.json()["access_token"]
    patch = client.patch(
        f"/user/{carol_id}",
        json={"password": "new"},
        headers=_bearer(alice_token),
    )
    assert patch.status_code == 403


def test_admin_can_delete_user_cascade_ads(client: TestClient) -> None:
    """Администратор удаляет пользователя; объявления этого владельца удаляются."""
    admin_tok: str = client.post(
        "/login", json={"username": "seed_admin", "password": "seed_secret"}
    ).json()["access_token"]
    victim_reg = client.post("/user", json={"username": "victim", "password": "vp"})
    assert victim_reg.status_code == 201
    victim_id: str = victim_reg.json()["id"]
    victim_tok: str = client.post(
        "/login", json={"username": "victim", "password": "vp"}
    ).json()["access_token"]
    ad: dict[str, Any] = client.post(
        "/advertisement",
        json={"title": "T", "description": "D", "price": 10.0},
        headers=_bearer(victim_tok),
    ).json()
    ad_id: str = ad["id"]
    del_r = client.delete(f"/user/{victim_id}", headers=_bearer(admin_tok))
    assert del_r.status_code == 204
    assert client.get(f"/advertisement/{ad_id}").status_code == 404


def test_admin_patch_foreign_advertisement(client: TestClient) -> None:
    """Админ может изменить чужое объявление."""
    seed_tok: str = client.post(
        "/login", json={"username": "seed_admin", "password": "seed_secret"}
    ).json()["access_token"]
    assert (
        client.post(
            "/user",
            json={"username": "adm", "password": "a", "role": "admin"},
            headers=_bearer(seed_tok),
        ).status_code
        == 201
    )
    client.post("/user", json={"username": "seller", "password": "s"})
    stok: str = client.post("/login", json={"username": "seller", "password": "s"}).json()[
        "access_token"
    ]
    ad: dict[str, Any] = client.post(
        "/advertisement",
        json={"title": "Item", "description": "D", "price": 5.0},
        headers=_bearer(stok),
    ).json()
    atok: str = client.post("/login", json={"username": "adm", "password": "a"}).json()[
        "access_token"
    ]
    patch = client.patch(
        f"/advertisement/{ad['id']}",
        json={"title": "Changed by admin"},
        headers=_bearer(atok),
    )
    assert patch.status_code == 200
    assert patch.json()["title"] == "Changed by admin"
