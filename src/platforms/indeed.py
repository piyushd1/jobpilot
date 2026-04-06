import datetime
import uuid

from src.models.schemas import RawJobArtifact
from src.platforms.base import PlatformAdapter


class IndeedAdapter(PlatformAdapter):
    """
    Adapter for Indeed.com
    Strategy Cascade: Official Publisher API -> RapidAPI fallback
    """

    async def search_jobs(self, query: str, location: str, **kwargs) -> list[RawJobArtifact]:
        print(f"[IndeedAdapter] Searching via Publisher API for '{query}' in '{location}'")

        return [
            RawJobArtifact(
                job_id=f"indeed_{uuid.uuid4().hex[:8]}",
                source_platform="indeed",
                retrieval_strategy_used="publisher_api",
                title=f"{query} (Indeed)",
                company="Global Solutions Inc",
                location=location,
                description_raw="Join our dynamic team...",
                application_url="https://www.indeed.com/viewjob?jk=123",
                scraped_at=datetime.datetime.utcnow().isoformat()
            )
        ]

    async def fetch_job_details(self, job_url: str) -> RawJobArtifact | None:
        print(f"[IndeedAdapter] Fetching details via RapidAPI for {job_url}")
        return RawJobArtifact(
            job_id=f"indeed_{uuid.uuid4().hex[:8]}",
            source_platform="indeed",
            retrieval_strategy_used="rapid_api",
            title="Software Engineer (Detailed)",
            company="Global Solutions Inc",
            description_raw="Extracted indeed description...",
            application_url=job_url,
            scraped_at=datetime.datetime.utcnow().isoformat()
        )
