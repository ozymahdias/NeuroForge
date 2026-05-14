"""Test Discovery Engine and Entropy System"""

import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain.discovery_engine import (
    OpenQuestion,
    Assumption,
    QuestionSeverity,
    EntropyCalculator,
    OpenQuestionGenerator,
    AssumptionBuilder,
    DiscoveryOutput
)
from brain.idea_reality_mcp import DiscoveryMCPAdapter, MockIdeaRealityValidator


def test_open_question_creation():
    """Test creating open questions."""
    q = OpenQuestion(
        id="q_1",
        question="Who is the user?",
        severity=QuestionSeverity.CRITICAL.value,
        domain="requirements",
        discovered_at="2026-05-14T00:00:00"
    )
    assert q.id == "q_1"
    assert q.severity == "CRITICAL"


def test_assumption_creation():
    """Test creating assumptions."""
    a = AssumptionBuilder.create_assumption(
        assumption="Users have stable internet",
        confidence=0.8,
        dependencies=[]
    )
    assert a.confidence == 0.8
    assert 0.0 <= a.confidence <= 1.0


def test_assumption_confidence_validation():
    """Test assumption confidence bounds."""
    try:
        AssumptionBuilder.create_assumption(
            assumption="Invalid assumption",
            confidence=1.5
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Confidence must be between" in str(e)


def test_entropy_calculation_empty():
    """Test entropy with no questions or assumptions."""
    metrics = EntropyCalculator.calculate_entropy([], [])
    assert metrics["total_entropy"] == 0.0
    assert metrics["question_entropy"] == 0.0


def test_entropy_calculation_with_critical_questions():
    """Test entropy rises with critical questions."""
    critical_q = OpenQuestion(
        id="q_1",
        question="Who is the user?",
        severity=QuestionSeverity.CRITICAL.value,
        domain="requirements",
        discovered_at="2026-05-14T00:00:00"
    )

    metrics = EntropyCalculator.calculate_entropy([critical_q], [])
    assert metrics["total_entropy"] > 0.0
    assert metrics["critical_blockers"] == 1


def test_entropy_calculation_with_assumptions():
    """Test entropy drops with high-confidence assumptions."""
    q = OpenQuestion(
        id="q_1",
        question="Test?",
        severity=QuestionSeverity.MEDIUM.value,
        domain="test",
        discovered_at="2026-05-14T00:00:00"
    )

    high_conf = AssumptionBuilder.create_assumption(
        assumption="High confidence assumption",
        confidence=0.95
    )

    metrics = EntropyCalculator.calculate_entropy([q], [high_conf])
    low_conf = 1.0 - 0.95
    assert metrics["assumption_uncertainty"] <= low_conf


def test_question_generator():
    """Test generating questions from description."""
    description = "Build a user-facing app for scale with security"

    questions = OpenQuestionGenerator.generate_from_description(description)
    assert len(questions) > 0

    # Should have picked up user, scale, security keywords
    severities = [q.severity for q in questions]
    assert QuestionSeverity.CRITICAL.value in severities


def test_custom_question():
    """Test adding custom questions."""
    questions = []
    questions = OpenQuestionGenerator.add_custom_question(
        questions,
        "What's the deployment strategy?",
        QuestionSeverity.HIGH,
        "architecture"
    )

    assert len(questions) == 1
    assert "deployment" in questions[0].question.lower()


def test_assumption_dependency_validation():
    """Test assumptions can track dependencies."""
    assumption = AssumptionBuilder.create_assumption(
        assumption="Platform exists",
        confidence=0.7,
        dependencies=["q_1", "q_2"]
    )

    questions = [
        OpenQuestion("q_1", "Exists?", "CRITICAL", "req", "2026-05-14T00:00:00"),
        OpenQuestion("q_3", "Other?", "MEDIUM", "arch", "2026-05-14T00:00:00")
    ]

    # q_1 is resolved, q_2 is not
    is_valid = AssumptionBuilder.validate_assumption(assumption, questions)
    # Validation only checks if dependencies are in open_questions
    # If q_1 and q_2 are open, they're unresolved
    assert not is_valid


def test_discovery_output_json():
    """Test DiscoveryOutput generates valid JSON."""
    output = DiscoveryOutput()

    q = OpenQuestion(
        "q_1",
        "Who uses this?",
        QuestionSeverity.CRITICAL.value,
        "requirements",
        "2026-05-14T00:00:00"
    )
    output.add_question(q)

    a = AssumptionBuilder.create_assumption("Users exist", 0.9)
    output.add_assumption(a)

    json_output = output.to_json()
    assert "open_questions" in json_output
    assert "assumptions" in json_output
    assert "entropy_metrics" in json_output
    assert "ready_for_prd" in json_output
    assert len(json_output["open_questions"]) == 1


def test_idea_reality_adapter():
    """Test MCP adapter integration."""
    adapter = DiscoveryMCPAdapter(MockIdeaRealityValidator())

    validation = adapter.run_discovery_validation(
        "Build a scalable web app for e-commerce"
    )

    assert "feasibility" in validation
    assert "market_saturation" in validation
    assert "innovation" in validation
    assert validation["feasibility"]["feasibility_score"] > 0.0


def test_decision_factors():
    """Test extraction of decision factors."""
    adapter = DiscoveryMCPAdapter(MockIdeaRealityValidator())

    validation = adapter.run_discovery_validation("Test idea")
    factors = adapter.get_decision_factors(validation)

    assert "feasibility_score" in factors
    assert "market_saturation_score" in factors
    assert "innovation_score" in factors
    assert "market_gap_exists" in factors


if __name__ == "__main__":
    test_open_question_creation()
    test_assumption_creation()
    test_assumption_confidence_validation()
    test_entropy_calculation_empty()
    test_entropy_calculation_with_critical_questions()
    test_entropy_calculation_with_assumptions()
    test_question_generator()
    test_custom_question()
    test_assumption_dependency_validation()
    test_discovery_output_json()
    test_idea_reality_adapter()
    test_decision_factors()
    print("✅ All discovery engine tests passed")
