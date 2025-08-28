import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as client:
        yield client


def test_index(client):
    rv = client.get("/")
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert "status" in json_data and json_data["status"] == "ok"


def test_healthz(client):
    rv = client.get("/healthz")
    assert rv.status_code == 200
    assert rv.get_data(as_text=True) == "ok"
