from abc import ABC, abstractmethod

from src.models.schemas import RawJobArtifact


class PlatformAdapter(ABC):
    """
    Abstract Base Class for all job platform adapters.
    """

    @abstractmethod
    async def search_jobs(self, query: str, location: str, **kwargs) -> list[RawJobArtifact]:
        """
        Search the platform for jobs matching the query and location.
        Implements the strategy cascade (Official API -> Vendor -> Fallbacks).
        """
        pass

    @abstractmethod
    async def fetch_job_details(self, job_url: str) -> RawJobArtifact | None:
        """
        Extract detailed job description and metadata from a specific job posting URL.
        """
        pass
