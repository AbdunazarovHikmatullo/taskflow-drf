"""Регистрация, JWT и служебные эндпоинты."""

import pytest

pytestmark = pytest.mark.django_db


def test_health(api):
    resp = api().get("/health/")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_and_obtain_jwt(api):
    client = api()
    resp = client.post(
        "/api/auth/register/",
        {"username": "hikmat", "email": "Hikmat@Example.com", "password": "VeryStr0ngPass"},
        format="json",
    )
    assert resp.status_code == 201, resp.content
    assert "password" not in resp.json()

    resp = client.post("/api/auth/token/", {"username": "hikmat", "password": "VeryStr0ngPass"}, format="json")
    assert resp.status_code == 200
    tokens = resp.json()
    assert {"access", "refresh"} <= tokens.keys()

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    me = client.get("/api/auth/me/")
    assert me.status_code == 200
    assert me.json()["email"] == "hikmat@example.com"

    refreshed = api().post("/api/auth/token/refresh/", {"refresh": tokens["refresh"]}, format="json")
    assert refreshed.status_code == 200
    assert "access" in refreshed.json()


def test_register_weak_password(api):
    resp = api().post("/api/auth/register/", {"username": "u1", "email": "u1@example.com", "password": "12345678"},
                      format="json")
    assert resp.status_code == 400


def test_register_duplicate_email(api, owner):
    resp = api().post("/api/auth/register/", {"username": "other", "email": "OWNER@example.com",
                                              "password": "VeryStr0ngPass"}, format="json")
    assert resp.status_code == 400


def test_api_requires_auth(api):
    assert api().get("/api/projects/").status_code == 401


def test_invalid_token_rejected(api):
    client = api()
    client.credentials(HTTP_AUTHORIZATION="Bearer invalid.token.value")
    assert client.get("/api/projects/").status_code == 401


def test_openapi_schema_and_docs(api):
    assert api().get("/api/schema/").status_code == 200
    assert api().get("/api/docs/").status_code == 200


def test_user_search(api, owner, member):
    resp = api(owner).get("/api/auth/users/", {"search": "mem"})
    assert resp.status_code == 200
    assert [u["username"] for u in resp.json()["results"]] == ["member"]
