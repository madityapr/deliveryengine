"""Unit tests for Sensors."""

import pytest
import hmac
import hashlib
from antigravity.sensors.mock import MockSensor
from antigravity.sensors.github import GitHubSensor


@pytest.mark.asyncio
async def test_mock_sensor_collect():
    sensor = MockSensor()
    events = await sensor.collect()
    assert len(events) >= 3
    stages = [e.stage for e in events]
    assert "ci.integration-tests" in stages
    assert "ci.docker-build" in stages


def test_github_sensor_hmac_verification():
    secret = "super-secret-key"
    sensor = GitHubSensor({"webhook_secret": secret})
    payload = b'{"action": "completed"}'
    valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()

    assert sensor.verify_webhook_signature(payload, valid_sig) is True
    assert sensor.verify_webhook_signature(payload, "sha256=invalid") is False


def test_github_sensor_workflow_job_parsing():
    sensor = GitHubSensor()
    payload = {
        "action": "completed",
        "workflow_job": {
            "name": "integration-tests",
            "conclusion": "success",
            "head_sha": "c0ffee123",
            "run_id": 9988,
        },
        "repository": {"full_name": "org/repo-a"},
    }
    event = sensor.parse_workflow_job_webhook(payload)
    assert event is not None
    assert event.stage == "ci.integration-tests"
    assert event.status == "success"
    assert event.commit_sha == "c0ffee123"
