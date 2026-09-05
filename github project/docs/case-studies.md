# Case Studies & Operational Scenarios

## Case Study 1: Mid-size SaaS Monorepo (40 Engineers)

- **Challenge**: Deploys stalled at ~1/day with 9-hour median lead time. Anecdotal blame was placed on review bottlenecks.
- **Diagnostics**: `antigravity field rank --scope org --window 14d` revealed:
  1. `ci.integration-tests` ($C_d = 1.00, P_{\text{fail}} = 0.24$)
  2. `review.approval-queue` ($C_d = 0.71, P_{\text{fail}} = 0.04$)
  3. `ci.docker-build` ($C_d = 0.38, P_{\text{fail}} = 0.02$)
- **Action**: Enabled `test_quarantine` (flake_threshold 0.15) and cache pre-warming.
- **Outcome**:
  - `Fix@3` = 0.93
  - Deploys/day: 1.0 → 2.4
  - Lead time: 9.0h → 4.6h
  - EVR: 0.33 → 0.80 (`APPROACHING`)

## Case Study 2: Regulated FinTech Compliance Gates

- **Challenge**: Compliance required mandatory 2-person sign-off on approvals. The gate could not be automated away.
- **Action**: Enabled `review_router` thruster to automatically re-assign stale approval requests idle > 4 hours to secondary approver pools.
- **Outcome**: Orbit Stability Index (OSI) improved from 0.52 to 0.81 without weakening compliance controls.
