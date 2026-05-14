"""Test Idea-Reality Validation Module"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from brain.validation_engine import (
    IdeaRealityValidator,
    ValidationDecision,
    ValidationScores,
    ValidationReport
)


def create_mock_discovery_metrics() -> dict:
    """Create mock discovery metrics."""
    return {
        "entropy_metrics": {
            "total_entropy": 0.35,
            "question_entropy": 0.4,
            "assumption_uncertainty": 0.3
        }
    }


def create_mock_mcp_validation(
    feasibility: float = 0.8,
    saturation: float = 0.3,
    innovation: float = 0.7
) -> dict:
    """Create mock MCP validation result."""
    return {
        "feasibility": {
            "feasibility_score": feasibility,
            "risks": ["Timeline uncertainty"],
            "blockers": []
        },
        "market_saturation": {
            "saturation_score": saturation,
            "similar_projects": 2,
            "market_gap_identified": True,
            "gaps": ["Better UX", "Faster deployment"]
        },
        "innovation": {
            "innovation_score": innovation,
            "novelty_factors": ["Different architecture", "Novel combination"]
        }
    }


def test_validation_scores_computation():
    """Test score computation."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation()

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)

    assert 0.0 <= scores.feasibility_score <= 1.0
    assert 0.0 <= scores.market_saturation_score <= 1.0
    assert 0.0 <= scores.redundancy_score <= 1.0
    assert 0.0 <= scores.innovation_delta <= 1.0
    assert 0.0 <= scores.viability_score <= 1.0
    assert 0.0 <= scores.confidence <= 1.0


def test_build_decision():
    """Test BUILD decision when metrics are strong."""
    discovery = create_mock_discovery_metrics()
    # Strong metrics: high feasibility, low saturation, high innovation
    mcp = create_mock_mcp_validation(feasibility=0.85, saturation=0.25, innovation=0.8)

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)
    decision = IdeaRealityValidator._make_decision(scores)

    assert decision == ValidationDecision.BUILD


def test_pivot_decision():
    """Test PIVOT decision when metrics are moderate."""
    discovery = create_mock_discovery_metrics()
    # Moderate metrics
    mcp = create_mock_mcp_validation(feasibility=0.6, saturation=0.5, innovation=0.55)

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)
    decision = IdeaRealityValidator._make_decision(scores)

    assert decision == ValidationDecision.PIVOT


def test_kill_decision():
    """Test KILL decision when metrics are weak."""
    discovery = create_mock_discovery_metrics()
    # Weak metrics: low feasibility, high saturation, low innovation
    mcp = create_mock_mcp_validation(feasibility=0.3, saturation=0.8, innovation=0.2)

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)
    decision = IdeaRealityValidator._make_decision(scores)

    assert decision == ValidationDecision.KILL


def test_validation_with_high_entropy():
    """Test that high entropy reduces viability."""
    discovery = {
        "entropy_metrics": {
            "total_entropy": 0.8,  # High uncertainty
            "question_entropy": 0.85,
            "assumption_uncertainty": 0.75
        }
    }
    mcp = create_mock_mcp_validation(feasibility=0.8, saturation=0.3, innovation=0.75)

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)
    # High entropy should reduce viability
    assert scores.viability_score < 0.75


def test_reasoning_for_build():
    """Test reasoning generation for BUILD decision."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation(feasibility=0.85, saturation=0.2, innovation=0.8)

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)
    decision = ValidationDecision.BUILD

    reasoning = IdeaRealityValidator._build_reasoning(scores, decision, mcp)

    assert "strengths" in reasoning
    assert "weaknesses" in reasoning
    assert "recommendations" in reasoning
    assert any("develop" in r.lower() for r in reasoning["recommendations"])


def test_reasoning_for_kill():
    """Test reasoning generation for KILL decision."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation(feasibility=0.2, saturation=0.9, innovation=0.1)

    scores = IdeaRealityValidator._compute_scores(discovery, mcp)
    decision = ValidationDecision.KILL

    reasoning = IdeaRealityValidator._build_reasoning(scores, decision, mcp)

    assert "weaknesses" in reasoning
    assert len(reasoning["weaknesses"]) > 0


def test_full_validation():
    """Test full validation flow."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation()

    result = IdeaRealityValidator.validate(
        "Build a collaborative AI tool",
        discovery,
        mcp
    )

    assert "decision" in result
    assert result["decision"] in ["BUILD", "PIVOT", "KILL"]
    assert "scores" in result
    assert "reasoning" in result
    assert "timestamp" in result


def test_validation_report_build():
    """Test ValidationReport for BUILD decision."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation(feasibility=0.85, saturation=0.2, innovation=0.8)

    report = ValidationReport("Test idea", discovery, mcp)

    assert report.should_proceed_to_prd() is True
    assert report.should_pivot() is False
    assert report.should_kill() is False


def test_validation_report_pivot():
    """Test ValidationReport for PIVOT decision."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation(feasibility=0.6, saturation=0.5, innovation=0.55)

    report = ValidationReport("Test idea", discovery, mcp)

    assert report.should_proceed_to_prd() is False
    assert report.should_pivot() is True
    assert report.should_kill() is False


def test_validation_report_json():
    """Test ValidationReport exports as JSON."""
    discovery = create_mock_discovery_metrics()
    mcp = create_mock_mcp_validation()

    report = ValidationReport("Test idea", discovery, mcp)
    json_output = report.to_json()

    assert "project_description" in json_output
    assert "discovery_metrics" in json_output
    assert "validation_result" in json_output
    assert "next_step" in json_output


def test_scores_to_dict():
    """Test scores serialize to dict."""
    scores = ValidationScores(
        feasibility_score=0.8,
        market_saturation_score=0.3,
        redundancy_score=0.35,
        innovation_delta=0.75,
        viability_score=0.72,
        confidence=0.8
    )

    scores_dict = scores.to_dict()

    assert all(isinstance(v, float) for v in scores_dict.values())
    assert scores_dict["feasibility"] == 0.8
    assert scores_dict["viability"] == 0.72


def test_confidence_varies_with_entropy():
    """Test confidence reflects certainty."""
    # Low entropy = high confidence
    discovery_low = {"entropy_metrics": {"total_entropy": 0.1}}
    mcp = create_mock_mcp_validation()

    scores_low = IdeaRealityValidator._compute_scores(discovery_low, mcp)

    # High entropy = low confidence
    discovery_high = {"entropy_metrics": {"total_entropy": 0.8}}
    scores_high = IdeaRealityValidator._compute_scores(discovery_high, mcp)

    assert scores_low.confidence > scores_high.confidence


if __name__ == "__main__":
    test_validation_scores_computation()
    test_build_decision()
    test_pivot_decision()
    test_kill_decision()
    test_validation_with_high_entropy()
    test_reasoning_for_build()
    test_reasoning_for_kill()
    test_full_validation()
    test_validation_report_build()
    test_validation_report_pivot()
    test_validation_report_json()
    test_scores_to_dict()
    test_confidence_varies_with_entropy()
    print("✅ All validation engine tests passed")
