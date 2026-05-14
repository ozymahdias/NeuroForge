"""Unit tests - Validation Engine correctness"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from brain.validation_engine import (
    IdeaRealityValidator,
    ValidationScores,
    ValidationReport,
    ValidationDecision
)


class TestValidationScores:
    """Test ValidationScores dataclass."""

    def test_scores_creation(self):
        """Can create ValidationScores."""
        scores = ValidationScores(
            feasibility_score=0.8,
            market_saturation_score=0.3,
            redundancy_score=0.2,
            innovation_delta=0.9,
            viability_score=0.7,
            confidence=0.8
        )

        assert scores.feasibility_score == 0.8
        assert scores.confidence == 0.8

    def test_scores_to_dict(self):
        """Can convert scores to dict."""
        scores = ValidationScores(
            feasibility_score=0.85,
            market_saturation_score=0.25,
            redundancy_score=0.15,
            innovation_delta=0.95,
            viability_score=0.75,
            confidence=0.85
        )

        data = scores.to_dict()
        assert data["feasibility"] == 0.85
        assert data["confidence"] == 0.85

    def test_scores_rounded(self):
        """Scores are rounded to 3 decimal places."""
        scores = ValidationScores(
            feasibility_score=0.8567,
            market_saturation_score=0.2567,
            redundancy_score=0.1567,
            innovation_delta=0.9567,
            viability_score=0.7567,
            confidence=0.8567
        )

        data = scores.to_dict()
        assert data["feasibility"] == 0.857
        assert data["confidence"] == 0.857


class TestScoreComputation:
    """Test score calculation logic."""

    def test_compute_scores_high_feasibility(self):
        """High feasibility scores contribute to viability."""
        discovery_metrics = {
            "entropy_metrics": {"total_entropy": 0.1}
        }
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.9},
            "market_saturation": {"saturation_score": 0.4},
            "innovation": {"innovation_score": 0.8}
        }

        scores = IdeaRealityValidator._compute_scores(
            discovery_metrics,
            mcp_validation
        )

        assert scores.feasibility_score == 0.9
        assert scores.viability_score > 0.6  # High feasibility pushes viability

    def test_compute_scores_high_entropy(self):
        """High entropy reduces viability."""
        discovery_metrics = {
            "entropy_metrics": {"total_entropy": 0.9}
        }
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.8},
            "market_saturation": {"saturation_score": 0.3},
            "innovation": {"innovation_score": 0.9}
        }

        scores = IdeaRealityValidator._compute_scores(
            discovery_metrics,
            mcp_validation
        )

        # High entropy = low confidence
        assert scores.confidence < 0.5

    def test_redundancy_calculated_correctly(self):
        """Redundancy = (market_sat + (1 - innovation)) / 2."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.5}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.5},
            "market_saturation": {"saturation_score": 0.6},
            "innovation": {"innovation_score": 0.8}
        }

        scores = IdeaRealityValidator._compute_scores(
            discovery_metrics,
            mcp_validation
        )

        # redundancy = (0.6 + (1 - 0.8)) / 2 = (0.6 + 0.2) / 2 = 0.4
        assert scores.redundancy_score == 0.4


class TestDecisionLogic:
    """Test BUILD/PIVOT/KILL decision making."""

    def test_build_decision_high_viability(self):
        """HIGH viability → BUILD decision."""
        scores = ValidationScores(
            feasibility_score=0.9,
            market_saturation_score=0.2,
            redundancy_score=0.1,
            innovation_delta=0.95,
            viability_score=0.8,  # > BUILD_THRESHOLD (0.65)
            confidence=0.9
        )

        decision = IdeaRealityValidator._make_decision(scores)
        assert decision == ValidationDecision.BUILD

    def test_pivot_decision_medium_viability(self):
        """MEDIUM viability → PIVOT decision."""
        scores = ValidationScores(
            feasibility_score=0.6,
            market_saturation_score=0.5,
            redundancy_score=0.5,
            innovation_delta=0.6,
            viability_score=0.55,  # Between PIVOT_THRESHOLD (0.4) and BUILD_THRESHOLD (0.65)
            confidence=0.5
        )

        decision = IdeaRealityValidator._make_decision(scores)
        assert decision == ValidationDecision.PIVOT

    def test_kill_decision_low_viability(self):
        """LOW viability → KILL decision."""
        scores = ValidationScores(
            feasibility_score=0.3,
            market_saturation_score=0.8,
            redundancy_score=0.85,
            innovation_delta=0.2,
            viability_score=0.25,  # < PIVOT_THRESHOLD (0.4)
            confidence=0.2
        )

        decision = IdeaRealityValidator._make_decision(scores)
        assert decision == ValidationDecision.KILL


class TestValidatorWorkflow:
    """Test complete validation workflow."""

    def test_validate_returns_dict(self):
        """Validate returns structured dict."""
        discovery_metrics = {
            "entropy_metrics": {"total_entropy": 0.2}
        }
        mcp_validation = {
            "feasibility": {
                "feasibility_score": 0.8,
                "risks": []
            },
            "market_saturation": {
                "saturation_score": 0.3,
                "gaps": []
            },
            "innovation": {
                "innovation_score": 0.85
            }
        }

        result = IdeaRealityValidator.validate(
            "Test project",
            discovery_metrics,
            mcp_validation
        )

        assert "decision" in result
        assert "scores" in result
        assert "reasoning" in result
        assert "timestamp" in result

    def test_validate_includes_scores(self):
        """Validation includes all scores."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.3}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.7},
            "market_saturation": {"saturation_score": 0.4},
            "innovation": {"innovation_score": 0.8}
        }

        result = IdeaRealityValidator.validate(
            "Test",
            discovery_metrics,
            mcp_validation
        )

        scores = result["scores"]
        assert "feasibility" in scores
        assert "market_saturation" in scores
        assert "innovation_delta" in scores
        assert "viability" in scores
        assert "confidence" in scores

    def test_validate_high_quality_idea(self):
        """High quality idea gets BUILD decision."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.15}}
        mcp_validation = {
            "feasibility": {
                "feasibility_score": 0.85,
                "risks": []
            },
            "market_saturation": {
                "saturation_score": 0.25,
                "gaps": ["Clear market gap"]
            },
            "innovation": {
                "innovation_score": 0.90
            }
        }

        result = IdeaRealityValidator.validate(
            "Great idea",
            discovery_metrics,
            mcp_validation
        )

        assert result["decision"] == "BUILD"
        assert result["scores"]["viability"] > 0.65


class TestValidationReport:
    """Test ValidationReport wrapper."""

    def test_report_creation(self):
        """Can create ValidationReport."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.3}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.7},
            "market_saturation": {"saturation_score": 0.4},
            "innovation": {"innovation_score": 0.8}
        }

        report = ValidationReport(
            "Test Project",
            discovery_metrics,
            mcp_validation
        )

        assert report.project_description == "Test Project"

    def test_report_should_proceed_to_prd(self):
        """Report correctly identifies BUILD decision."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.1}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.9},
            "market_saturation": {"saturation_score": 0.2},
            "innovation": {"innovation_score": 0.95}
        }

        report = ValidationReport(
            "High quality idea",
            discovery_metrics,
            mcp_validation
        )

        assert report.should_proceed_to_prd() is True
        assert report.should_pivot() is False
        assert report.should_kill() is False

    def test_report_should_pivot(self):
        """Report correctly identifies PIVOT decision."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.5}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.5},
            "market_saturation": {"saturation_score": 0.6},
            "innovation": {"innovation_score": 0.5}
        }

        report = ValidationReport(
            "Medium idea",
            discovery_metrics,
            mcp_validation
        )

        assert report.should_pivot() is True
        assert report.should_proceed_to_prd() is False
        assert report.should_kill() is False

    def test_report_should_kill(self):
        """Report correctly identifies KILL decision."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.8}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.3},
            "market_saturation": {"saturation_score": 0.9},
            "innovation": {"innovation_score": 0.2}
        }

        report = ValidationReport(
            "Bad idea",
            discovery_metrics,
            mcp_validation
        )

        assert report.should_kill() is True
        assert report.should_pivot() is False
        assert report.should_proceed_to_prd() is False

    def test_report_to_json(self):
        """Report can be exported to JSON."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.2}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.8},
            "market_saturation": {"saturation_score": 0.3},
            "innovation": {"innovation_score": 0.85}
        }

        report = ValidationReport(
            "Test Project",
            discovery_metrics,
            mcp_validation
        )

        json_data = report.to_json()
        assert "project_description" in json_data
        assert "validation_result" in json_data
        assert "next_step" in json_data


class TestReasoningGeneration:
    """Test reasoning generation for decisions."""

    def test_reasoning_includes_strengths_and_weaknesses(self):
        """Reasoning includes identified strengths and weaknesses."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.2}}
        mcp_validation = {
            "feasibility": {
                "feasibility_score": 0.8,
                "risks": ["Risk 1", "Risk 2"]
            },
            "market_saturation": {
                "saturation_score": 0.3,
                "gaps": ["Gap 1"]
            },
            "innovation": {
                "innovation_score": 0.85
            }
        }

        result = IdeaRealityValidator.validate(
            "Test",
            discovery_metrics,
            mcp_validation
        )

        reasoning = result["reasoning"]
        assert "strengths" in reasoning
        assert "weaknesses" in reasoning
        assert "recommendations" in reasoning

    def test_reasoning_includes_build_recommendations(self):
        """BUILD decision includes proceed recommendations."""
        discovery_metrics = {"entropy_metrics": {"total_entropy": 0.1}}
        mcp_validation = {
            "feasibility": {"feasibility_score": 0.85},
            "market_saturation": {"saturation_score": 0.25},
            "innovation": {"innovation_score": 0.9}
        }

        result = IdeaRealityValidator.validate(
            "Good idea",
            discovery_metrics,
            mcp_validation
        )

        reasoning = result["reasoning"]
        assert result["decision"] == "BUILD"
        assert any("Proceed" in str(r) for r in reasoning["recommendations"])


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
