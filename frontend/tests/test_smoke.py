import os
import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parents[2]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from frontend.app import app
from fastapi.testclient import TestClient


def test_home_shows_public_landing():
    client = TestClient(app)
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 200
    assert "/citizen/report" in response.text
    assert "/login" in response.text
