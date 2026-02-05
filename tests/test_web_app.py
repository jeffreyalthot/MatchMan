from uuid import uuid4

from fastapi.testclient import TestClient

from web.app import app


client = TestClient(app)


def test_home_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "MatchMan" in response.text


def test_discovery_requires_login() -> None:
    response = client.get("/women/discover", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/auth/login"


def test_woman_login_and_discovery_filter() -> None:
    response = client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "secret123"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Espace femme" in response.text

    filtered = client.get("/women/discover", params={"city": "Paris"})
    assert filtered.status_code == 200
    assert "NoahFit" in filtered.text
    assert "LeoArt" not in filtered.text


def test_register_persists_login_session() -> None:
    register_client = TestClient(app)
    response = register_client.post(
        "/auth/register",
        data={
            "username": "Nina",
            "email": f"nina-{uuid4().hex}@example.com",
            "password": "secret123",
            "role": "woman",
        },
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/women/discover"

    discover_response = register_client.get("/women/discover")
    assert discover_response.status_code == 200
    assert "Espace femme" in discover_response.text


def test_create_match_redirects_to_conversation() -> None:
    login_client = TestClient(app)
    login_client.post(
        "/auth/login",
        data={"email": "alice@example.com", "password": "secret123"},
        follow_redirects=True,
    )
    response = login_client.post(
        "/women/match",
        data={"man_id": 1, "woman_id": 7, "woman_name": "Alice"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/conversations/")
