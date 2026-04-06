from abc import ABC, abstractmethod
from typing import List, Optional
from src.models.schemas import RawJobArtifact

class PlatformAdapter(ABC):
    """
    Abstract Base Class for all job platform adapters.
    """
    
    @abstractmethod
    async def search_jobs(self, query: str, location: str, **kwargs) -> List[RawJobArtifact]:
        """
        Search the platform for jobs matching the query and location.
        Implements the strategy cascade (Official API -> Vendor -> Fallbacks).
        """
        pass

    @abstractmethod
    async def fetch_job_details(self, job_url: str) -> Optional[RawJobArtifact]:
        """
        Extract detailed job description and metadata from a specific job posting URL.
        """
        pass
