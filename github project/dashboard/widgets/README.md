# Antigravity Dashboard Widgets

This directory provides component integration patterns for embedding Antigravity velocity metrics and drag rankings into internal developer portals such as **Backstage**, **Compass**, or custom React frontends.

## Embedded Web Dashboard

Antigravity includes a self-hosted, zero-configuration HTML5 dashboard served directly by FastAPI at:
```
http://localhost:8000/dashboard
```

## API Consumption Pattern

You can fetch live telemetry for your portal via standard REST endpoints:

- **Orbital State & Escape Velocity**:
  ```http
  GET /v1/orbital-state?scope=org
  ```

- **Top Gravity Wells**:
  ```http
  GET /v1/field/rank?scope=repo&target=my-service&limit=5
  ```

- **Audit Log**:
  ```http
  GET /v1/audit/log?limit=10
  ```
