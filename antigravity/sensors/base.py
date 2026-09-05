"""Base sensor definitions and abstract classes."""

from abc import ABC, abstractmethod
from typing import List
from antigravity.models import RawEvent


class BaseSensor(ABC):
    """Abstract base class for all Antigravity telemetry collectors."""
    
    name: str = "base_sensor"

    def __init__(self, config: dict = None):
        self.config = config or {}

    @abstractmethod
    async def collect(self) -> List[RawEvent]:
        """Collects raw pipeline or telemetry events."""
        pass
