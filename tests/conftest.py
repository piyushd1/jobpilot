"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_candidate_profile():
    """A sample parsed candidate profile for testing."""
    from src.models.schemas import CandidateProfile, Education, WorkExperience

    return CandidateProfile(
        full_name="Jane Doe",
        email="jane@example.com",
        location="Bangalore, India",
        summary="Senior backend engineer with 8 years of experience in distributed systems.",
        target_roles=["Senior Software Engineer", "Staff Engineer", "Backend Lead"],
        target_companies=["Google", "Microsoft", "Stripe"],
        target_locations=["Bangalore", "Remote"],
        open_to_remote=True,
        skills=[
            "Python",
            "Go",
            "Kubernetes",
            "PostgreSQL",
            "Redis",
            "gRPC",
            "AWS",
            "Docker",
            "Kafka",
            "React",
        ],
        skills_normalized=[
            "python",
            "go",
            "kubernetes",
            "postgresql",
            "redis",
            "grpc",
            "aws",
            "docker",
            "kafka",
            "react",
        ],
        work_experience=[
            WorkExperience(
                company="Acme Corp",
                title="Senior Software Engineer",
                start_date="2020-01",
                is_current=True,
                description="Led backend platform team building distributed services.",
                skills_used=["Python", "Kubernetes", "PostgreSQL", "Kafka"],
            ),
            WorkExperience(
                company="StartupXYZ",
                title="Software Engineer",
                start_date="2016-06",
                end_date="2019-12",
                description="Full-stack development on fintech platform.",
                skills_used=["Go", "React", "Redis", "Docker"],
            ),
        ],
        total_experience_years=8.0,
        education=[
            Education(
                institution="IIT Bombay",
                degree="B.Tech",
                field_of_study="Computer Science",
                graduation_year=2016,
            )
        ],
    )


@pytest.fixture
def sample_job_description():
    """A sample job description for testing."""
    from src.models.schemas import JobDescription

    return JobDescription(
        title="Senior Backend Engineer",
        company="TechCorp",
        location="Bangalore, India",
        is_remote=False,
        description="We are looking for a senior backend engineer to build distributed systems.",
        required_skills=["Python", "Kubernetes", "PostgreSQL", "AWS"],
        preferred_skills=["Kafka", "gRPC", "Go"],
        min_experience_years=5,
        max_experience_years=10,
        source_platform="naukri",
        application_url_employer="https://techcorp.com/careers/senior-backend",
    )
