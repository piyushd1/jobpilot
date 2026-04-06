"""Unit tests for the Tech Adjacency Graph."""

import pytest

from src.scoring.skill_graph import TechAdjacencyGraph

pytestmark = pytest.mark.unit


@pytest.fixture
def graph():
    return TechAdjacencyGraph()


def test_synonym_expansion_react(graph):
    equivalents = graph.get_equivalents("react.js")
    assert "react" in equivalents
    assert "reactjs" in equivalents


def test_synonym_expansion_kubernetes(graph):
    equivalents = graph.get_equivalents("k8s")
    assert "kubernetes" in equivalents


def test_synonym_expansion_aws(graph):
    equivalents = graph.get_equivalents("Amazon Web Services")
    assert "aws" in equivalents


def test_canonicalize_normalizes(graph):
    assert graph.canonicalize("React.js") == "react"
    assert graph.canonicalize("K8s") == "kubernetes"
    assert graph.canonicalize("golang") == "go"


def test_unknown_skill_returns_lowercase(graph):
    assert graph.canonicalize("SomeRandomTech") == "somerandomtech"


def test_self_adjacency_returns_1(graph):
    assert graph.adjacency_score("python", "python") == 1.0
    assert graph.adjacency_score("k8s", "kubernetes") == 1.0


def test_adjacency_kubernetes_docker(graph):
    score = graph.adjacency_score("kubernetes", "docker")
    assert score == 0.8


def test_adjacency_react_vue(graph):
    score = graph.adjacency_score("react", "vue")
    assert score == 0.6


def test_adjacency_python_java(graph):
    score = graph.adjacency_score("python", "java")
    assert score == 0.3


def test_adjacency_unrelated_returns_zero(graph):
    score = graph.adjacency_score("python", "figma")
    assert score == 0.0


def test_get_adjacent_python(graph):
    adjacent = graph.get_adjacent("python")
    assert "java" in adjacent
    assert "go" in adjacent
    assert "django" in adjacent


def test_get_adjacent_empty_for_unknown(graph):
    adjacent = graph.get_adjacent("totally_unknown_tech")
    assert adjacent == {}


def test_adjacency_symmetric(graph):
    assert graph.adjacency_score("react", "vue") == graph.adjacency_score("vue", "react")
