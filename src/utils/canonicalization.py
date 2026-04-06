import re
import litellm
import httpx
from src.models.schemas import RawJobArtifact, JobDescriptionStructured

class JobCanonicalizer:
    def __init__(self, model="gpt-4o-mini"):
        self.model = model

    def normalize_title(self, title: str) -> str:
        """
        Standardizes casing, removes noise (Sr., III, etc.)
        """
        title = title.strip().title()
        # Remove typical noise
        noise_words = [r"\bSr\b\.?", r"\bJr\b\.?", r"III", r"II", r"- Remote", r"\(Remote\)"]
        for word in noise_words:
            title = re.sub(word, "", title, flags=re.IGNORECASE)
        # Fix multi-spaces
        title = re.sub(r"\s+", " ", title).strip()
        # Basic mapping
        title = title.replace("Senior", "").replace("Junior", "").strip()
        return title

    def normalize_company(self, name: str) -> str:
        """
        Strips legal suffixes, resolves common aliases.
        """
        name = name.strip()
        suffixes = [r"\bInc\b\.?", r"\bCorp\b\.?", r"\bLLC\b", r"\bPvt\b", r"\bLtd\b\.?", r"\bGmbH\b"]
        for suffix in suffixes:
            name = re.sub(suffix, "", name, flags=re.IGNORECASE)
        return re.sub(r"[\.,]$", "", name.strip()).strip()

    def normalize_location(self, loc: str) -> str:
        """
        Standardize city/state/country.
        """
        if not loc:
            return "Remote"
        
        loc = loc.strip().title()
        # Basic parsing or via LLM in a realistic scenario. 
        # For MVP, we return capitalized standard.
        return loc

    async def extract_structured_jd(self, raw_text: str) -> JobDescriptionStructured:
        """
        Uses LiteLLM to extract requirements, salary.
        """
        prompt = f"Extract structured job requirements (must have, nice to have), benefits, and experience range from this text:\\n\\n{raw_text[:2000]}"
        
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a JD parser. Respond with JSON containing responsibilities, requirements (must_have, nice_to_have), benefits, and experience_range."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            # Assuming perfectly formed JSON for the skeleton
            # content = json.loads(response.choices[0].message.content)
            # return JobDescriptionStructured(**content)
            
            # Return dummy structure pending real integration
            return JobDescriptionStructured(
                responsibilities=["Develop backend"],
                requirements={"must_have": ["Python"], "nice_to_have": ["AWS"]},
                benefits=["Healthcare"],
                experience_range="3-5 years"
            )
        except Exception as e:
            print(f"Extraction failed: {e}")
            return JobDescriptionStructured()

    async def resolve_canonical_url(self, url: str) -> str:
        """
        Unwraps redirection to get the canonical ATS URL.
        """
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=5.0) as client:
                response = await client.head(url)
                return str(response.url)
        except Exception:
            return url  # Fallback to original
