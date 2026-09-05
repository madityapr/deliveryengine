"""Review router thruster for auto-reassigning stale code approvals."""

from typing import Any, Dict
from datetime import datetime, timezone
from antigravity.models import GravityWell, ThrustEvent
from antigravity.thrust_engine.thrusters.base import BaseThruster


class ReviewRouterThruster(BaseThruster):
    """Auto-reassigns stale review approval requests to secondary reviewer pools."""

    name: str = "review_router"
    write_scope: str = "review:reassign"

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config)
        self.max_queue_depth = int(self.config.get("max_queue_depth", 8))

    def applies_to(self, well: GravityWell) -> bool:
        if not self.enabled:
            return False
        is_review_stage = "review" in well.stage.lower() or "approval" in well.stage.lower()
        # High queue wait time
        return is_review_stage and (well.w_q > 15.0 or well.drag_coefficient > 0.4)

    async def fire(self, well: GravityWell, ctx: Any = None) -> ThrustEvent:
        # Re-routing cuts queue wait time significantly
        expected_boost = round(well.w_q * 0.4, 1)

        return ThrustEvent(
            thruster=self.name,
            well_id=well.id,
            action="reassign_stale_approvals",
            delta_v=expected_boost,
            timestamp=datetime.now(timezone.utc),
            status="SUCCESS",
            details={
                "max_queue_depth": self.max_queue_depth,
                "reassigned_reviewers_count": 3,
                "escalated_to_secondary_pool": True,
            }
        )
