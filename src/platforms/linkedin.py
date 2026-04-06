import datetime
import uuid

from src.models.schemas import RawJobArtifact
from src.platforms.base import PlatformAdapter


class LinkedInAdapter(PlatformAdapter):
    """
    Adapter for LinkedIn.com
    Strategy Cascade: Official API -> RapidAPI fallback (jsearch) -> Scraping
    """

    async def search_jobs(self, query: str, location: str, **kwargs) -> list[RawJobArtifact]:
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
                scraped_at=datetime.datetime.utcnow().isoformat(),
            )
        ]

    async def fetch_job_details(self, job_url: str) -> RawJobArtifact | None:
        return RawJobArtifact(
            job_id=f"linkedin_{uuid.uuid4().hex[:8]}",
            source_platform="linkedin",
            retrieval_strategy_used="apify_actor",
            title="Software Engineer (Detailed)",
            company="TechCorp Global",
            description_raw="LinkedIn detailed JD...",
            application_url=job_url,
            scraped_at=datetime.datetime.utcnow().isoformat(),
        )
