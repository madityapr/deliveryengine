"""Unit tests for the Fix@k remediation metric, matching Section 6.1 hand-worked example."""

import pytest
from antigravity.metrics import (
    compute_fix_at_k,
    compute_drag,
    compute_drag_coefficients,
    compute_escape_velocity_ratio,
    compute_orbital_status,
    compute_osi,
    compute_lift_coefficient,
)
from antigravity.models import GravityWell, OrbitalStatus


def test_fix_at_k_worked_example():
    """Verify exact values from README.md Section 6.1:
    n = 200, c = 150
    Fix@1 = 1 - C(50,1)/C(200,1) = 0.75
    Fix@3 = 1 - C(50,3)/C(200,3) ≈ 0.985
    """
    n = 200
    c = 150

    fix_1 = compute_fix_at_k(n, c, 1)
    assert pytest.approx(fix_1, abs=1e-4) == 0.75

    fix_3 = compute_fix_at_k(n, c, 3)
    # 1 - (50*49*48) / (200*199*198) = 1 - 117600 / 7880400 = 1 - 0.014923... ≈ 0.985
    assert pytest.approx(fix_3, abs=1e-3) == 0.985


def test_fix_at_k_boundary_conditions():
    # 0 successes
    assert compute_fix_at_k(100, 0, 1) == 0.0
    assert compute_fix_at_k(100, 0, 5) == 0.0

    # 100% successes
    assert compute_fix_at_k(100, 100, 1) == 1.0
    assert compute_fix_at_k(100, 100, 5) == 1.0

    # When remaining failures is less than k: certain success
    # n=10, c=9 (only 1 failure). For k=2, choosing 2 failures is impossible, so Fix@2 = 1.0
    assert compute_fix_at_k(10, 9, 2) == 1.0

    # Invalid / zero inputs
    assert compute_fix_at_k(0, 0, 1) == 0.0
    assert compute_fix_at_k(50, 20, 0) == 0.0


def test_drag_equation():
    """Verify D(w, t) = W_q + W_s * P_fail."""
    # w_q = 10, w_s = 30, p_fail = 0.2 -> 10 + 30 * 0.2 = 16.0
    drag = compute_drag(w_q=10.0, w_s=30.0, p_fail=0.2)
    assert drag == 16.0


def test_drag_coefficient_normalization():
    wells = [
        GravityWell(id="w1", stage="s1", drag_magnitude=50.0),
        GravityWell(id="w2", stage="s2", drag_magnitude=25.0),
        GravityWell(id="w3", stage="s3", drag_magnitude=0.0),
    ]
    compute_drag_coefficients(wells)
    assert wells[0].drag_coefficient == 1.0
    assert wells[1].drag_coefficient == 0.5
    assert wells[2].drag_coefficient == 0.0


def test_escape_velocity_ratio_and_status():
    # Section 5.3: current=2.1, target=3.0 -> EVR = 0.70
    evr = compute_escape_velocity_ratio(2.1, 3.0)
    assert evr == 0.70

    status = compute_orbital_status(evr)
    assert status == OrbitalStatus.SUB_ORBITAL

    # Approaching
    assert compute_orbital_status(0.90) == OrbitalStatus.APPROACHING

    # Escape sustained
    assert compute_orbital_status(1.10, sustained_days=14) == OrbitalStatus.ESCAPE


def test_orbit_stability_index():
    # Perfectly stable
    stable_series = [3.0, 3.0, 3.0, 3.0]
    assert compute_osi(stable_series) == 1.0

    # Erratic
    erratic_series = [1.0, 5.0, 1.0, 5.0]
    osi = compute_osi(erratic_series)
    assert 0.0 <= osi < 0.8
