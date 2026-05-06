from app import app
from fastapi.testclient import TestClient


def test_home_shows_public_landing():
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    assert "/citizen/report" in response.text
    assert "/login" in response.text
