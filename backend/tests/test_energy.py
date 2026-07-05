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

SAMPLE_TIMESERIES = [
    {"datetime": "2026-04-24T00:00:00+00:00", "wind_mw": 1200.0, "solar_mw": 3.0, "total_demand_mw": 3000.0, "renewable_score": 0.401},
    {"datetime": "2026-04-25T00:00:00+00:00", "wind_mw": 1400.0, "solar_mw": 5.0, "total_demand_mw": 3100.0, "renewable_score": 0.452},
]


class _MockResult:
    def __init__(self, many=False):
        self._many = many

    def mappings(self):
        return self

    def first(self):
        return SAMPLE_ENERGY

    def all(self):
        return SAMPLE_TIMESERIES


class _MockSession:
    async def execute(self, query, params=None):
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


# --- timeseries ---

def test_timeseries_default_200():
    response = client.get("/api/energy/timeseries")
    assert response.status_code == 200


def test_timeseries_returns_list():
    response = client.get("/api/energy/timeseries")
    assert isinstance(response.json(), list)


def test_timeseries_fields():
    response = client.get("/api/energy/timeseries")
    row = response.json()[0]
    for field in ("datetime", "wind_mw", "solar_mw", "total_demand_mw", "renewable_score"):
        assert field in row


def test_timeseries_days_7_interval_1h():
    response = client.get("/api/energy/timeseries?days=7&interval=1h")
    assert response.status_code == 200


def test_timeseries_days_30_interval_1d():
    response = client.get("/api/energy/timeseries?days=30&interval=1d")
    assert response.status_code == 200


def test_timeseries_all_interval_1d():
    response = client.get("/api/energy/timeseries?days=all&interval=1d")
    assert response.status_code == 200


def test_timeseries_invalid_interval():
    response = client.get("/api/energy/timeseries?interval=5m")
    assert response.status_code == 400


def test_timeseries_all_with_15m_rejected():
    response = client.get("/api/energy/timeseries?days=all&interval=15m")
    assert response.status_code == 400


def test_timeseries_days_30_with_15m_rejected():
    response = client.get("/api/energy/timeseries?days=30&interval=15m")
    assert response.status_code == 400


def test_timeseries_days_100_with_1h_rejected():
    response = client.get("/api/energy/timeseries?days=100&interval=1h")
    assert response.status_code == 400


def test_timeseries_invalid_days():
    response = client.get("/api/energy/timeseries?days=abc")
    assert response.status_code == 400
