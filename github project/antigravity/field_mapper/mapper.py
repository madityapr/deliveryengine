"""Field mapper module for attributing delivery latency and mapping gravity wells."""

from collections import defaultdict
from typing import Dict, List, Optional
from datetime import datetime, timezone
from antigravity.models import GravityWell, DragVector, GravitationalField, RawEvent
from antigravity.metrics import compute_drag, compute_drag_coefficients


class FieldMapper:
    """Aggregates raw events into DragVectors, ranks GravityWells, and maps the Gravitational Field."""

    def __init__(self):
        self._history: Dict[str, float] = {}  # well_id -> previous drag magnitude

    def process_events(
        self,
        events: List[RawEvent],
        scope: str = "repo",
        target: Optional[str] = None,
    ) -> GravitationalField:
        """Processes raw events into a ranked GravitationalField."""
        # Filter by scope/target if provided
        filtered = [
            e for e in events
            if target is None or e.repo == target
        ]

        if not filtered:
            return GravitationalField(scope=scope, target=target, wells=[], total_drag=0.0)

        # Group by (repo, stage)
        grouped: Dict[tuple, List[RawEvent]] = defaultdict(list)
        for e in filtered:
            grouped[(e.repo, e.stage)].append(e)

        wells: List[GravityWell] = []

        for (repo, stage), stage_events in grouped.items():
            well_id = f"{stage}"
            count = len(stage_events)
            if count == 0:
                continue

            # Queue wait time in minutes
            w_q = sum(e.queue_seconds for e in stage_events) / (count * 60.0)
            # Service / execution time in minutes
            w_s = sum(e.duration_seconds for e in stage_events) / (count * 60.0)
            # Failure rate
            failures = sum(1 for e in stage_events if e.status in ("failure", "flaky", "error"))
            p_fail = failures / count

            drag = compute_drag(w_q=w_q, w_s=w_s, p_fail=p_fail)

            # Determine trend compared to historical drag
            prev_drag = self._history.get(well_id, drag)
            if prev_drag > 0:
                diff_pct = ((drag - prev_drag) / prev_drag) * 100.0
                if diff_pct > 3.0:
                    trend = f"+{int(diff_pct)}%"
                elif diff_pct < -3.0:
                    trend = f"{int(diff_pct)}%"
                else:
                    trend = "0%"
            else:
                trend = "0%"

            self._history[well_id] = drag

            wells.append(
                GravityWell(
                    id=well_id,
                    stage=stage,
                    repo=repo,
                    w_q=round(w_q, 1),
                    w_s=round(w_s, 1),
                    p_fail=round(p_fail, 2),
                    drag_magnitude=round(drag, 1),
                    trend=trend,
                    last_updated=datetime.now(timezone.utc),
                )
            )

        # Rank wells descending by drag magnitude
        wells.sort(key=lambda w: w.drag_magnitude, reverse=True)

        # Compute normalized Drag Coefficients (Cd)
        compute_drag_coefficients(wells)

        total_drag = sum(w.drag_magnitude for w in wells)

        return GravitationalField(
            scope=scope,
            target=target,
            wells=wells,
            total_drag=round(total_drag, 1),
            timestamp=datetime.now(timezone.utc),
        )

    def extract_drag_vectors(self, field: GravitationalField) -> List[DragVector]:
        """Extracts DragVector instances from mapped wells for time-series persistence."""
        vectors: List[DragVector] = []
        for well in field.wells:
            vectors.append(
                DragVector(
                    well_id=well.id,
                    magnitude=well.drag_magnitude,
                    source="field_mapper",
                    stage=well.stage,
                    repo=well.repo,
                )
            )
        return vectors
