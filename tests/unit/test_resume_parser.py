"""Unit tests for the resume parser agent (no external deps)."""

import pytest

from src.scoring.normalizer import normalize_skill, normalize_skills
from src.agents.resume_parser import ResumeParserAgent, ResumeParserInput
from src.models.schemas import CandidateProfile

pytestmark = pytest.mark.unit


# --- Skill normalization ---

def test_normalize_react_js():
    assert normalize_skill("react.js") == "React"


def test_normalize_k8s():
    assert normalize_skill("k8s") == "Kubernetes"


def test_normalize_aws():
    assert normalize_skill("Amazon Web Services") == "AWS"


def test_normalize_golang():
    assert normalize_skill("golang") == "Go"


def test_normalize_unknown_preserves():
    assert normalize_skill("SomeNewFramework") == "SomeNewFramework"


def test_normalize_skills_deduplicates():
    result = normalize_skills(["Python", "python", "PYTHON"])
    python_entries = [s for s in result if s.lower() == "python"]
    assert len(python_entries) == 1


def test_normalize_skills_preserves_order():
    result = normalize_skills(["react.js", "k8s", "python"])
    assert result[0] == "React"
    assert result[1] == "Kubernetes"


# --- Agent instantiation ---

def test_agent_name():
    agent = ResumeParserAgent()
    assert agent.agent_name == "resume_parser"


def test_agent_input_type():
    agent = ResumeParserAgent()
    assert agent.input_type is ResumeParserInput


def test_agent_output_type():
    agent = ResumeParserAgent()
    assert agent.output_type is CandidateProfile


# --- Input validation ---

def test_input_with_path():
    inp = ResumeParserInput(pdf_path="/tmp/test.pdf", user_id="u1")
    assert inp.pdf_path == "/tmp/test.pdf"
    assert inp.pdf_bytes is None


def test_input_with_bytes():
    inp = ResumeParserInput(pdf_bytes=b"fake pdf", user_id="u1")
    assert inp.pdf_bytes == b"fake pdf"
