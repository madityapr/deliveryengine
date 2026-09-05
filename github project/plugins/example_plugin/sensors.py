"""Example custom sensor plugin matching Section 8.1 in README.md."""

from typing import List
from antigravity.sensors.base import BaseSensor
from antigravity.models import RawEvent


class JiraTicketAgeSensor(BaseSensor):
    """Custom sensor monitoring Jira ticket review queue duration."""

    name: str = "jira_ticket_age"

    async def collect(self) -> List[RawEvent]:
        # Synthetic simulation of Jira ticket age polling
        return [
            RawEvent(
                source=self.name,
                stage="review.ticket_age",
                status="success",
                queue_seconds=1800.0,
                duration_seconds=300.0,
                repo="your-org/service-a",
                metadata={"ticket_key": "PROJ-1024", "assignee": "alex"},
            )
        ]
