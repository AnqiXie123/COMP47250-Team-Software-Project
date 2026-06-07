import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

SAMPLE_CHARGER = {
    "id": "esb_0",
    "lat": 53.611523,
    "lon": -6.182852,
    "address": "Irish Rail, Railway Street, Balbriggan",
    "operator": "ESB eCars",
    "num_chargers": 1,
    "source_area": "ESB_national",
    "open_hours": "24 x 7",
}


class _MockResult:
    def mappings(self):
        return self

    def all(self):
        return [SAMPLE_CHARGER]


class _MockSession:
    async def execute(self, query):
        return _MockResult()


async def _mock_get_db():
    yield _MockSession()


@pytest.fixture(autouse=True)
def override_db():
    app.dependency_overrides[get_db] = _mock_get_db
    yield
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_chargers_status_200():
    response = client.get("/api/chargers")
    assert response.status_code == 200


def test_get_chargers_returns_list():
    response = client.get("/api/chargers")
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1


def test_get_chargers_fields():
    response = client.get("/api/chargers")
    charger = response.json()[0]
    assert charger["id"] == "esb_0"
    assert charger["lat"] == 53.611523
    assert charger["lon"] == -6.182852
    assert charger["operator"] == "ESB eCars"
    assert charger["num_chargers"] == 1
