# Antigravity System Architecture

Antigravity models engineering pipelines as physical systems subject to drag ("gravity") and applies automated, measurable counterforces ("thrust") to achieve and sustain **escape velocity**.

```
 ┌────────────┐   ┌────────────────────┐   ┌───────────────────┐   ┌─────────────┐
 │  Sensors   │──▶│ Gravity Field       │──▶│ Thrust Engine      │──▶│ Telemetry & │
 │ (collectors)│   │ Mapper (analysis)   │   │ (interventions)    │   │ Metrics Store│
 └────────────┘   └────────────────────┘   └───────────────────┘   └─────────────┘
        ▲                                                                  │
        │                                                                  ▼
        │                                                          ┌───────────────┐
        └──────────────────────── feedback loop ────────────────── │ Dashboard / API│
                                                                   └───────────────┘
```

## 1. Sensors Layer (`antigravity/sensors/`)
Collectors that poll or receive webhooks from CI/CD, VCS, and issue trackers.
- `MockSensor`: Standalone offline event generator for testing.
- `GitHubSensor`: Webhook and API collector for GitHub Actions workflows.
- Extensible via `BaseSensor` protocol.

## 2. Field Mapper (`antigravity/field_mapper/`)
Aggregates raw latency and retry events into cost-weighted `GravityWell`s.
- Computes $W_q$ (queue wait), $W_s$ (service time), and $P_{\text{fail}}$ (failure rate).
- Computes drag magnitude:
  $$D(w, t) = W_q(w, t) + W_s(w, t) \cdot P_{\text{fail}}(w, t)$$
- Normalizes Drag Coefficient $C_d \in [0, 1]$.

## 3. Thrust Engine (`antigravity/thrust_engine/`)
Pluggable remediation runtime:
- Dispatches remediation actions (`test_quarantine`, `cache_warmer`, `review_router`).
- Manages concurrency and idempotency windows `(well_id, thruster_name, window)`.
- Enforces dry-run simulation mode.
- Circuit breaker auto-disables thrusters if $Fix@1 < 0.30$ over 20 runs.

## 4. Telemetry & Storage (`antigravity/telemetry/`)
- Universal local SQLite store (zero cost, zero configuration).
- TimescaleDB / PostgreSQL support for enterprise deployments.
- Immutable WORM-style thrust audit log (`thrust_audit_log`).
- Prometheus `/metrics` exporter.

## 5. API & UI (`antigravity/api/`)
- FastAPI REST service (`/v1/health`, `/v1/field/rank`, `/v1/orbital-state`, `/v1/ingest`).
- Real-time embedded HTML5 dashboard at `/dashboard`.
