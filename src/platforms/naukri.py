import datetime
import uuid

from src.models.schemas import RawJobArtifact
from src.platforms.base import PlatformAdapter


class NaukriAdapter(PlatformAdapter):
    """
    Adapter for Naukri.com
    Strategy Cascade: SerpAPI (Google search) -> Apify (Actor fallback) -> Manual ATS Extraction
    """

    async def search_jobs(self, query: str, location: str, **kwargs) -> list[RawJobArtifact]:
        # Mocking SerpAPI call response
        print(f"[NaukriAdapter] Searching via SerpAPI for '{query}' in '{location}'")

        # Simulated payload
        return [
            RawJobArtifact(
                job_id=f"naukri_{uuid.uuid4().hex[:8]}",
                source_platform="naukri",
                retrieval_strategy_used="serp_api",
                title=f"{query} (Naukri)",
                company="MockTech India Pvt Ltd",
                location=location,
                description_raw="We are looking for a skilled professional...",
                application_url="https://www.naukri.com/job-listings-123",
                scraped_at=datetime.datetime.utcnow().isoformat()
            )
        ]

    async def fetch_job_details(self, job_url: str) -> RawJobArtifact | None:
        print(f"[NaukriAdapter] Fetching details via Apify fallback for {job_url}")
        return RawJobArtifact(
            job_id=f"naukri_{uuid.uuid4().hex[:8]}",
            source_platform="naukri",
            retrieval_strategy_used="apify_actor",
            title="Software Engineer (Detailed)",
            company="MockTech India Pvt Ltd",
            description_raw="Detailed description from Apify extraction...",
            application_url=job_url,
            scraped_at=datetime.datetime.utcnow().isoformat()
        )
