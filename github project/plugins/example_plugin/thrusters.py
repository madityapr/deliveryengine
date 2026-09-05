"""Example custom thruster plugin matching Section 8.2 in README.md."""

from typing import Any
from antigravity.models import GravityWell, ThrustEvent
from antigravity.thrust_engine.thrusters.base import BaseThruster


class CustomCacheWarmerThruster(BaseThruster):
    """Custom thruster plugin example."""

    name: str = "custom_cache_warmer"
    write_scope: str = "ci:cache_prewarm"

    def applies_to(self, well: GravityWell) -> bool:
        return well.stage == "ci.docker-build" and well.drag_coefficient > 0.3

    async def fire(self, well: GravityWell, ctx: Any = None) -> ThrustEvent:
        return ThrustEvent(
            thruster=self.name,
            well_id=well.id,
            action="prewarm_cache",
            delta_v=12.5,
            status="SUCCESS",
            details={"plugin": "example_plugin"},
        )
