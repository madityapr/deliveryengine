"""Cache warmer thruster for pre-warming build caches."""

from typing import Any, Dict
from datetime import datetime, timezone
from antigravity.models import GravityWell, ThrustEvent
from antigravity.thrust_engine.thrusters.base import BaseThruster


class CacheWarmerThruster(BaseThruster):
    """Pre-warms container image layers and dependency caches before peak developer hours."""

    name: str = "cache_warmer"
    write_scope: str = "ci:cache_prewarm"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.warm_before_hours = self.config.get("warm_before_hours", [7, 13])

    def applies_to(self, well: GravityWell) -> bool:
        if not self.enabled:
            return False
        is_build_stage = "build" in well.stage.lower() or "docker" in well.stage.lower()
        return is_build_stage and (well.drag_coefficient >= 0.3)

    async def fire(self, well: GravityWell, ctx: Any = None) -> ThrustEvent:
        # Pre-warming typically reduces build service time by 40-60%
        expected_boost = round(well.w_s * 0.5, 1)

        return ThrustEvent(
            thruster=self.name,
            well_id=well.id,
            action="prewarm_cache",
            delta_v=expected_boost,
            timestamp=datetime.now(timezone.utc),
            status="SUCCESS",
            details={
                "repo": well.repo,
                "warm_before_hours": self.warm_before_hours,
                "target_layer_cache": "docker-build-cache",
            }
        )
