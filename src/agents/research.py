import litellm


class ResearchAgent:
    """
    Agent 3: Enriches company data (funding, size, ratings) via search.
    """

    def __init__(self, model: str | None = None):
        from src.config.settings import settings

        self.model = model or settings.llm_fast_model

    async def enrich_company(self, company_name: str) -> dict:
        """
        Triggered when a new job is discovered. Searches Crunchbase/Glassdoor.
        """
        print(f"[ResearchAgent] Enriching data for {company_name}")

        # In a full implementation, this uses SerpAPI for glassdoor and crunchbase
        prompt = f"Provide a JSON estimate for '{company_name}': funding_stage (e.g. Series A, Public), employee_count (e.g. 100-500), glassdoor_rating_estimate (0.0-5.0)."

        try:
            await litellm.acompletion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a company research tool returning JSON.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            # Mock parsing logic
            return {
                "name": company_name,
                "funding_stage": "Public",
                "employee_count": "1000+",
                "glassdoor_rating": 4.1,
            }
        except Exception as e:
            print(f"Research failed: {e}")
            return {}
