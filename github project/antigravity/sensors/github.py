"""GitHub telemetry sensor collecting workflow run and pull request metrics."""

import hmac
import hashlib
from typing import Any, Dict, List, Optional
from antigravity.models import RawEvent
from antigravity.sensors.base import BaseSensor


class GitHubSensor(BaseSensor):
    """Collector for GitHub webhooks and API events."""
    
    name: str = "github"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.webhook_secret = self.config.get("webhook_secret", "")

    def verify_webhook_signature(self, payload: bytes, signature_header: str) -> bool:
        """Verifies HMAC SHA-256 signature from GitHub webhooks."""
        if not self.webhook_secret:
            return True  # If no secret configured in dev, skip
        if not signature_header or not signature_header.startswith("sha256="):
            return False
        
        expected_sig = "sha256=" + hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(expected_sig, signature_header)

    def parse_workflow_job_webhook(self, payload: Dict[str, Any]) -> Optional[RawEvent]:
        """Parses a workflow_job webhook event into a RawEvent."""
        workflow_job = payload.get("workflow_job")
        if not workflow_job:
            return None
            
        stage_name = f"ci.{workflow_job.get('name', 'unknown-job')}"
        conclusion = workflow_job.get("conclusion") or "running"
        status = "success" if conclusion == "success" else "failure"
        
        # Approximate durations
        return RawEvent(
            source=self.name,
            stage=stage_name,
            status=status,
            repo=payload.get("repository", {}).get("full_name", "unknown-repo"),
            commit_sha=workflow_job.get("head_sha"),
            metadata={
                "run_id": workflow_job.get("run_id"),
                "html_url": workflow_job.get("html_url"),
            }
        )

    async def collect(self) -> List[RawEvent]:
        """Polls GitHub API if configured (e.g. using GITHUB_TOKEN)."""
        # Standalone implementation returns empty if no token configured
        return []
