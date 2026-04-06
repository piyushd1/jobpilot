import datetime
import uuid

import litellm

from src.models.schemas import RawJobArtifact


class ManualInputService:
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model

    async def parse_urls(self, urls: list[str]) -> list[RawJobArtifact]:
        """
        Takes a list of URLs, optionally fetches their content, and generates artifacts.
        Since we might not have a web scraper in this barebones phase, we will mock parsing slightly, 
        or use LiteLLM to structure just the URLs assuming they contain hints.
        For production, a web scraper tool fetches the DOM before sending to LiteLLM.
        """
        artifacts = []
        for url in urls:
            prompt = f"Parse the following job URL and extract best-effort title and company: {url}"
            try:
                # In complete implementation, we'd fetch URL HTML first
                response = await litellm.acompletion(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You extract job info from minimal context. Return a JSON structure."},
                        {"role": "user", "content": prompt}
                    ],
                    response_format={ "type": "json_object" }
                )

                # Mock extraction assuming LLM gave valid output
                # We put dummy data so pipeline doesn't break
                artifacts.append(
                    RawJobArtifact(
                        job_id=f"manual_{uuid.uuid4().hex[:8]}",
                        source_platform="manual_url",
                        title="Unknown Title (from URL)",
                        company="Unknown Company",
                        description_raw=f"Job found at {url}",
                        application_url=url,
                        scraped_at=datetime.datetime.utcnow().isoformat()
                    )
                )
            except Exception as e:
                print(f"Error parsing {url}: {e}")
        return artifacts

    async def parse_raw_text(self, text: str) -> list[RawJobArtifact]:
        """
        Extracts multiple jobs from pasted text/CSV.
        """
        # A full prompt to `litellm` asking for `List[RawJobArtifact]` schema extraction
        # Mocking for skeleton:
        return [
             RawJobArtifact(
                job_id=f"manual_{uuid.uuid4().hex[:8]}",
                source_platform="manual_text_paste",
                title="Software Engineer",
                company="Mock Corp",
                description_raw=text[:200] + "...",
                application_url="https://mockcorp.com/jobs",
                scraped_at=datetime.datetime.utcnow().isoformat()
            )
        ]
