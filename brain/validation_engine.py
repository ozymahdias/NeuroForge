"""Idea-Reality Validation Module - Decision engine"""

from typing import Dict, Any, Optional
from enum import Enum
from dataclasses import dataclass
from datetime import datetime


class ValidationDecision(Enum):
    """High-level decisions from validation."""
    BUILD = "BUILD"
    PIVOT = "PIVOT"
    KILL = "KILL"


@dataclass
class ValidationScores:
    """Computed validation scores."""
    feasibility_score: float  # 0.0-1.0: can we build it?
    market_saturation_score: float  # 0.0-1.0: is market saturated?
    redundancy_score: float  # 0.0-1.0: how redundant with existing?
    innovation_delta: float  # 0.0-1.0: how novel/different?
    viability_score: float  # 0.0-1.0: combined viability
    confidence: float  # 0.0-1.0: confidence in decision

    def to_dict(self) -> Dict[str, float]:
        return {
            "feasibility": round(self.feasibility_score, 3),
            "market_saturation": round(self.market_saturation_score, 3),
            "redundancy": round(self.redundancy_score, 3),
            "innovation_delta": round(self.innovation_delta, 3),
            "viability": round(self.viability_score, 3),
            "confidence": round(self.confidence, 3),
        }


class IdeaRealityValidator:
    """Validates ideas against reality metrics."""

    # Decision thresholds
    BUILD_THRESHOLD = 0.65
    PIVOT_THRESHOLD = 0.40
    KILL_THRESHOLD = 0.40

    @staticmethod
    def validate(
        project_description: str,
        discovery_metrics: Dict[str, Any],
        mcp_validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Validate idea against reality metrics.
        Combines discovery entropy, MCP feasibility/market checks, and innovation.
        """
        scores = IdeaRealityValidator._compute_scores(
            discovery_metrics,
            mcp_validation
        )

        decision = IdeaRealityValidator._make_decision(scores)
        reasoning = IdeaRealityValidator._build_reasoning(
            scores, decision, mcp_validation
        )

        return {
            "decision": decision.value,
            "scores": scores.to_dict(),
            "reasoning": reasoning,
            "timestamp": datetime.now().isoformat(),
            "validation_level": "full"
        }

    @staticmethod
    def _compute_scores(
        discovery_metrics: Dict[str, Any],
        mcp_validation: Dict[str, Any],
    ) -> ValidationScores:
        """Compute comprehensive validation scores."""

        # Extract MCP scores
        feasibility = mcp_validation.get("feasibility", {}).get("feasibility_score", 0.5)
        market_sat = mcp_validation.get("market_saturation", {}).get("saturation_score", 0.5)
        innovation = mcp_validation.get("innovation", {}).get("innovation_score", 0.5)

        # Redundancy = market saturation + (1 - innovation)
        redundancy = (market_sat + (1.0 - innovation)) / 2.0

        # Entropy from discovery (inverse: lower entropy is better)
        entropy = discovery_metrics.get("entropy_metrics", {}).get("total_entropy", 0.5)
        entropy_factor = 1.0 - entropy  # Inverse: high entropy = bad signal

        # Viability = weighted combination
        # High feasibility, low redundancy, high innovation, low entropy = good
        viability = (
            (feasibility * 0.35) +
            ((1.0 - redundancy) * 0.25) +
            (innovation * 0.25) +
            (entropy_factor * 0.15)
        )

        # Confidence = how certain are we?
        # Higher when: entropy is low, agreement between metrics
        metric_agreement = 1.0 - abs(feasibility - innovation)
        confidence = (entropy_factor * 0.5) + (metric_agreement * 0.5)

        return ValidationScores(
            feasibility_score=feasibility,
            market_saturation_score=market_sat,
            redundancy_score=redundancy,
            innovation_delta=innovation,
            viability_score=viability,
            confidence=confidence,
        )

    @staticmethod
    def _make_decision(scores: ValidationScores) -> ValidationDecision:
        """Make BUILD/PIVOT/KILL decision based on scores."""

        # Decision logic
        if scores.viability_score >= IdeaRealityValidator.BUILD_THRESHOLD:
            # Good idea - proceed
            return ValidationDecision.BUILD

        elif scores.viability_score >= IdeaRealityValidator.PIVOT_THRESHOLD:
            # Viable but needs adjustment
            return ValidationDecision.PIVOT

        else:
            # Not viable
            return ValidationDecision.KILL

    @staticmethod
    def _build_reasoning(
        scores: ValidationScores,
        decision: ValidationDecision,
        mcp_validation: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build human-readable reasoning for the decision."""

        strengths = []
        weaknesses = []
        recommendations = []

        # Analyze feasibility
        if scores.feasibility_score > 0.7:
            strengths.append("High feasibility - team can build this")
        elif scores.feasibility_score < 0.4:
            weaknesses.append("Low feasibility - significant technical risks")
            if decision == ValidationDecision.PIVOT:
                recommendations.append("Consider reducing scope or timeline")

        # Analyze market saturation
        if scores.market_saturation_score < 0.4:
            strengths.append("Low market saturation - clear differentiation opportunity")
        elif scores.market_saturation_score > 0.7:
            weaknesses.append("High market saturation - difficult to differentiate")

        # Analyze innovation
        if scores.innovation_delta > 0.7:
            strengths.append("High innovation delta - clear novelty")
        else:
            weaknesses.append("Low innovation - incremental improvement")

        # Analyze redundancy
        if scores.redundancy_score > 0.6:
            weaknesses.append("High redundancy with existing solutions")
        else:
            strengths.append("Low redundancy - fills a gap")

        # Feasibility blockers
        blockers = mcp_validation.get("feasibility", {}).get("risks", [])
        if blockers:
            weaknesses.extend([f"Risk: {risk}" for risk in blockers[:2]])

        # Market gaps
        gaps = mcp_validation.get("market_saturation", {}).get("gaps", [])
        if gaps:
            strengths.extend([f"Gap: {gap}" for gap in gaps[:2]])

        # Build recommendations
        if decision == ValidationDecision.BUILD:
            recommendations.append("Proceed with development")
            recommendations.append("Validate assumptions with early users")
        elif decision == ValidationDecision.PIVOT:
            recommendations.append("Pivot scope or positioning")
            recommendations.append("Address identified weaknesses before build")
        else:  # KILL
            recommendations.append("Consider shelving or major rethink")

        return {
            "decision": decision.value,
            "strengths": strengths[:3],
            "weaknesses": weaknesses[:3],
            "recommendations": recommendations,
            "confidence_level": "high" if scores.confidence > 0.7 else "medium" if scores.confidence > 0.4 else "low"
        }


class ValidationReport:
    """Structured validation report."""

    def __init__(
        self,
        project_description: str,
        discovery_metrics: Dict[str, Any],
        mcp_validation: Dict[str, Any],
    ):
        self.project_description = project_description
        self.discovery_metrics = discovery_metrics
        self.mcp_validation = mcp_validation
        self.validation_result = IdeaRealityValidator.validate(
            project_description,
            discovery_metrics,
            mcp_validation
        )

    def should_proceed_to_prd(self) -> bool:
        """Check if idea cleared validation for PRD phase."""
        return self.validation_result["decision"] == "BUILD"

    def should_pivot(self) -> bool:
        """Check if idea needs adjustment."""
        return self.validation_result["decision"] == "PIVOT"

    def should_kill(self) -> bool:
        """Check if idea should be rejected."""
        return self.validation_result["decision"] == "KILL"

    def to_json(self) -> Dict[str, Any]:
        """Export complete validation report as JSON."""
        return {
            "project_description": self.project_description,
            "discovery_metrics": self.discovery_metrics,
            "validation_result": self.validation_result,
            "next_step": {
                "BUILD": "Proceed to PRD phase",
                "PIVOT": "Adjust scope/positioning and revalidate",
                "KILL": "Consider alternative ideas"
            }[self.validation_result["decision"]]
        }
