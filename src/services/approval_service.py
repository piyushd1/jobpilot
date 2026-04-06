"""Approval workflow service — human-in-the-loop gates for the pipeline.

Four mandatory gates:
  1. Post-parsing: user corrects extracted profile (optional)
  2. Post-ranking: user approves/rejects shortlisted jobs
  3. Post-contacts: user approves contact list before draft generation
  4. Post-drafts: user approves outreach messages before send

Plus automatic gates for risk review and challenge review.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from src.utils.logging import get_logger

logger = get_logger(__name__)


class ApprovalType(StrEnum):
    """Types of approval gates in the pipeline."""

    PROFILE_REVIEW = "profile_review"
    SHORTLIST = "shortlist"
    CONTACTS = "contacts"
    OUTREACH_DRAFTS = "outreach_drafts"
    RISK_REVIEW = "risk_review"
    CHALLENGE_REVIEW = "challenge_review"


class ApprovalDecision(StrEnum):
    APPROVED = "approved"
    REJECTED = "rejected"
    PARTIALLY_APPROVED = "partially_approved"


class ApprovalRequest(BaseModel):
    """Request to create an approval task."""

    campaign_id: str
    approval_type: ApprovalType
    payload: dict[str, Any]
    item_count: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)


class ApprovalResponse(BaseModel):
    """Response when submitting a decision."""

    approval_id: str
    decision: ApprovalDecision
    notes: str = ""
    per_item_decisions: dict[str, str] = Field(default_factory=dict)


class ApprovalTask(BaseModel):
    """An approval task pending human review."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    campaign_id: str
    approval_type: ApprovalType
    payload: dict[str, Any]
    status: str = "pending"
    decision: ApprovalDecision | None = None
    decision_notes: str = ""
    per_item_decisions: dict[str, str] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    decided_at: str | None = None


class ApprovalService:
    """Manages approval tasks and integrates with the Temporal workflow.

    In production, tasks are persisted to the `approval_tasks` DB table.
    For now, uses an in-memory store.
    """

    def __init__(self) -> None:
        self._tasks: dict[str, ApprovalTask] = {}

    async def create_approval_task(
        self,
        campaign_id: str,
        approval_type: ApprovalType,
        payload: dict[str, Any],
        metadata: dict[str, Any] | None = None,
    ) -> ApprovalTask:
        """Create a new approval task. Returns the task for tracking.

        In production, this also sends a Temporal signal `APPROVAL_PENDING`
        to pause the workflow until a decision is made.
        """
        task = ApprovalTask(
            campaign_id=campaign_id,
            approval_type=approval_type,
            payload=payload,
        )
        self._tasks[task.id] = task

        logger.info(
            "Approval task created",
            task_id=task.id,
            campaign_id=campaign_id,
            type=approval_type,
        )

        return task

    async def submit_decision(
        self,
        approval_id: str,
        decision: ApprovalDecision,
        notes: str = "",
        per_item_decisions: dict[str, str] | None = None,
    ) -> ApprovalTask:
        """Submit a decision for an approval task.

        Supports per-item decisions for list-type approvals (e.g., approve
        job 1, reject job 3 in a shortlist).

        In production, this sends a Temporal signal `APPROVAL_COMPLETE`
        to resume the paused workflow.
        """
        task = self._tasks.get(approval_id)
        if task is None:
            raise ValueError(f"Approval task not found: {approval_id}")

        if task.status != "pending":
            raise ValueError(f"Approval task {approval_id} already decided: {task.status}")

        task.decision = decision
        task.decision_notes = notes
        task.per_item_decisions = per_item_decisions or {}
        task.status = "decided"
        task.decided_at = datetime.now(timezone.utc).isoformat()

        logger.info(
            "Approval decision submitted",
            task_id=approval_id,
            decision=decision,
            items=len(task.per_item_decisions),
        )

        return task

    async def get_task(self, approval_id: str) -> ApprovalTask | None:
        """Get an approval task by ID."""
        return self._tasks.get(approval_id)

    async def get_pending_tasks(self, campaign_id: str) -> list[ApprovalTask]:
        """Get all pending approval tasks for a campaign."""
        return [
            t for t in self._tasks.values()
            if t.campaign_id == campaign_id and t.status == "pending"
        ]

    async def get_approved_items(self, approval_id: str) -> list[str]:
        """For list-type approvals, return the IDs of approved items."""
        task = self._tasks.get(approval_id)
        if task is None or task.decision is None:
            return []

        if task.decision == ApprovalDecision.APPROVED:
            # All items approved
            return list(task.per_item_decisions.keys()) or ["all"]

        if task.decision == ApprovalDecision.PARTIALLY_APPROVED:
            return [
                item_id for item_id, dec in task.per_item_decisions.items()
                if dec == "approved"
            ]

        return []

    # --- Gate-specific convenience methods ---

    async def create_shortlist_gate(
        self, campaign_id: str, shortlist: list[dict[str, Any]]
    ) -> ApprovalTask:
        """Create approval gate for post-ranking shortlist review."""
        return await self.create_approval_task(
            campaign_id=campaign_id,
            approval_type=ApprovalType.SHORTLIST,
            payload={
                "description": "Review scored job shortlist. Approve or reject each job.",
                "items": shortlist,
                "item_count": len(shortlist),
            },
        )

    async def create_contacts_gate(
        self, campaign_id: str, contacts: list[dict[str, Any]]
    ) -> ApprovalTask:
        """Create approval gate for contact list review."""
        return await self.create_approval_task(
            campaign_id=campaign_id,
            approval_type=ApprovalType.CONTACTS,
            payload={
                "description": "Review prioritized contacts before outreach drafts.",
                "items": contacts,
                "item_count": len(contacts),
            },
        )

    async def create_drafts_gate(
        self, campaign_id: str, drafts: list[dict[str, Any]]
    ) -> ApprovalTask:
        """Create approval gate for outreach message drafts."""
        return await self.create_approval_task(
            campaign_id=campaign_id,
            approval_type=ApprovalType.OUTREACH_DRAFTS,
            payload={
                "description": "Review outreach message drafts before sending.",
                "items": drafts,
                "item_count": len(drafts),
            },
        )

    async def create_risk_review_gate(
        self, campaign_id: str, flagged_jobs: list[dict[str, Any]]
    ) -> ApprovalTask:
        """Create mandatory review gate for risk-flagged jobs."""
        return await self.create_approval_task(
            campaign_id=campaign_id,
            approval_type=ApprovalType.RISK_REVIEW,
            payload={
                "description": "Jobs flagged as high risk. Review before including in shortlist.",
                "items": flagged_jobs,
                "item_count": len(flagged_jobs),
            },
        )

    async def create_challenge_review_gate(
        self, campaign_id: str, challenge_details: dict[str, Any]
    ) -> ApprovalTask:
        """Create review gate for browser challenge events."""
        return await self.create_approval_task(
            campaign_id=campaign_id,
            approval_type=ApprovalType.CHALLENGE_REVIEW,
            payload={
                "description": "Browser automation detected a challenge. Review details.",
                **challenge_details,
            },
        )


# Singleton
approval_service = ApprovalService()
