"""Unit tests for the resume parser agent (no external deps).

Covers:
  - Skill normalization edge cases
  - ResumeParserAgent instantiation (agent_name, input_type, output_type)
  - ResumeParserInput validation
"""

import pytest
from pydantic import ValidationError

from src.agents.resume_parser import ResumeParserAgent, ResumeParserInput
from src.models.schemas import CandidateProfile
from src.scoring.normalizer import normalize_skill, normalize_skills

pytestmark = pytest.mark.unit


# ===================================================================
# normalize_skill edge cases
# ===================================================================


class TestNormalizeSkill:
    def test_react_js(self):
        assert normalize_skill("react.js") == "React"

    def test_reactjs(self):
        assert normalize_skill("reactjs") == "React"

    def test_k8s(self):
        assert normalize_skill("k8s") == "Kubernetes"

    def test_aws(self):
        assert normalize_skill("Amazon Web Services") == "AWS"

    def test_aws_lowercase(self):
        assert normalize_skill("aws") == "AWS"

    def test_golang(self):
        assert normalize_skill("golang") == "Go"

    def test_unknown_preserves_original(self):
        assert normalize_skill("SomeNewFramework") == "SomeNewFramework"

    def test_whitespace_stripped(self):
        assert normalize_skill("  react.js  ") == "React"

    def test_case_insensitive_lookup(self):
        # "python3" is a known alias -> "Python"; bare "python" is not in dict
        assert normalize_skill("python3") == "Python"
        assert normalize_skill("Python3") == "Python"
        # Unknown forms pass through with original casing (stripped)
        assert normalize_skill("PYTHON") == "PYTHON"
        assert normalize_skill("python") == "python"

    def test_typescript_variants(self):
        assert normalize_skill("typescript") == "TypeScript"
        assert normalize_skill("ts") == "TypeScript"

    def test_node_variants(self):
        assert normalize_skill("node.js") == "Node.js"
        assert normalize_skill("nodejs") == "Node.js"
        assert normalize_skill("node") == "Node.js"

    def test_docker(self):
        assert normalize_skill("docker") == "Docker"

    def test_postgres_variants(self):
        assert normalize_skill("postgresql") == "PostgreSQL"
        assert normalize_skill("postgres") == "PostgreSQL"
        assert normalize_skill("pg") == "PostgreSQL"

    def test_mongodb_variants(self):
        assert normalize_skill("mongodb") == "MongoDB"
        assert normalize_skill("mongo") == "MongoDB"

    def test_cicd_variants(self):
        assert normalize_skill("ci/cd") == "CI/CD"
        assert normalize_skill("cicd") == "CI/CD"

    def test_ml_variants(self):
        assert normalize_skill("machine learning") == "Machine Learning"
        assert normalize_skill("ml") == "Machine Learning"

    def test_tensorflow_variants(self):
        assert normalize_skill("tensorflow") == "TensorFlow"

    def test_pytorch_variants(self):
        assert normalize_skill("pytorch") == "PyTorch"
        assert normalize_skill("torch") == "PyTorch"

    def test_fastapi(self):
        assert normalize_skill("fast api") == "FastAPI"
        assert normalize_skill("fastapi") == "FastAPI"

    def test_dotnet_variants(self):
        assert normalize_skill(".net") == ".NET"
        assert normalize_skill("dotnet") == ".NET"

    def test_cpp_variants(self):
        assert normalize_skill("c++") == "C++"
        assert normalize_skill("cpp") == "C++"

    def test_csharp_variants(self):
        assert normalize_skill("c#") == "C#"
        assert normalize_skill("csharp") == "C#"

    def test_ruby_on_rails_variants(self):
        assert normalize_skill("ruby on rails") == "Ruby on Rails"
        assert normalize_skill("rails") == "Ruby on Rails"
        assert normalize_skill("ror") == "Ruby on Rails"

    def test_elasticsearch(self):
        assert normalize_skill("elastic search") == "Elasticsearch"
        assert normalize_skill("elasticsearch") == "Elasticsearch"

    def test_graphql(self):
        assert normalize_skill("graphql") == "GraphQL"

    def test_rest_api(self):
        assert normalize_skill("rest api") == "REST"
        assert normalize_skill("restful") == "REST"

    def test_tailwind(self):
        assert normalize_skill("tailwindcss") == "Tailwind CSS"
        assert normalize_skill("tailwind css") == "Tailwind CSS"

    def test_kafka(self):
        assert normalize_skill("apache kafka") == "Kafka"

    def test_spark(self):
        assert normalize_skill("apache spark") == "Spark"
        assert normalize_skill("pyspark") == "Spark"

    def test_empty_string_returns_empty(self):
        result = normalize_skill("")
        assert result == ""

    def test_whitespace_only(self):
        result = normalize_skill("   ")
        assert result == ""


# ===================================================================
# normalize_skills (list-level)
# ===================================================================


class TestNormalizeSkills:
    def test_deduplicates_case_variants(self):
        result = normalize_skills(["Python", "python", "PYTHON"])
        python_entries = [s for s in result if s.lower() == "python"]
        assert len(python_entries) == 1

    def test_preserves_order(self):
        result = normalize_skills(["react.js", "k8s", "python3"])
        assert result[0] == "React"
        assert result[1] == "Kubernetes"
        assert result[2] == "Python"

    def test_empty_list(self):
        assert normalize_skills([]) == []

    def test_single_skill(self):
        result = normalize_skills(["aws"])
        assert result == ["AWS"]

    def test_mixed_known_unknown(self):
        result = normalize_skills(["python3", "ObscureTool", "k8s"])
        assert "Python" in result
        assert "ObscureTool" in result
        assert "Kubernetes" in result

    def test_deduplicates_aliases(self):
        result = normalize_skills(["react.js", "reactjs", "React"])
        react_entries = [s for s in result if "react" in s.lower()]
        assert len(react_entries) == 1

    def test_deduplicates_kubernetes_aliases(self):
        result = normalize_skills(["k8s", "kubernetes", "Kubernetes"])
        k8s_entries = [s for s in result if "kubernetes" in s.lower()]
        assert len(k8s_entries) == 1


# ===================================================================
# ResumeParserAgent instantiation
# ===================================================================


class TestAgentInstantiation:
    def test_agent_name(self):
        agent = ResumeParserAgent()
        assert agent.agent_name == "resume_parser"

    def test_input_type(self):
        agent = ResumeParserAgent()
        assert agent.input_type is ResumeParserInput

    def test_output_type(self):
        agent = ResumeParserAgent()
        assert agent.output_type is CandidateProfile

    def test_persona_set(self):
        agent = ResumeParserAgent()
        assert "resume" in agent.persona.lower() or "parser" in agent.persona.lower()

    def test_memory_starts_empty(self):
        agent = ResumeParserAgent()
        assert agent.memory == {}

    def test_tools_empty_by_default(self):
        agent = ResumeParserAgent()
        assert agent.get_tools_for_llm() == []


# ===================================================================
# ResumeParserInput validation
# ===================================================================


class TestResumeParserInput:
    def test_with_path(self):
        inp = ResumeParserInput(pdf_path="/tmp/test.pdf", user_id="u1")
        assert inp.pdf_path == "/tmp/test.pdf"
        assert inp.pdf_bytes is None

    def test_with_bytes(self):
        inp = ResumeParserInput(pdf_bytes=b"fake pdf", user_id="u1")
        assert inp.pdf_bytes == b"fake pdf"
        assert inp.pdf_path is None

    def test_both_none_valid(self):
        # Both can be None at construction time; validation happens at runtime
        inp = ResumeParserInput(user_id="u1")
        assert inp.pdf_bytes is None
        assert inp.pdf_path is None

    def test_user_id_required(self):
        with pytest.raises(ValidationError):
            ResumeParserInput(pdf_path="/tmp/test.pdf")

    def test_user_id_stored(self):
        inp = ResumeParserInput(user_id="user_abc_123", pdf_path="/tmp/x.pdf")
        assert inp.user_id == "user_abc_123"

    def test_bytes_type(self):
        inp = ResumeParserInput(pdf_bytes=b"\x00\x01\x02", user_id="u1")
        assert isinstance(inp.pdf_bytes, bytes)

    def test_path_type(self):
        inp = ResumeParserInput(pdf_path="/some/path.pdf", user_id="u1")
        assert isinstance(inp.pdf_path, str)
