"""Integration tests for Antigravity FastAPI REST API."""

import pytest
from fastapi.testclient import TestClient
from antigravity.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["orbital_engine"] == "running"


def test_ingest_endpoint():
    payload = {
        "source": "github_actions",
        "stage": "ci.unit-tests",
        "status": "success",
        "duration_seconds": 184.0,
        "queue_seconds": 30.0,
        "repo": "your-org/service-a",
        "commit_sha": "abc1234",
    }
    response = client.post("/v1/ingest", json=payload)
    assert response.status_code == 202
    data = response.json()
    assert data["status"] == "accepted"


def test_field_rank_endpoint():
    response = client.get("/v1/field/rank?scope=repo&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "field" in data
    assert isinstance(data["field"], list)
    if data["field"]:
        first = data["field"][0]
        assert "well" in first
        assert "drag_coefficient" in first


def test_orbital_state_endpoint():
    response = client.get("/v1/orbital-state?scope=org")
    assert response.status_code == 200
    data = response.json()
    assert data["scope"] == "org"
    assert "current_velocity" in data
    assert "escape_velocity_target" in data
    assert "escape_velocity_ratio" in data
    assert data["status"] in ["SUB_ORBITAL", "APPROACHING", "ESCAPE", "DECAYING"]


def test_thruster_enable_disable():
    res = client.post("/v1/thrusters/test_quarantine/enable", json={"config": {"flake_threshold": 0.12}})
    assert res.status_code == 200
    assert res.json()["enabled"] is True

    res = client.post("/v1/thrusters/test_quarantine/disable")
    assert res.status_code == 200
    assert res.json()["enabled"] is False


def test_metrics_prometheus_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "antigravity_orbital_velocity_ratio" in response.text


def test_dashboard_endpoint():
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "Antigravity Delivery Engine" in response.text
