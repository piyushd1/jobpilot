from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class JobDescriptionStructured(BaseModel):
    responsibilities: List[str] = []
    requirements: Dict[str, List[str]] = {"must_have": [], "nice_to_have": []}
    benefits: List[str] = []
    experience_range: Optional[str] = None

class SalaryInfo(BaseModel):
    disclosed: bool = False
    range: Optional[str] = None
    estimated_range: Optional[str] = None

class RawJobArtifact(BaseModel):
    job_id: str
    source_platform: str
    retrieval_strategy_used: str = "manual_input"
    title: str
    company: str
    location: Optional[str] = None
    remote_type: Optional[str] = None
    description_raw: str
    description_structured: Optional[JobDescriptionStructured] = None
    salary_info: Optional[SalaryInfo] = Field(default_factory=SalaryInfo) # Use Field(default_factory=SalaryInfo)  # Oh wait, using inline default for now
    posted_date: Optional[str] = None
    application_url: str
    canonical_employer_url: Optional[str] = None
    apply_method: str = "external_redirect"
    recruiter_name_on_posting: Optional[str] = None
    scraped_at: str
    risk_flags: List[str] = []
    embedding_id: Optional[str] = None
