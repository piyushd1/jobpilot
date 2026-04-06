from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/approvals", tags=["approvals"])


class ApprovalDecision(BaseModel):
    decision: str  # e.g., "APPROVED", "REJECTED"
    notes: str = ""


@router.post("/{approval_id}/decision")
async def submit_decision(approval_id: str, decision: ApprovalDecision):
    """
    Submit a human-in-the-loop decision, which signals the Temporal workflow to continue.
    """
    return {
        "status": "success",
        "approval_id": approval_id,
        "decision": decision.decision,
        "message": "Decision recorded. Temporal workflow signaled.",
    }
