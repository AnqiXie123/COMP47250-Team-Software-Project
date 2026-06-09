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


def test_get_chargers_returns_geojson():
    data = client.get("/api/chargers").json()
    assert data["type"] == "FeatureCollection"
    assert data["count"] == 1
    assert len(data["features"]) == 1


def test_get_chargers_feature_structure():
    feature = client.get("/api/chargers").json()["features"][0]
    assert feature["type"] == "Feature"
    assert feature["geometry"]["type"] == "Point"
    assert feature["geometry"]["coordinates"] == [-6.182852, 53.611523]


def test_get_chargers_properties():
    props = client.get("/api/chargers").json()["features"][0]["properties"]
    assert props["id"] == "esb_0"
    assert props["operator"] == "ESB eCars"
    assert props["num_chargers"] == 1
    assert "lat" not in props
    assert "lon" not in props
