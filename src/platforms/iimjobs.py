import uuid
import datetime
from typing import List, Optional
from src.platforms.base import PlatformAdapter
from src.models.schemas import RawJobArtifact

class IIMJobsAdapter(PlatformAdapter):
    """
    Adapter for IIMJobs.com
    Dedicated strategy for premium Indian management/tech jobs.
    """

    async def search_jobs(self, query: str, location: str, **kwargs) -> List[RawJobArtifact]:
        print(f"[IIMJobsAdapter] Searching via custom scraper for '{query}' in '{location}'")
        return [
            RawJobArtifact(
                job_id=f"iimjobs_{uuid.uuid4().hex[:8]}",
                source_platform="iimjobs",
                retrieval_strategy_used="custom_scraper",
                title=f"{query} (IIMJobs)",
                company="Elite Finance",
                location=location,
                description_raw="Exclusive opportunity...",
                application_url="https://www.iimjobs.com/j/123",
                scraped_at=datetime.datetime.utcnow().isoformat()
            )
        ]

    async def fetch_job_details(self, job_url: str) -> Optional[RawJobArtifact]:
        return RawJobArtifact(
            job_id=f"iimjobs_{uuid.uuid4().hex[:8]}",
            source_platform="iimjobs",
            retrieval_strategy_used="custom_scraper",
            title="VP Engineering",
            company="Elite Finance",
            description_raw="Detailed IIMJobs JD...",
            application_url=job_url,
            scraped_at=datetime.datetime.utcnow().isoformat()
        )
