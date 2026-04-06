"""Technology adjacency graph for skill matching and synonym resolution.

Provides synonym expansion (e.g., react.js -> react) and weighted adjacency
scores between related technologies (e.g., kubernetes <-> docker = 0.8).
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Synonym registry
# Keys are canonical skill names (lowercase).  Values are sets of known
# aliases that should all resolve to the canonical form.
# ---------------------------------------------------------------------------
_SYNONYMS: dict[str, set[str]] = {
    "python": {"python3", "py", "cpython"},
    "javascript": {"js", "ecmascript", "es6", "es2015"},
    "typescript": {"ts"},
    "react": {"react.js", "reactjs", "react js"},
    "angular": {"angular.js", "angularjs", "angular js"},
    "vue": {"vue.js", "vuejs", "vue js"},
    "node": {"node.js", "nodejs", "node js"},
    "kubernetes": {"k8s", "kube"},
    "docker": {"docker engine", "docker ce"},
    "aws": {"amazon web services", "amazon aws"},
    "gcp": {"google cloud", "google cloud platform"},
    "azure": {"microsoft azure", "ms azure"},
    "postgres": {"postgresql", "psql", "pg"},
    "mysql": {"mariadb"},
    "mongodb": {"mongo"},
    "redis": {"redis server"},
    "elasticsearch": {"elastic", "es", "opensearch"},
    "terraform": {"tf"},
    "ansible": {"ansible automation"},
    "jenkins": {"jenkins ci"},
    "github actions": {"gha", "gh actions"},
    "ci/cd": {"cicd", "ci cd", "continuous integration", "continuous delivery"},
    "graphql": {"gql"},
    "rest": {"rest api", "restful", "restful api"},
    "sql": {"structured query language"},
    "nosql": {"no-sql", "non-relational"},
    "machine learning": {"ml"},
    "deep learning": {"dl"},
    "natural language processing": {"nlp"},
    "computer vision": {"cv"},
    "data science": {"data analytics"},
    "pandas": {"pd"},
    "numpy": {"np"},
    "scikit-learn": {"sklearn", "scikit learn"},
    "pytorch": {"torch"},
    "tensorflow": {"tf", "tensor flow"},
    "java": {"jdk", "jre"},
    "spring": {"spring boot", "spring framework", "springboot"},
    "go": {"golang"},
    "rust": {"rust-lang", "rustlang"},
    "c++": {"cpp", "cplusplus", "c plus plus"},
    "c#": {"csharp", "c sharp"},
    ".net": {"dotnet", "dot net", "asp.net"},
    "ruby": {"ruby lang"},
    "rails": {"ruby on rails", "ror"},
    "django": {"django framework"},
    "flask": {"flask framework"},
    "fastapi": {"fast api"},
    "express": {"express.js", "expressjs"},
    "next.js": {"nextjs", "next js", "next"},
    "svelte": {"svelte.js", "sveltejs"},
    "tailwind": {"tailwindcss", "tailwind css"},
    "css": {"css3"},
    "html": {"html5"},
    "sass": {"scss"},
    "kafka": {"apache kafka"},
    "rabbitmq": {"rabbit mq", "rabbit"},
    "celery": {"celery task queue"},
    "linux": {"gnu/linux"},
    "bash": {"shell", "shell scripting", "sh"},
    "git": {"git vcs"},
    "jira": {"atlassian jira"},
    "confluence": {"atlassian confluence"},
    "figma": {"figma design"},
    "tableau": {"tableau desktop"},
    "power bi": {"powerbi", "power-bi"},
    "spark": {"apache spark", "pyspark"},
    "hadoop": {"apache hadoop"},
    "airflow": {"apache airflow"},
    "snowflake": {"snowflake db"},
    "databricks": {"databricks lakehouse"},
    "dbt": {"data build tool"},
}

# Build a reverse lookup: alias (lowercase) -> canonical name
_ALIAS_TO_CANONICAL: dict[str, str] = {}
for _canonical, _aliases in _SYNONYMS.items():
    _ALIAS_TO_CANONICAL[_canonical] = _canonical
    for _alias in _aliases:
        _ALIAS_TO_CANONICAL[_alias.lower()] = _canonical


# ---------------------------------------------------------------------------
# Adjacency edges
# Each entry is (skill_a, skill_b, weight).  Weights range 0-1 where 1 means
# "essentially interchangeable" and lower values indicate weaker relatedness.
# ---------------------------------------------------------------------------
_ADJACENCY_EDGES: list[tuple[str, str, float]] = [
    # Container / orchestration
    ("kubernetes", "docker", 0.80),
    ("kubernetes", "terraform", 0.55),
    ("docker", "terraform", 0.45),
    ("kubernetes", "ansible", 0.40),
    # Cloud providers
    ("aws", "gcp", 0.65),
    ("aws", "azure", 0.65),
    ("gcp", "azure", 0.65),
    ("aws", "terraform", 0.55),
    # Frontend JS frameworks
    ("react", "vue", 0.60),
    ("react", "angular", 0.55),
    ("react", "svelte", 0.55),
    ("vue", "angular", 0.55),
    ("vue", "svelte", 0.60),
    ("angular", "svelte", 0.50),
    ("react", "next.js", 0.85),
    # Frontend misc
    ("css", "tailwind", 0.70),
    ("css", "sass", 0.80),
    ("html", "css", 0.75),
    ("javascript", "typescript", 0.85),
    # Backend frameworks (Python)
    ("django", "flask", 0.70),
    ("django", "fastapi", 0.65),
    ("flask", "fastapi", 0.75),
    # Backend frameworks (JS)
    ("node", "express", 0.85),
    ("express", "fastapi", 0.40),
    # Languages
    ("python", "java", 0.30),
    ("python", "go", 0.35),
    ("python", "ruby", 0.45),
    ("java", "c#", 0.60),
    ("java", "go", 0.40),
    ("java", "kotlin", 0.80),
    ("c++", "rust", 0.55),
    ("c++", "c#", 0.45),
    ("ruby", "rails", 0.85),
    ("python", "django", 0.70),
    ("python", "flask", 0.65),
    ("python", "fastapi", 0.65),
    ("javascript", "node", 0.80),
    ("typescript", "node", 0.75),
    ("go", "rust", 0.45),
    # Databases
    ("postgres", "mysql", 0.75),
    ("postgres", "sql", 0.80),
    ("mysql", "sql", 0.80),
    ("mongodb", "nosql", 0.80),
    ("redis", "nosql", 0.50),
    ("elasticsearch", "nosql", 0.50),
    ("mongodb", "redis", 0.35),
    ("postgres", "mongodb", 0.30),
    # ML / Data Science
    ("machine learning", "deep learning", 0.80),
    ("machine learning", "data science", 0.75),
    ("machine learning", "natural language processing", 0.65),
    ("machine learning", "computer vision", 0.65),
    ("pytorch", "tensorflow", 0.80),
    ("scikit-learn", "machine learning", 0.75),
    ("pandas", "numpy", 0.75),
    ("pandas", "data science", 0.70),
    ("numpy", "data science", 0.60),
    ("python", "machine learning", 0.50),
    # Data engineering
    ("spark", "hadoop", 0.70),
    ("spark", "databricks", 0.75),
    ("airflow", "celery", 0.35),
    ("kafka", "rabbitmq", 0.65),
    ("snowflake", "databricks", 0.60),
    ("dbt", "snowflake", 0.55),
    ("dbt", "data science", 0.40),
    ("sql", "dbt", 0.55),
    # APIs
    ("rest", "graphql", 0.60),
    # CI/CD
    ("ci/cd", "jenkins", 0.70),
    ("ci/cd", "github actions", 0.75),
    ("jenkins", "github actions", 0.65),
    # OS / scripting
    ("linux", "bash", 0.70),
    ("bash", "python", 0.30),
    # Visualization
    ("tableau", "power bi", 0.80),
]


class TechAdjacencyGraph:
    """In-memory graph for technology skill synonym resolution and adjacency scoring."""

    def __init__(self) -> None:
        self._alias_to_canonical: dict[str, str] = dict(_ALIAS_TO_CANONICAL)
        # adjacency stored as {canonical_a: {canonical_b: weight}}
        self._adjacency: dict[str, dict[str, float]] = {}
        for skill_a, skill_b, weight in _ADJACENCY_EDGES:
            self._adjacency.setdefault(skill_a, {})[skill_b] = weight
            self._adjacency.setdefault(skill_b, {})[skill_a] = weight

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def canonicalize(self, skill: str) -> str:
        """Return the canonical form of *skill*, or lowercase original if unknown."""
        return self._alias_to_canonical.get(skill.lower().strip(), skill.lower().strip())

    def get_equivalents(self, skill: str) -> set[str]:
        """Return all known synonyms for *skill*, including the canonical form.

        If the skill is not in the synonym registry the returned set contains
        only the canonicalized input.
        """
        canonical = self.canonicalize(skill)
        aliases = _SYNONYMS.get(canonical, set())
        return {canonical} | {a.lower() for a in aliases}

    def adjacency_score(self, skill_a: str, skill_b: str) -> float:
        """Return the adjacency weight between two skills (0.0 if unrelated).

        Both inputs are canonicalized before lookup, so ``adjacency_score('k8s', 'docker')``
        works the same as ``adjacency_score('kubernetes', 'docker')``.
        """
        ca = self.canonicalize(skill_a)
        cb = self.canonicalize(skill_b)
        if ca == cb:
            return 1.0
        return self._adjacency.get(ca, {}).get(cb, 0.0)

    def get_adjacent(self, skill: str) -> dict[str, float]:
        """Return all skills adjacent to *skill* with their weights.

        Returns a ``{canonical_skill: weight}`` mapping.  Empty dict when the
        skill has no registered adjacency edges.
        """
        canonical = self.canonicalize(skill)
        return dict(self._adjacency.get(canonical, {}))
