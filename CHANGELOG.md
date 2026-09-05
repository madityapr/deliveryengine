# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-09-05

### Added
- **Core Abstractions**: Implemented `GravityWell`, `DragVector`, `Thruster`, `ThrustEvent`, `OrbitalState`, and `Field` models.
- **Mathematical Formulations**:
  - Unbiased estimator for `Fix@k` remediation confidence metric ($1 - \frac{\binom{n-c}{k}}{\binom{n}{k}}$).
  - Cost-weighted drag equation ($D(w, t) = W_q(w, t) + W_s(w, t) \cdot P_{\text{fail}}(w, t)$).
  - Normalized Drag Coefficient ($C_d(w) = D(w, t) / D_{\max}(field, t)$).
  - Escape Velocity Ratio (EVR) and status tracking (`SUB_ORBITAL`, `APPROACHING`, `ESCAPE`, `DECAYING`).
  - Orbit Stability Index (OSI) and Lift Coefficient ($C_l$).
- **Sensors**: Base sensor protocol, Mock sensor for standalone offline testing, and GitHub Actions / VCS sensor.
- **Field Mapper**: Aggregation engine for ranking drag wells and deriving drag vectors.
- **Thrust Engine**: Scheduler and execution runtime supporting dry-run modes, idempotency keys, and automation circuit breakers.
- **Built-in Thrusters**: `test_quarantine`, `cache_warmer`, and `review_router`.
- **Telemetry & Audit**: Universal SQLite backend with TimescaleDB compatibility, immutable WORM-style thrust audit log.
- **REST API**: FastAPI service serving `/v1/health`, `/v1/ingest`, `/v1/field/rank`, `/v1/orbital-state`, and `/metrics`.
- **Interactive UI**: Embedded lightweight web dashboard for real-time velocity and gravity well inspection.
- **CLI**: Rich Typer CLI with `bootstrap`, `field rank`, `thruster`, `orbital-state`, `metrics recompute`, `plugins list`, and `audit log`.
- **Packaging & Deployment**: `pyproject.toml`, Docker Compose stack, and Kubernetes Helm chart.
