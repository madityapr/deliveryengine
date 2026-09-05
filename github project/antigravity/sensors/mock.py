"""Mock sensor generating realistic delivery pipeline telemetry for testing and local dev."""

import random
from datetime import datetime, timezone
from typing import List
from antigravity.models import RawEvent
from antigravity.sensors.base import BaseSensor


class MockSensor(BaseSensor):
    """Generates synthetic CI/CD and review pipeline events."""
    
    name: str = "mock"

    async def collect(self) -> List[RawEvent]:
        now = datetime.now(timezone.utc)
        events: List[RawEvent] = []
        
        stages = [
            {
                "stage": "ci.integration-tests",
                "repo": "your-org/service-a",
                "queue_seconds": 120.0 + random.uniform(-20, 30),
                "duration_seconds": 2400.0 + random.uniform(-100, 200),  # ~40 mins
                "p_fail": 0.21,
            },
            {
                "stage": "review.approval-queue",
                "repo": "your-org/service-a",
                "queue_seconds": 1800.0 + random.uniform(-300, 300),  # ~30 mins
                "duration_seconds": 600.0 + random.uniform(-50, 50),
                "p_fail": 0.05,
            },
            {
                "stage": "ci.docker-build",
                "repo": "your-org/service-a",
                "queue_seconds": 60.0 + random.uniform(-10, 20),
                "duration_seconds": 1100.0 + random.uniform(-50, 80),  # ~18 mins
                "p_fail": 0.03,
            },
            {
                "stage": "onboarding.env-setup",
                "repo": "your-org/service-b",
                "queue_seconds": 300.0 + random.uniform(-30, 50),
                "duration_seconds": 900.0 + random.uniform(-50, 50),  # ~15 mins
                "p_fail": 0.40,
            },
        ]
        
        for s in stages:
            is_failure = random.random() < s["p_fail"]
            status = "failure" if is_failure else "success"
            
            events.append(
                RawEvent(
                    source=self.name,
                    stage=s["stage"],
                    status=status,
                    queue_seconds=s["queue_seconds"],
                    duration_seconds=s["duration_seconds"],
                    repo=s["repo"],
                    commit_sha=f"sha-{random.randint(1000, 9999)}",
                    timestamp=now,
                    metadata={"synthetic": True},
                )
            )
            
        return events
