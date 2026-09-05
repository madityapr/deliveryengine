"""Thrust engine orchestration runtime and scheduler."""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from antigravity.models import GravityWell, GravitationalField, ThrustEvent
from antigravity.thrust_engine.registry import ThrusterRegistry
from antigravity.metrics import compute_fix_at_k


class ThrustEngine:
    """Orchestrates thruster evaluations, idempotency, dry-run simulations, and circuit breakers."""

    def __init__(
        self,
        registry: Optional[ThrusterRegistry] = None,
        dry_run: bool = False,
        max_concurrent_thrusters: int = 5,
    ):
        self.registry = registry or ThrusterRegistry()
        self.dry_run = dry_run
        self.max_concurrent_thrusters = max_concurrent_thrusters
        self._fired_windows: Set[str] = set()
        # History: (well_id, thruster_name) -> list of booleans (True = success, False = fail)
        self._execution_history: Dict[tuple, List[bool]] = {}
        self._circuit_broken: Set[tuple] = set()

    def _get_window_key(self, well_id: str, thruster_name: str, window_minutes: int = 5) -> str:
        now = datetime.now(timezone.utc)
        window_idx = int(now.timestamp() // (window_minutes * 60))
        return f"{well_id}:{thruster_name}:{window_idx}"

    def is_circuit_broken(self, well_id: str, thruster_name: str) -> bool:
        return (well_id, thruster_name) in self._circuit_broken

    def check_circuit_breaker(self, well_id: str, thruster_name: str) -> bool:
        """Checks if Fix@1 < 0.3 over last 20 attempts and auto-disables if tripped."""
        key = (well_id, thruster_name)
        history = self._execution_history.get(key, [])
        if len(history) >= 20:
            n = len(history)
            c = sum(1 for success in history if success)
            fix_at_1 = compute_fix_at_k(n, c, 1)
            if fix_at_1 < 0.30:
                self._circuit_broken.add(key)
                return True
        return False

    async def execute_thruster_for_well(
        self,
        thruster_name: str,
        well: GravityWell,
        ctx: Optional[dict] = None,
    ) -> ThrustEvent:
        """Executes a single thruster against a gravity well with safeguards."""
        thruster = self.registry.get(thruster_name)
        if not thruster or not thruster.enabled:
            return ThrustEvent(
                thruster=thruster_name,
                well_id=well.id,
                action="skipped",
                status="SKIPPED",
                details={"reason": "Thruster not found or disabled"},
            )

        # 1. Circuit breaker check
        if self.is_circuit_broken(well.id, thruster_name):
            return ThrustEvent(
                thruster=thruster_name,
                well_id=well.id,
                action="circuit_breaker_tripped",
                status="CIRCUIT_BREAKER_TRIPPED",
                details={"reason": "Fix@1 dropped below 0.3 threshold over 20 runs"},
            )

        # 2. Idempotency window check
        window_key = self._get_window_key(well.id, thruster_name)
        if window_key in self._fired_windows:
            return ThrustEvent(
                thruster=thruster_name,
                well_id=well.id,
                action="idempotency_skip",
                status="SKIPPED",
                details={"reason": "Already fired within current idempotency window"},
            )

        # 3. Dry-run mode
        if self.dry_run:
            event = await thruster.fire(well, ctx)
            event.status = "DRY_RUN"
            event.details["dry_run"] = True
            self._fired_windows.add(window_key)
            return event

        # 4. Live execution
        try:
            event = await thruster.fire(well, ctx)
            event.status = "SUCCESS"
            self._fired_windows.add(window_key)

            # Record success in history
            key = (well.id, thruster_name)
            self._execution_history.setdefault(key, []).append(True)

            return event
        except Exception as e:
            key = (well.id, thruster_name)
            self._execution_history.setdefault(key, []).append(False)
            self.check_circuit_breaker(well.id, thruster_name)

            return ThrustEvent(
                thruster=thruster_name,
                well_id=well.id,
                action="failed",
                status="FAILED",
                details={"error": str(e)},
            )

    async def run_cycle(self, field: GravitationalField) -> List[ThrustEvent]:
        """Runs an evaluation and remediation cycle against the ranked wells in a field."""
        events: List[ThrustEvent] = []
        semaphore = asyncio.Semaphore(self.max_concurrent_thrusters)

        async def run_safe(thruster_name: str, well: GravityWell):
            async with semaphore:
                return await self.execute_thruster_for_well(thruster_name, well)

        tasks = []
        for well in field.wells:
            for thruster in self.registry.list_all():
                if thruster.enabled and thruster.applies_to(well):
                    tasks.append(run_safe(thruster.name, well))

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for res in results:
                if isinstance(res, ThrustEvent):
                    events.append(res)

        return events
