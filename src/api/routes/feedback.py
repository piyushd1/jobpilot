from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackEvent(BaseModel):
    campaign_id: str
    job_id: str
    action: str  # e.g., "SAVED", "DISMISSED", "APPLIED"

@router.post("/")
async def record_feedback(event: FeedbackEvent):
    """
    Record user feedback on a job to feed the learning agent.
    """
    return {
        "status": "success",
        "event": event,
        "message": "Feedback recorded."
    }
