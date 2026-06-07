import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.database import get_db

SAMPLE_ENERGY = {
    "datetime": "2026-04-30T23:45:00+00:00",
    "wind_mw": 1823.4,
    "solar_mw": 0.0,
    "total_demand_mw": 3241.0,
    "renewable_score": 0.563,
}


class _MockResult:
    def mappings(self):
        return self

    def first(self):
        return SAMPLE_ENERGY


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


def test_get_energy_latest_status_200():
    response = client.get("/api/energy/latest")
    assert response.status_code == 200


def test_get_energy_latest_fields():
    response = client.get("/api/energy/latest")
    data = response.json()
    assert "wind_mw" in data
    assert "solar_mw" in data
    assert "renewable_score" in data
    assert "datetime" in data


def test_get_energy_latest_values():
    response = client.get("/api/energy/latest")
    data = response.json()
    assert data["wind_mw"] == 1823.4
    assert data["renewable_score"] == 0.563
