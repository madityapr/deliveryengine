"""Immutable thrust audit log operations."""

from typing import Any, Dict, List, Optional
from antigravity.telemetry.db import TelemetryStore
from antigravity.models import ThrustEvent


class AuditLogger:
    """Provides append-only immutable audit logging for all thruster actions."""

    def __init__(self, store: Optional[TelemetryStore] = None):
        self.store = store or TelemetryStore()

    def log_thrust_event(self, event: ThrustEvent):
        self.store.record_thrust_event(event)

    def get_logs(self, limit: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.store.get_audit_log(limit=limit, since=since)
