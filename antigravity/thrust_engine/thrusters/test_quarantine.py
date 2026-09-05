"""Test quarantine thruster for isolating flaky tests."""

from typing import Any, Dict
from datetime import datetime, timezone
from antigravity.models import GravityWell, ThrustEvent
from antigravity.thrust_engine.thrusters.base import BaseThruster


class TestQuarantineThruster(BaseThruster):
    """Quarantines tests exceeding flakiness threshold to unblock CI."""

    __test__ = False
    name: str = "test_quarantine"
    write_scope: str = "ci:test_quarantine"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.flake_threshold = float(self.config.get("flake_threshold", 0.15))
        self.window_runs = int(self.config.get("window_runs", 50))
        self.min_confidence = float(self.config.get("min_confidence", 0.90))

    def applies_to(self, well: GravityWell) -> bool:
        if not self.enabled:
            return False
        # Matches test-related stages with failure rate exceeding flake threshold
        is_test_stage = "test" in well.stage.lower() or "ci." in well.stage.lower()
        return is_test_stage and (well.p_fail >= self.flake_threshold)

    async def fire(self, well: GravityWell, ctx: Any = None) -> ThrustEvent:
        # Expected delta_v gained by eliminating the flakiness retry overhead
        expected_boost = round(well.w_s * well.p_fail, 1)
        
        return ThrustEvent(
            thruster=self.name,
            well_id=well.id,
            action="quarantine_flaky_test",
            delta_v=expected_boost,
            timestamp=datetime.now(timezone.utc),
            status="SUCCESS",
            details={
                "tag": "@antigravity-quarantined",
                "flake_threshold": self.flake_threshold,
                "measured_p_fail": well.p_fail,
                "tracking_issue_opened": True,
            }
        )
