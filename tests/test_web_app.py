from fastapi.testclient import TestClient

from web.app import app


client = TestClient(app)


def test_home_page() -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "MatchMan" in response.text


def test_discovery_filter() -> None:
    response = client.get("/women/discover", params={"city": "Paris"})
    assert response.status_code == 200
    assert "NoahFit" in response.text
    assert "LeoArt" not in response.text


def test_create_match_redirects_to_conversation() -> None:
    response = client.post(
        "/women/match",
        data={"man_id": 1, "woman_id": 7, "woman_name": "Alice"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert response.headers["location"].startswith("/conversations/")
