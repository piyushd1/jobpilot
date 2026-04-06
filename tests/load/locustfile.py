"""Load testing for JobPilot using Locust.

Simulates 10 concurrent campaigns to measure:
  - Temporal worker throughput
  - API response times
  - Scoring engine performance under load
  - Deduplication pipeline concurrency

Run: locust -f tests/load/locustfile.py --host=http://localhost:8000
"""

from __future__ import annotations

import random
import uuid

from locust import HttpUser, between, task

SAMPLE_ROLES = [
    "Senior Software Engineer",
    "Backend Developer",
    "Full Stack Developer",
    "Data Engineer",
    "ML Engineer",
    "DevOps Engineer",
    "Platform Engineer",
    "Frontend Engineer",
]

SAMPLE_COMPANIES = [
    "Google",
    "Microsoft",
    "Stripe",
    "Amazon",
    "Meta",
    "Flipkart",
    "Swiggy",
    "Razorpay",
    "Zerodha",
    "CRED",
]

SAMPLE_SKILLS = [
    "Python",
    "Go",
    "Java",
    "TypeScript",
    "Kubernetes",
    "PostgreSQL",
    "Redis",
    "Kafka",
    "Docker",
    "AWS",
    "React",
    "Node.js",
    "Terraform",
    "gRPC",
    "GraphQL",
]


class CampaignUser(HttpUser):
    """Simulates a user running a job search campaign."""

    wait_time = between(1, 3)

    def on_start(self) -> None:
        self.campaign_id = str(uuid.uuid4())
        self.user_id = str(uuid.uuid4())

    @task(3)
    def health_check(self) -> None:
        self.client.get("/health")

    @task(2)
    def create_campaign(self) -> None:
        payload = {
            "user_id": self.user_id,
            "name": f"Load test campaign {self.campaign_id[:8]}",
            "roles": random.sample(SAMPLE_ROLES, k=random.randint(1, 3)),
            "companies": random.sample(SAMPLE_COMPANIES, k=random.randint(2, 5)),
            "skills": random.sample(SAMPLE_SKILLS, k=random.randint(3, 8)),
            "locations": ["Bangalore", "Remote"],
        }
        self.client.post(
            "/campaigns",
            json=payload,
            name="/campaigns [create]",
        )

    @task(1)
    def get_campaign_status(self) -> None:
        self.client.get(
            f"/campaigns/{self.campaign_id}/status",
            name="/campaigns/{id}/status",
        )

    @task(1)
    def get_campaign_jobs(self) -> None:
        self.client.get(
            f"/campaigns/{self.campaign_id}/jobs",
            name="/campaigns/{id}/jobs",
        )


class ScoringLoadUser(HttpUser):
    """Simulates scoring engine load by hitting the scoring endpoint."""

    wait_time = between(0.5, 1.5)

    @task
    def score_job(self) -> None:
        payload = {
            "candidate": {
                "skills": random.sample(SAMPLE_SKILLS, k=random.randint(4, 10)),
                "target_roles": random.sample(SAMPLE_ROLES, k=2),
                "experience_years": random.randint(2, 15),
            },
            "job": {
                "title": random.choice(SAMPLE_ROLES),
                "company": random.choice(SAMPLE_COMPANIES),
                "required_skills": random.sample(SAMPLE_SKILLS, k=random.randint(3, 6)),
            },
        }
        self.client.post(
            "/score",
            json=payload,
            name="/score [compute]",
        )
