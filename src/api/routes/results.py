from fastapi import APIRouter

router = APIRouter(prefix="/campaigns/{campaign_id}/results", tags=["results"])


@router.get("/")
async def get_campaign_results(campaign_id: str):
    """
    Get the ranked results of jobs found so far.
    """
    return {
        "campaign_id": campaign_id,
        "results": [
            {"job_id": "mock_123", "title": "Senior Engineer", "company": "Mock Inc", "score": 0.95}
        ],
    }
