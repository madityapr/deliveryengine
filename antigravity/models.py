"""Core domain models and abstractions for Antigravity."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


class OrbitalStatus(str, Enum):
    SUB_ORBITAL = "SUB_ORBITAL"
    APPROACHING = "APPROACHING"
    ESCAPE = "ESCAPE"
    DECAYING = "DECAYING"


class RawEvent(BaseModel):
    """Raw pipeline or telemetry event ingested by sensors."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source: str
    stage: str
    status: str = "success"  # success, failure, flaky, error
    duration_seconds: float = 0.0
    queue_seconds: float = 0.0
    repo: str = "default-repo"
    commit_sha: Optional[str] = None
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DragVector(BaseModel):
    """A single measured instance of drag (magnitude, timestamp, source, stage)."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    well_id: str
    magnitude: float
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    source: str
    stage: str
    repo: Optional[str] = None


class GravityWell(BaseModel):
    """A named, measurable source of delivery drag with a time-series drag signal."""
    id: str
    stage: str
    repo: str = "default-repo"
    w_q: float = 0.0  # Average queue wait time in minutes
    w_s: float = 0.0  # Average service time in minutes
    p_fail: float = 0.0  # Failure / retry probability [0.0 - 1.0]
    drag_magnitude: float = 0.0  # Cost-weighted drag: W_q + W_s * P_fail
    drag_coefficient: float = 0.0  # Normalized Cd in [0.0 - 1.0]
    trend: str = "▬ 0%"  # e.g. ▲ +12%, ▼ -8%
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ThrustEvent(BaseModel):
    """A record of a thruster firing: input state, action taken, resulting Δv."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    thruster: str
    well_id: str
    action: str
    delta_v: float = 0.0  # Velocity boost gained
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "SUCCESS"  # SUCCESS, FAILED, DRY_RUN, SKIPPED
    details: Dict[str, Any] = Field(default_factory=dict)


class VelocityMetric(BaseModel):
    deploys_per_day: float = 0.0
    lead_time_hours: float = 0.0


class EscapeVelocityTarget(BaseModel):
    deploys_per_day: float = 3.0
    lead_time_hours: float = 4.0


class OrbitalState(BaseModel):
    """The current velocity, acceleration, and stability of a pipeline or team."""
    scope: str = "repo"
    target: Optional[str] = None
    current_velocity: VelocityMetric = Field(default_factory=VelocityMetric)
    escape_velocity_target: EscapeVelocityTarget = Field(default_factory=EscapeVelocityTarget)
    escape_velocity_ratio: float = 0.0  # EVR = v_current / v_target
    status: OrbitalStatus = OrbitalStatus.SUB_ORBITAL
    top_drag_contributors: List[str] = Field(default_factory=list)
    osi: float = 1.0  # Orbit Stability Index


class GravitationalField(BaseModel):
    """The complete set of GravityWells for a given scope."""
    scope: str = "repo"
    target: Optional[str] = None
    wells: List[GravityWell] = Field(default_factory=list)
    total_drag: float = 0.0
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
