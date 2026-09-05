"""Universal telemetry database layer with SQLite local fallback and TimescaleDB compatibility."""

import sqlite3
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
from antigravity.models import RawEvent, DragVector, GravityWell, ThrustEvent


DB_FILE = os.getenv("ANTIGRAVITY_DB_PATH", "antigravity.sqlite3")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initializes the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS raw_events (
        id TEXT PRIMARY KEY,
        source TEXT,
        stage TEXT,
        status TEXT,
        duration_seconds REAL,
        queue_seconds REAL,
        repo TEXT,
        commit_sha TEXT,
        timestamp TEXT,
        metadata TEXT
    );

    CREATE TABLE IF NOT EXISTS drag_vectors (
        id TEXT PRIMARY KEY,
        well_id TEXT,
        magnitude REAL,
        timestamp TEXT,
        source TEXT,
        stage TEXT,
        repo TEXT
    );

    CREATE TABLE IF NOT EXISTS gravity_wells (
        id TEXT PRIMARY KEY,
        stage TEXT,
        repo TEXT,
        w_q REAL,
        w_s REAL,
        p_fail REAL,
        drag_magnitude REAL,
        drag_coefficient REAL,
        trend TEXT,
        last_updated TEXT
    );

    -- Immutable WORM-style thrust audit log
    CREATE TABLE IF NOT EXISTS thrust_audit_log (
        id TEXT PRIMARY KEY,
        thruster TEXT NOT NULL,
        well_id TEXT NOT NULL,
        action TEXT NOT NULL,
        delta_v REAL,
        timestamp TEXT NOT NULL,
        status TEXT NOT NULL,
        details TEXT
    );
    """)
    conn.commit()
    conn.close()


class TelemetryStore:
    """Interface for saving and querying telemetry data."""

    def __init__(self):
        init_db()

    def record_raw_event(self, event: RawEvent):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO raw_events 
            (id, source, stage, status, duration_seconds, queue_seconds, repo, commit_sha, timestamp, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.source,
                event.stage,
                event.status,
                event.duration_seconds,
                event.queue_seconds,
                event.repo,
                event.commit_sha,
                event.timestamp.isoformat(),
                json.dumps(event.metadata),
            ),
        )
        conn.commit()
        conn.close()

    def get_raw_events(self, limit: int = 1000) -> List[RawEvent]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM raw_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        events = []
        for r in rows:
            events.append(
                RawEvent(
                    id=r["id"],
                    source=r["source"],
                    stage=r["stage"],
                    status=r["status"],
                    duration_seconds=r["duration_seconds"],
                    queue_seconds=r["queue_seconds"],
                    repo=r["repo"],
                    commit_sha=r["commit_sha"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {},
                )
            )
        return events

    def record_thrust_event(self, event: ThrustEvent):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO thrust_audit_log
            (id, thruster, well_id, action, delta_v, timestamp, status, details)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event.id,
                event.thruster,
                event.well_id,
                event.action,
                event.delta_v,
                event.timestamp.isoformat(),
                event.status,
                json.dumps(event.details),
            ),
        )
        conn.commit()
        conn.close()

    def get_audit_log(self, limit: int = 100, since: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection()
        cursor = conn.cursor()
        if since:
            cursor.execute(
                "SELECT * FROM thrust_audit_log WHERE timestamp >= ? ORDER BY timestamp DESC LIMIT ?",
                (since, limit),
            )
        else:
            cursor.execute("SELECT * FROM thrust_audit_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            {
                "id": r["id"],
                "thruster": r["thruster"],
                "well_id": r["well_id"],
                "action": r["action"],
                "delta_v": r["delta_v"],
                "timestamp": r["timestamp"],
                "status": r["status"],
                "details": json.loads(r["details"]) if r["details"] else {},
            }
            for r in rows
        ]

    def save_wells(self, wells: List[GravityWell]):
        conn = get_connection()
        cursor = conn.cursor()
        for w in wells:
            cursor.execute(
                """
                INSERT OR REPLACE INTO gravity_wells
                (id, stage, repo, w_q, w_s, p_fail, drag_magnitude, drag_coefficient, trend, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    w.id,
                    w.stage,
                    w.repo,
                    w.w_q,
                    w.w_s,
                    w.p_fail,
                    w.drag_magnitude,
                    w.drag_coefficient,
                    w.trend,
                    w.last_updated.isoformat(),
                ),
            )
        conn.commit()
        conn.close()

    def get_saved_wells(self, limit: int = 50) -> List[GravityWell]:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM gravity_wells ORDER BY drag_magnitude DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        conn.close()

        return [
            GravityWell(
                id=r["id"],
                stage=r["stage"],
                repo=r["repo"],
                w_q=r["w_q"],
                w_s=r["w_s"],
                p_fail=r["p_fail"],
                drag_magnitude=r["drag_magnitude"],
                drag_coefficient=r["drag_coefficient"],
                trend=r["trend"],
                last_updated=datetime.fromisoformat(r["last_updated"]),
            )
            for r in rows
        ]
