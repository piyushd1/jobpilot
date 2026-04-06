import litellm


class OutreachDrafterAgent:
    """
    Takes a candidate profile, a job description, and a target contact to
    draft highly personalized, context-aware networking messages in 5 templates.
    """

    def __init__(self, model="gpt-4o"):
        self.model = model

    def build_developer_prompt(self, contact, company, job_title):
        return f"""
        Draft 5 separate message variants to {contact["name"]} ({contact["role"]}) at {company} regarding the {job_title} role.
        Return JSON with keys:
        - linkedin_connection (max 300 chars, casual, professional)
        - recruiter_intro (4-6 lines highlighting top 2 matched skills)
        - peer_referral (informational chat request)
        - exec_summary (bottom-line impact driven, for hiring manager)
        - general_email (warm outbound with attached resume CTA)
        """

    async def draft_messages(self, contact: dict, company: str, job_title: str) -> dict:
        print(f"[OutreachDrafter] Drafting variants for {contact['name']} at {company}")

        prompt = self.build_developer_prompt(contact, company, job_title)
        try:
            response = await litellm.acompletion(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an elite executive recruiter drafting concise candidate outreach messages.",
                    },
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            return eval(response.choices[0].message.content)  # Assuming JSON structured response
        except Exception as e:
            print(f"Error drafting messages: {e}")
            # deterministic fallback
            return {
                "linkedin_connection": f"Hi {contact['name']}, I'd love to connect and learn more about the {job_title} team at {company}!",
                "recruiter_intro": "Mock recruiter intro text...",
                "peer_referral": "Mock peer referral text...",
                "exec_summary": "Mock exec summary text...",
                "general_email": "Mock general email text...",
            }
