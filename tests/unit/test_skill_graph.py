"""Unit tests for the Tech Adjacency Graph.

Covers:
  - Synonym expansion (react.js -> react, k8s -> kubernetes)
  - Adjacency scores (kubernetes<->docker = 0.8, react<->vue = 0.6)
  - Unknown skills return lowercase canonical
  - Self-adjacency returns 1.0
  - get_adjacent returns expected neighbors
"""

import pytest

from src.scoring.skill_graph import TechAdjacencyGraph

pytestmark = pytest.mark.unit


@pytest.fixture
def graph():
    return TechAdjacencyGraph()


# ===================================================================
# Synonym expansion / canonicalization
# ===================================================================


class TestSynonymExpansion:
    def test_react_js_to_react(self, graph):
        assert graph.canonicalize("react.js") == "react"

    def test_reactjs_to_react(self, graph):
        assert graph.canonicalize("reactjs") == "react"

    def test_react_js_spaced(self, graph):
        assert graph.canonicalize("react js") == "react"

    def test_k8s_to_kubernetes(self, graph):
        assert graph.canonicalize("k8s") == "kubernetes"

    def test_kube_to_kubernetes(self, graph):
        assert graph.canonicalize("kube") == "kubernetes"

    def test_py_to_python(self, graph):
        assert graph.canonicalize("py") == "python"

    def test_python3_to_python(self, graph):
        assert graph.canonicalize("python3") == "python"

    def test_ts_to_typescript(self, graph):
        assert graph.canonicalize("ts") == "typescript"

    def test_js_to_javascript(self, graph):
        assert graph.canonicalize("js") == "javascript"

    def test_golang_to_go(self, graph):
        assert graph.canonicalize("golang") == "go"

    def test_postgresql_to_postgres(self, graph):
        assert graph.canonicalize("postgresql") == "postgres"

    def test_mongo_to_mongodb(self, graph):
        assert graph.canonicalize("mongo") == "mongodb"

    def test_amazon_web_services_to_aws(self, graph):
        assert graph.canonicalize("amazon web services") == "aws"

    def test_google_cloud_to_gcp(self, graph):
        assert graph.canonicalize("google cloud") == "gcp"

    def test_docker_engine_to_docker(self, graph):
        assert graph.canonicalize("docker engine") == "docker"

    def test_case_insensitivity(self, graph):
        assert graph.canonicalize("React.JS") == "react"
        assert graph.canonicalize("KUBERNETES") == "kubernetes"
        assert graph.canonicalize("Docker") == "docker"

    def test_whitespace_stripping(self, graph):
        assert graph.canonicalize("  react.js  ") == "react"
        assert graph.canonicalize(" k8s ") == "kubernetes"

    def test_cicd_variants(self, graph):
        assert graph.canonicalize("cicd") == "ci/cd"
        assert graph.canonicalize("ci cd") == "ci/cd"
        assert graph.canonicalize("continuous integration") == "ci/cd"

    def test_spring_boot_to_spring(self, graph):
        assert graph.canonicalize("spring boot") == "spring"

    def test_ruby_on_rails_to_rails(self, graph):
        assert graph.canonicalize("ruby on rails") == "rails"


class TestGetEquivalents:
    def test_react_equivalents(self, graph):
        equivs = graph.get_equivalents("react")
        assert "react" in equivs
        assert "react.js" in equivs
        assert "reactjs" in equivs

    def test_kubernetes_equivalents(self, graph):
        equivs = graph.get_equivalents("k8s")
        assert "kubernetes" in equivs
        assert "k8s" in equivs
        assert "kube" in equivs

    def test_aws_equivalents(self, graph):
        equivs = graph.get_equivalents("Amazon Web Services")
        assert "aws" in equivs

    def test_unknown_skill_singleton(self, graph):
        equivs = graph.get_equivalents("obscureskill")
        assert equivs == {"obscureskill"}

    def test_alias_input_resolves(self, graph):
        equivs = graph.get_equivalents("reactjs")
        assert "react" in equivs


# ===================================================================
# Unknown skills
# ===================================================================


class TestUnknownSkills:
    def test_unknown_returns_lowercase(self, graph):
        assert graph.canonicalize("SomeRandomTech") == "somerandomtech"

    def test_unknown_with_spaces(self, graph):
        assert graph.canonicalize("  My Custom Tool  ") == "my custom tool"

    def test_unknown_preserves_structure(self, graph):
        assert graph.canonicalize("Apache Flink") == "apache flink"


# ===================================================================
# Self-adjacency
# ===================================================================


class TestSelfAdjacency:
    def test_self_adjacency_returns_one(self, graph):
        assert graph.adjacency_score("python", "python") == 1.0

    def test_self_adjacency_via_alias(self, graph):
        assert graph.adjacency_score("k8s", "kubernetes") == 1.0

    def test_self_adjacency_react_variants(self, graph):
        assert graph.adjacency_score("react.js", "reactjs") == 1.0

    def test_self_adjacency_case_insensitive(self, graph):
        assert graph.adjacency_score("Python", "python") == 1.0


# ===================================================================
# Adjacency scores
# ===================================================================


class TestAdjacencyScores:
    def test_kubernetes_docker(self, graph):
        assert graph.adjacency_score("kubernetes", "docker") == 0.8

    def test_docker_kubernetes_symmetric(self, graph):
        assert graph.adjacency_score("docker", "kubernetes") == 0.8

    def test_react_vue(self, graph):
        assert graph.adjacency_score("react", "vue") == 0.6

    def test_javascript_typescript(self, graph):
        assert graph.adjacency_score("javascript", "typescript") == pytest.approx(0.85)

    def test_django_flask(self, graph):
        assert graph.adjacency_score("django", "flask") == pytest.approx(0.70)

    def test_flask_fastapi(self, graph):
        assert graph.adjacency_score("flask", "fastapi") == pytest.approx(0.75)

    def test_aws_gcp(self, graph):
        assert graph.adjacency_score("aws", "gcp") == pytest.approx(0.65)

    def test_python_java(self, graph):
        assert graph.adjacency_score("python", "java") == 0.3

    def test_pytorch_tensorflow(self, graph):
        assert graph.adjacency_score("pytorch", "tensorflow") == pytest.approx(0.80)

    def test_postgres_mysql(self, graph):
        assert graph.adjacency_score("postgres", "mysql") == pytest.approx(0.75)

    def test_unrelated_returns_zero(self, graph):
        assert graph.adjacency_score("python", "figma") == 0.0

    def test_unknown_skill_zero(self, graph):
        assert graph.adjacency_score("python", "obscureskill") == 0.0

    def test_adjacency_via_aliases(self, graph):
        assert graph.adjacency_score("k8s", "docker engine") == pytest.approx(0.80)

    def test_react_nextjs(self, graph):
        assert graph.adjacency_score("react", "next.js") == pytest.approx(0.85)

    def test_node_express(self, graph):
        assert graph.adjacency_score("node", "express") == pytest.approx(0.85)

    def test_kafka_rabbitmq(self, graph):
        assert graph.adjacency_score("kafka", "rabbitmq") == pytest.approx(0.65)

    def test_ml_dl(self, graph):
        assert graph.adjacency_score("machine learning", "deep learning") == pytest.approx(0.80)

    def test_symmetry(self, graph):
        assert graph.adjacency_score("react", "vue") == graph.adjacency_score("vue", "react")


# ===================================================================
# get_adjacent
# ===================================================================


class TestGetAdjacent:
    def test_kubernetes_neighbors(self, graph):
        neighbors = graph.get_adjacent("kubernetes")
        assert "docker" in neighbors
        assert "terraform" in neighbors
        assert "ansible" in neighbors
        assert neighbors["docker"] == pytest.approx(0.80)

    def test_react_neighbors(self, graph):
        neighbors = graph.get_adjacent("react")
        assert "vue" in neighbors
        assert "angular" in neighbors
        assert "svelte" in neighbors
        assert "next.js" in neighbors

    def test_python_neighbors(self, graph):
        neighbors = graph.get_adjacent("python")
        assert "java" in neighbors
        assert "go" in neighbors
        assert "django" in neighbors

    def test_alias_input_works(self, graph):
        neighbors = graph.get_adjacent("k8s")
        assert "docker" in neighbors

    def test_unknown_skill_empty(self, graph):
        neighbors = graph.get_adjacent("totally_unknown_tech")
        assert neighbors == {}

    def test_returns_dict_copy(self, graph):
        neighbors1 = graph.get_adjacent("python")
        neighbors2 = graph.get_adjacent("python")
        neighbors1["test_mutation"] = 99.0
        assert "test_mutation" not in neighbors2
