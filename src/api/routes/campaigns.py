from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

router = APIRouter(prefix="/campaigns", tags=["campaigns"])

class CampaignCreate(BaseModel):
    resume_id: str
    target_roles: List[str]
    target_companies: List[str]
    target_locations: List[str]
    remote_preference: str

@router.post("/")
async def create_campaign(campaign: CampaignCreate):
    """
    Creates a new job hunt campaign.
    Validates preferences and spawns the Temporal workflow.
    """
    # Mock behavior until Temporal is hooked up
    import uuid
    campaign_id = str(uuid.uuid4())
    return {
        "status": "created",
        "campaign_id": campaign_id,
        "message": "Workflow started (Mock)"
    }

@router.get("/{campaign_id}")
async def get_campaign(campaign_id: str):
    """
    Retrieves the status of an ongoing campaign.
    """
    return {
        "campaign_id": campaign_id,
        "status": "RUNNING",
        "phase": "SCOUTING"
    }
