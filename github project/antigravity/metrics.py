"""Mathematical formulations and evaluation metrics for Antigravity."""

import math
import statistics
from typing import List, Optional
from antigravity.models import GravityWell, OrbitalStatus


def compute_fix_at_k(n: int, c: int, k: int) -> float:
    """Computes the Fix@k remediation confidence metric (analogue to pass@k).
    
    Formula:
        Fix@k = 1 - C(n - c, k) / C(n, k)
    
    Where:
        n = total number of independent remediation attempts
        c = number of successful attempts
        k = number of attempts considered per trial
        C(a, b) = binomial coefficient (a choose b)
        
    Example:
        n = 200, c = 150
        Fix@1 = 1 - C(50, 1) / C(200, 1) = 1 - 50/200 = 0.75
        Fix@3 = 1 - C(50, 3) / C(200, 3) = 1 - 19600 / 1313400 ≈ 0.985
    """
    if n <= 0 or k <= 0:
        return 0.0
    if c <= 0:
        return 0.0
    if c >= n:
        return 1.0
    if n - c < k:
        return 1.0
    if k > n:
        return 1.0 if c > 0 else 0.0

    try:
        combinations_fail = math.comb(n - c, k)
        combinations_total = math.comb(n, k)
        if combinations_total == 0:
            return 0.0
        return float(1.0 - (combinations_fail / combinations_total))
    except (ValueError, OverflowError):
        return 0.0


def compute_drag(w_q: float, w_s: float, p_fail: float) -> float:
    """Computes drag magnitude for a gravity well.
    
    Formula:
        D(w, t) = W_q(w, t) + W_s(w, t) * P_fail(w, t)
        
    Where:
        W_q = average queue wait time
        W_s = average service execution time
        P_fail = empirical failure or retry probability [0.0 - 1.0]
    """
    p_clamped = max(0.0, min(1.0, p_fail))
    return float(w_q + (w_s * p_clamped))


def compute_drag_coefficients(wells: List[GravityWell]) -> List[GravityWell]:
    """Computes normalized Drag Coefficient Cd(w) = D(w, t) / D_max(field, t).
    
    Updates the drag_coefficient attribute on each well in-place and returns the list.
    """
    if not wells:
        return []
    
    max_drag = max((w.drag_magnitude for w in wells), default=0.0)
    
    for well in wells:
        if max_drag > 0:
            well.drag_coefficient = round(well.drag_magnitude / max_drag, 2)
        else:
            well.drag_coefficient = 0.0
            
    return wells


def compute_escape_velocity_ratio(
    current_deploys: float,
    target_deploys: float,
    current_lead_time: Optional[float] = None,
    target_lead_time: Optional[float] = None,
) -> float:
    """Computes the Escape Velocity Ratio (EVR).
    
    Primary signal is throughput velocity ratio (deploys / target_deploys).
    """
    if target_deploys <= 0:
        return 0.0
    ratio = current_deploys / target_deploys
    return round(float(ratio), 2)


def compute_orbital_status(
    evr: float,
    sustained_days: int = 0,
    is_decaying: bool = False,
) -> OrbitalStatus:
    """Determines the orbital status based on EVR and duration.
    
    Status thresholds:
        - SUB_ORBITAL: < 0.85 EVR
        - APPROACHING: 0.85 - 0.99 EVR
        - ESCAPE: >= 1.0 EVR sustained >= 14 days
        - DECAYING: Trending down >= 10% over 2 weeks after ESCAPE
    """
    if is_decaying:
        return OrbitalStatus.DECAYING
    if evr >= 1.0 and sustained_days >= 14:
        return OrbitalStatus.ESCAPE
    elif evr >= 0.85:
        return OrbitalStatus.APPROACHING
    else:
        return OrbitalStatus.SUB_ORBITAL


def compute_osi(velocity_series: List[float]) -> float:
    """Computes the Orbit Stability Index (OSI).
    
    Formula:
        OSI = 1 - stddev(v, 14d) / mean(v, 14d)
        
    Near 1 = stable, near 0 = erratic.
    """
    if not velocity_series or len(velocity_series) < 2:
        return 1.0
    
    mean_v = statistics.mean(velocity_series)
    if mean_v <= 0:
        return 0.0
        
    stdev_v = statistics.stdev(velocity_series)
    osi = 1.0 - (stdev_v / mean_v)
    return round(max(0.0, min(1.0, float(osi))), 2)


def compute_lift_coefficient(delta_vs: List[float], drag_magnitudes: List[float]) -> float:
    """Computes Lift Coefficient (Cl) = Σ delta_v / Σ drag_magnitude.
    
    Fraction of total measured drag neutralized in a period.
    """
    total_drag = sum(drag_magnitudes)
    if total_drag <= 0:
        return 0.0
    total_lift = sum(delta_vs)
    return round(float(total_lift / total_drag), 2)
