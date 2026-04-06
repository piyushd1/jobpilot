class OutreachFinderAgent:
    """
    Identifies and ranks contacts at shortlisted companies using 5-tier discovery.
    1. Recruiter, 2. Hiring Manager, 3. Internal HR, 4. Peer, 5. Alumni
    Relies on SerpAPI Google Custom Search instead of direct LinkedIn scraping.
    """

    def __init__(self, model="gpt-4o-mini"):
        self.model = model

    def _mock_google_search(self, query: str):
        """Mocks SerpAPI response for site:linkedin.com/in"""
        print(f"[OutreachFinder] Searching: {query}")
        # Returns deterministic mock depending on queries
        if "VP" in query or "Manager" in query:
            return [
                {
                    "title": "Alice Smith - VP Engineering at MockCorp - LinkedIn",
                    "link": "https://linkedin.com/in/alicesmith",
                }
            ]
        return [
            {
                "title": "Bob Jones - Recruiter at MockCorp - LinkedIn",
                "link": "https://linkedin.com/in/bobjones",
            }
        ]

    async def discover_contacts(self, company_name: str, job_title: str) -> list:
        print(f"[OutreachFinder] Finding contacts for {job_title} at {company_name}")

        # simulated logic building search payloads
        manager_query = f'site:linkedin.com/in "{company_name}" ("VP Engineering" OR "Director of Engineering" OR "Engineering Manager")'
        recruiter_query = (
            f'site:linkedin.com/in "{company_name}" ("Technical Recruiter" OR "Talent Acquisition")'
        )

        manager_results = self._mock_google_search(manager_query)
        recruiter_results = self._mock_google_search(recruiter_query)

        contacts = []

        if manager_results:
            contacts.append(
                {
                    "name": manager_results[0]["title"].split("-")[0].strip(),
                    "role": "Hiring Manager",
                    "linkedin": manager_results[0]["link"],
                    "tier": 2,
                }
            )

        if recruiter_results:
            contacts.append(
                {
                    "name": recruiter_results[0]["title"].split("-")[0].strip(),
                    "role": "Recruiter",
                    "linkedin": recruiter_results[0]["link"],
                    "tier": 1,
                }
            )

        return contacts
