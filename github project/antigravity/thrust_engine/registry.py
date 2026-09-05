"""Registry for managing and dynamically discovering thruster plugins."""

from typing import Dict, List, Optional
from antigravity.thrust_engine.thrusters.base import BaseThruster
from antigravity.thrust_engine.thrusters.test_quarantine import TestQuarantineThruster
from antigravity.thrust_engine.thrusters.cache_warmer import CacheWarmerThruster
from antigravity.thrust_engine.thrusters.review_router import ReviewRouterThruster


class ThrusterRegistry:
    """Manages all registered thruster plugins."""

    def __init__(self):
        self._thrusters: Dict[str, BaseThruster] = {}
        self._register_defaults()

    def _register_defaults(self):
        self.register(TestQuarantineThruster())
        self.register(CacheWarmerThruster())
        self.register(ReviewRouterThruster())

    def register(self, thruster: BaseThruster):
        self._thrusters[thruster.name] = thruster

    def get(self, name: str) -> Optional[BaseThruster]:
        return self._thrusters.get(name)

    def list_all(self) -> List[BaseThruster]:
        return list(self._thrusters.values())

    def enable(self, name: str, config: Optional[dict] = None) -> bool:
        thruster = self._thrusters.get(name)
        if not thruster:
            return False
        thruster.enabled = True
        if config:
            thruster.config.update(config)
            # Re-initialize thresholds if provided
            if hasattr(thruster, "flake_threshold") and "flake_threshold" in config:
                thruster.flake_threshold = float(config["flake_threshold"])
            if hasattr(thruster, "window_runs") and "window_runs" in config:
                thruster.window_runs = int(config["window_runs"])
            if hasattr(thruster, "max_queue_depth") and "max_queue_depth" in config:
                thruster.max_queue_depth = int(config["max_queue_depth"])
        return True

    def disable(self, name: str) -> bool:
        thruster = self._thrusters.get(name)
        if not thruster:
            return False
        thruster.enabled = False
        return True
