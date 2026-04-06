"""Skill normalization — maps common variations to canonical forms.

Used to deduplicate and standardize skills extracted from resumes and
job descriptions so that scoring comparisons work reliably.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Synonym dictionary: lowercase variant -> canonical form
# ---------------------------------------------------------------------------
_SKILL_SYNONYMS: dict[str, str] = {
    # JavaScript ecosystem
    "react.js": "React",
    "reactjs": "React",
    "react js": "React",
    "react native": "React Native",
    "reactnative": "React Native",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "next js": "Next.js",
    "vue.js": "Vue.js",
    "vuejs": "Vue.js",
    "vue js": "Vue.js",
    "nuxt.js": "Nuxt.js",
    "nuxtjs": "Nuxt.js",
    "angular.js": "Angular",
    "angularjs": "Angular",
    "angular js": "Angular",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "node js": "Node.js",
    "node": "Node.js",
    "express.js": "Express.js",
    "expressjs": "Express.js",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    # Python ecosystem
    "python3": "Python",
    "python 3": "Python",
    "py": "Python",
    "django": "Django",
    "flask": "Flask",
    "fastapi": "FastAPI",
    "fast api": "FastAPI",
    "pandas": "Pandas",
    "numpy": "NumPy",
    "scipy": "SciPy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    # Cloud / Infrastructure
    "amazon web services": "AWS",
    "aws": "AWS",
    "google cloud platform": "GCP",
    "google cloud": "GCP",
    "gcp": "GCP",
    "microsoft azure": "Azure",
    "azure": "Azure",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "docker": "Docker",
    "terraform": "Terraform",
    "tf": "Terraform",
    "ansible": "Ansible",
    # Databases
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "pg": "PostgreSQL",
    "mysql": "MySQL",
    "my sql": "MySQL",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "mongo db": "MongoDB",
    "redis": "Redis",
    "dynamodb": "DynamoDB",
    "dynamo db": "DynamoDB",
    "elasticsearch": "Elasticsearch",
    "elastic search": "Elasticsearch",
    "es": "Elasticsearch",
    "sqlite": "SQLite",
    "sql server": "SQL Server",
    "mssql": "SQL Server",
    "ms sql": "SQL Server",
    # Languages
    "golang": "Go",
    "go lang": "Go",
    "go language": "Go",
    "rust lang": "Rust",
    "rustlang": "Rust",
    "c++": "C++",
    "cpp": "C++",
    "c plus plus": "C++",
    "c#": "C#",
    "csharp": "C#",
    "c sharp": "C#",
    "objective-c": "Objective-C",
    "objc": "Objective-C",
    "obj-c": "Objective-C",
    "ruby on rails": "Ruby on Rails",
    "rails": "Ruby on Rails",
    "ror": "Ruby on Rails",
    # ML / AI
    "machine learning": "Machine Learning",
    "ml": "Machine Learning",
    "deep learning": "Deep Learning",
    "dl": "Deep Learning",
    "artificial intelligence": "AI",
    "ai": "AI",
    "natural language processing": "NLP",
    "nlp": "NLP",
    "computer vision": "Computer Vision",
    "cv": "Computer Vision",
    "tensorflow": "TensorFlow",
    "tf (ml)": "TensorFlow",
    "pytorch": "PyTorch",
    "torch": "PyTorch",
    "large language models": "LLMs",
    "llm": "LLMs",
    "llms": "LLMs",
    # DevOps / CI-CD
    "ci/cd": "CI/CD",
    "cicd": "CI/CD",
    "ci cd": "CI/CD",
    "continuous integration": "CI/CD",
    "github actions": "GitHub Actions",
    "gh actions": "GitHub Actions",
    "jenkins": "Jenkins",
    "circleci": "CircleCI",
    "circle ci": "CircleCI",
    # Data / Analytics
    "apache spark": "Spark",
    "pyspark": "Spark",
    "apache kafka": "Kafka",
    "apache airflow": "Airflow",
    "airflow": "Airflow",
    "snowflake": "Snowflake",
    "bigquery": "BigQuery",
    "big query": "BigQuery",
    "google bigquery": "BigQuery",
    # Misc tools
    "graphql": "GraphQL",
    "graph ql": "GraphQL",
    "rest api": "REST",
    "restful": "REST",
    "restful api": "REST",
    "rest apis": "REST",
    "grpc": "gRPC",
    "rabbitmq": "RabbitMQ",
    "rabbit mq": "RabbitMQ",
    "html5": "HTML",
    "html": "HTML",
    "css3": "CSS",
    "css": "CSS",
    "sass": "Sass",
    "scss": "Sass",
    "tailwindcss": "Tailwind CSS",
    "tailwind css": "Tailwind CSS",
    "tailwind": "Tailwind CSS",
    ".net": ".NET",
    "dotnet": ".NET",
    "dot net": ".NET",
    "asp.net": "ASP.NET",
    "aspnet": "ASP.NET",
    "git": "Git",
    "github": "GitHub",
    "gitlab": "GitLab",
    "jira": "Jira",
    "confluence": "Confluence",
    "figma": "Figma",
    "linux": "Linux",
    "unix": "Unix",
    "bash": "Bash",
    "shell scripting": "Bash",
    "agile": "Agile",
    "scrum": "Scrum",
}


def normalize_skill(skill: str) -> str:
    """Normalize a single skill string to its canonical form.

    Performs a case-insensitive lookup in the synonym dictionary.
    If no mapping is found, returns the original string with leading/trailing
    whitespace stripped.

    Args:
        skill: Raw skill string (e.g. "react.js", "K8s", "Amazon Web Services").

    Returns:
        Canonical skill name (e.g. "React", "Kubernetes", "AWS").
    """
    stripped = skill.strip()
    return _SKILL_SYNONYMS.get(stripped.lower(), stripped)


def normalize_skills(skills: list[str]) -> list[str]:
    """Normalize a list of skills, removing duplicates while preserving order.

    Args:
        skills: Raw skill strings.

    Returns:
        Deduplicated list of canonical skill names in first-seen order.
    """
    seen: set[str] = set()
    result: list[str] = []
    for skill in skills:
        canonical = normalize_skill(skill)
        key = canonical.lower()
        if key not in seen:
            seen.add(key)
            result.append(canonical)
    return result
