"""
Integration Tests for EcoPulse Flask Application
Tests route handlers, API endpoints, persistence, health check, and error responses.
"""

import json
import pytest
from app import create_app
from config import TestConfig
import database as db

@pytest.fixture
def client(tmp_path):
    """Fixture providing a configured test client with an isolated SQLite database."""
    test_db = str(tmp_path / "test_ecopulse.db")

    class IsolatedConfig(TestConfig):
        DATABASE_PATH = test_db

    app = create_app(IsolatedConfig)
    app.config["TESTING"] = True

    with app.test_client() as test_client:
        with app.app_context():
            db.init_db(test_db)
        yield test_client

def test_home_page(client):
    """Verify home page loads successfully with 200 OK and expected DOM tags."""
    response = client.get("/")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "EcoPulse" in html
    assert "EARTH VIEW" in html
    assert "BREAKDOWN" in html
    assert "CARBON FOOTPRINT" in html
    assert "METRICS" in html

def test_about_page(client):
    """Verify about page loads successfully."""
    response = client.get("/about")
    assert response.status_code == 200
    html = response.data.decode("utf-8")
    assert "SYSTEM ARCHITECTURE &amp; METHODOLOGY" in html or "SYSTEM ARCHITECTURE & METHODOLOGY" in html
    assert "DOCUMENTED EMISSION FACTORS" in html

def test_healthz_endpoint(client):
    """Verify health-check endpoint returns 200 OK with healthy database status."""
    response = client.get("/healthz")
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data["status"] == "healthy"
    assert data["service"] == "ecopulse"
    assert data["database"] == "connected"

def test_api_entries_lifecycle(client):
    """Test full CRUD lifecycle: create, list, retrieve, update, delete."""
    # 1. Initial list should be empty
    res_list = client.get("/api/entries")
    assert res_list.status_code == 200
    data_list = json.loads(res_list.data)
    assert data_list["count"] == 0

    # 2. Create first entry
    payload = {
        "title": "Initial Baseline",
        "vehicle_miles_per_week": 160.0,
        "vehicle_mpg": 32.0,
        "vehicle_maintenance": True,
        "transit_miles_per_week": 25.0,
        "flights_per_year": 1.0,
        "electricity_kwh_per_month": 380.0,
        "clean_energy_pct": 10.0,
        "heating_units_per_month": 20.0,
        "waste_bags_per_week": 2.0,
        "recycling_habit": "regularly",
        "composting_habit": True,
        "diet_habit": "average",
        "shopping_habit": "average",
        "reusable_habit": True
    }
    res_create = client.post("/api/entries", json=payload)
    assert res_create.status_code == 201
    created_entry = json.loads(res_create.data)["entry"]
    entry_id = created_entry["id"]
    assert entry_id is not None
    assert created_entry["title"] == "Initial Baseline"
    assert created_entry["total_tonnes"] > 0

    # 3. Retrieve by ID
    res_get = client.get(f"/api/entries/{entry_id}")
    assert res_get.status_code == 200
    entry_details = json.loads(res_get.data)["entry"]
    assert entry_details["id"] == entry_id
    assert "calculations" in entry_details

    # 4. Update the entry (e.g. user increased car usage)
    updated_payload = dict(payload, vehicle_miles_per_week=300.0)
    res_update = client.put(f"/api/entries/{entry_id}", json=updated_payload)
    assert res_update.status_code == 200
    updated_entry = json.loads(res_update.data)["entry"]
    assert updated_entry["total_tonnes"] > created_entry["total_tonnes"]

    # 5. History should now reflect the updated entry
    res_hist = client.get("/api/history")
    assert res_hist.status_code == 200
    hist_data = json.loads(res_hist.data)
    assert len(hist_data["history"]) == 1
    assert hist_data["history"][0]["id"] == entry_id

    # 6. Delete the entry
    res_del = client.delete(f"/api/entries/{entry_id}")
    assert res_del.status_code == 200

    # 7. Confirm deletion
    res_get_deleted = client.get(f"/api/entries/{entry_id}")
    assert res_get_deleted.status_code == 404

def test_api_entries_validation_failure(client):
    """Verify malformed input receives 400 Bad Request with field-level errors."""
    bad_payload = {
        "vehicle_miles_per_week": -100,
        "clean_energy_pct": 120
    }
    response = client.post("/api/entries", json=bad_payload)
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["success"] is False
    assert "vehicle_miles_per_week" in data["errors"]

def test_api_calculate_preview(client):
    """Verify calculation preview does not require writing to database."""
    preview_data = {
        "vehicle_miles_per_week": 200,
        "vehicle_mpg": 30
    }
    response = client.post("/api/calculate", json=preview_data)
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "calculations" in data
    assert data["calculations"]["total_tonnes"] > 0
