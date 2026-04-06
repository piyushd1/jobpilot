from fastapi import APIRouter, File, UploadFile, HTTPException, Form
from pydantic import BaseModel
from typing import List, Optional
from src.platforms.manual_input import ManualInputService

router = APIRouter(prefix="/campaigns/{campaign_id}/manual-links", tags=["manual_links"])
manual_service = ManualInputService()

class ManualUrlsRequest(BaseModel):
    urls: List[str]

@router.post("/urls")
async def add_manual_urls(campaign_id: str, payload: ManualUrlsRequest):
    """
    Accepts a list of URLs manually provided by the user.
    """
    artifacts = await manual_service.parse_urls(payload.urls)
    return {
        "status": "success",
        "campaign_id": campaign_id,
        "processed_count": len(artifacts),
        "artifacts": artifacts
    }

@router.post("/paste")
async def add_manual_paste(campaign_id: str, raw_text: str = Form(...)):
    """
    Accepts raw CSV string or text pasted by the user.
    """
    artifacts = await manual_service.parse_raw_text(raw_text)
    return {
        "status": "success",
        "campaign_id": campaign_id,
        "processed_count": len(artifacts),
        "artifacts": artifacts
    }
