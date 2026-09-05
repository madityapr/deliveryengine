"""Base thruster abstractions and interfaces."""

from abc import ABC, abstractmethod
from typing import Any, Dict
from antigravity.models import GravityWell, ThrustEvent


class BaseThruster(ABC):
    """Abstract base class for all pluggable remediation thrusters."""

    name: str = "base_thruster"
    write_scope: str = "read"  # e.g., 'ci:quarantine', 'review:reassign', 'cache:prewarm'
    enabled: bool = True

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.enabled = self.config.get("enabled", True)

    @abstractmethod
    def applies_to(self, well: GravityWell) -> bool:
        """Determines whether this thruster is suitable for counteracting the given GravityWell."""
        pass

    @abstractmethod
    async def fire(self, well: GravityWell, ctx: Any = None) -> ThrustEvent:
        """Executes the remediation action against the gravity well."""
        pass
