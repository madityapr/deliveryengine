"""Unit tests for ThrustEngine and Thrusters."""

import pytest
import asyncio
from antigravity.models import GravityWell, GravitationalField
from antigravity.thrust_engine.engine import ThrustEngine
from antigravity.thrust_engine.registry import ThrusterRegistry
from antigravity.thrust_engine.thrusters.test_quarantine import TestQuarantineThruster
from antigravity.thrust_engine.thrusters.cache_warmer import CacheWarmerThruster
from antigravity.thrust_engine.thrusters.review_router import ReviewRouterThruster


@pytest.mark.asyncio
async def test_test_quarantine_applies_and_fires():
    thruster = TestQuarantineThruster({"flake_threshold": 0.15})
    flaky_well = GravityWell(
        id="ci.integration-tests",
        stage="ci.integration-tests",
        p_fail=0.20,
        w_s=40.0,
    )
    stable_well = GravityWell(
        id="ci.unit-tests",
        stage="ci.unit-tests",
        p_fail=0.02,
        w_s=5.0,
    )

    assert thruster.applies_to(flaky_well) is True
    assert thruster.applies_to(stable_well) is False

    event = await thruster.fire(flaky_well)
    assert event.action == "quarantine_flaky_test"
    assert event.status == "SUCCESS"
    assert event.delta_v > 0


@pytest.mark.asyncio
async def test_thrust_engine_dry_run():
    registry = ThrusterRegistry()
    engine = ThrustEngine(registry=registry, dry_run=True)
    well = GravityWell(
        id="ci.integration-tests",
        stage="ci.integration-tests",
        p_fail=0.25,
        w_s=30.0,
    )

    event = await engine.execute_thruster_for_well("test_quarantine", well)
    assert event.status == "DRY_RUN"
    assert event.details.get("dry_run") is True


@pytest.mark.asyncio
async def test_circuit_breaker():
    registry = ThrusterRegistry()
    engine = ThrustEngine(registry=registry, dry_run=False)
    well = GravityWell(
        id="ci.test-failing",
        stage="ci.test-failing",
        p_fail=0.30,
        w_s=10.0,
    )

    # Force 20 failure attempts into execution history
    key = (well.id, "test_quarantine")
    engine._execution_history[key] = [False] * 20

    is_tripped = engine.check_circuit_breaker(well.id, "test_quarantine")
    assert is_tripped is True

    # Next execution must return circuit breaker tripped
    event = await engine.execute_thruster_for_well("test_quarantine", well)
    assert event.status == "CIRCUIT_BREAKER_TRIPPED"
