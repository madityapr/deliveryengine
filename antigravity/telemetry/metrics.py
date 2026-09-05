"""Prometheus metric generation and batch metric calculation."""

from typing import Dict, List
from antigravity.models import GravityWell, OrbitalState
from antigravity.metrics import compute_fix_at_k, compute_osi


class MetricsService:
    """Manages telemetry calculations and Prometheus-compatible exports."""

    def __init__(self):
        pass

    def generate_prometheus_metrics(
        self,
        wells: List[GravityWell],
        orbital_state: OrbitalState,
        fix_at_k_map: Dict[int, float],
    ) -> str:
        """Generates Prometheus text-format metrics."""
        lines = [
            "# HELP antigravity_orbital_velocity_ratio Current escape velocity ratio",
            "# TYPE antigravity_orbital_velocity_ratio gauge",
            f'antigravity_orbital_velocity_ratio{{scope="{orbital_state.scope}"}} {orbital_state.escape_velocity_ratio}',
            "",
            "# HELP antigravity_orbit_stability_index Stability of delivery velocity",
            "# TYPE antigravity_orbit_stability_index gauge",
            f'antigravity_orbit_stability_index{{scope="{orbital_state.scope}"}} {orbital_state.osi}',
            "",
            "# HELP antigravity_drag_coefficient Normalized drag coefficient per gravity well",
            "# TYPE antigravity_drag_coefficient gauge",
        ]

        for w in wells:
            lines.append(
                f'antigravity_drag_coefficient{{well="{w.id}",repo="{w.repo}",stage="{w.stage}"}} {w.drag_coefficient}'
            )

        lines.extend([
            "",
            "# HELP antigravity_drag_magnitude Raw cost-weighted drag magnitude (minutes)",
            "# TYPE antigravity_drag_magnitude gauge",
        ])
        for w in wells:
            lines.append(
                f'antigravity_drag_magnitude{{well="{w.id}",repo="{w.repo}",stage="{w.stage}"}} {w.drag_magnitude}'
            )

        lines.extend([
            "",
            "# HELP antigravity_fix_at_k Remediation confidence metric Fix@k",
            "# TYPE antigravity_fix_at_k gauge",
        ])
        for k, val in fix_at_k_map.items():
            lines.append(f'antigravity_fix_at_k{{k="{k}"}} {val}')

        lines.append("")
        return "\n".join(lines)

    def recompute_metric(self, metric_name: str, **kwargs) -> Dict[str, any]:
        """Recomputes a specific metric on demand."""
        name = metric_name.lower().replace("-", "_")
        if name == "fix_at_k":
            n = kwargs.get("n", 200)
            c = kwargs.get("c", 150)
            k_values = kwargs.get("k_values", [1, 3, 5])
            results = {f"Fix@{k}": compute_fix_at_k(n, c, k) for k in k_values}
            return {
                "metric": "fix_at_k",
                "sample_size": n,
                "successes": c,
                "results": results,
            }
        elif name in ("osi", "orbit_stability_index"):
            history = kwargs.get("history", [2.5, 2.7, 2.4, 2.6, 2.8, 2.5, 2.6])
            osi = compute_osi(history)
            return {"metric": "osi", "value": osi, "samples": len(history)}
        else:
            return {"error": f"Unknown metric: {metric_name}"}
