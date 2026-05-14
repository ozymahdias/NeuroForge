"""Idea-Reality MCP Adapter - Hook for external validation"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class IdeaRealityValidator(ABC):
    """Abstract interface for idea-reality validation via MCP."""

    @abstractmethod
    def validate_feasibility(self, project_description: str) -> Dict[str, Any]:
        """
        Validate feasibility of project idea.
        Returns: feasibility_score (0.0-1.0), blockers, risks
        """
        pass

    @abstractmethod
    def check_market_saturation(self, project_description: str) -> Dict[str, Any]:
        """
        Check market saturation for similar ideas.
        Returns: saturation_score (0.0-1.0), similar_projects, gaps
        """
        pass

    @abstractmethod
    def calculate_innovation_delta(self, project_description: str) -> Dict[str, Any]:
        """
        Calculate innovation score vs existing solutions.
        Returns: innovation_score (0.0-1.0), novelty_factors
        """
        pass


class MockIdeaRealityValidator(IdeaRealityValidator):
    """Mock validator for testing without MCP."""

    def validate_feasibility(self, project_description: str) -> Dict[str, Any]:
        """Mock feasibility validation."""
        return {
            "feasibility_score": 0.75,
            "blockers": [],
            "risks": ["Unknown integrations", "Timeline uncertainty"],
            "confidence": "medium"
        }

    def check_market_saturation(self, project_description: str) -> Dict[str, Any]:
        """Mock market saturation check."""
        return {
            "saturation_score": 0.4,
            "similar_projects": 3,
            "market_gap_identified": True,
            "gaps": ["Better UX", "Lower cost", "Faster onboarding"]
        }

    def calculate_innovation_delta(self, project_description: str) -> Dict[str, Any]:
        """Mock innovation calculation."""
        return {
            "innovation_score": 0.65,
            "novelty_factors": [
                "Different architecture approach",
                "Novel use case combination",
                "Improved performance angle"
            ]
        }


class DiscoveryMCPAdapter:
    """Adapter that integrates MCP validator into discovery flow."""

    def __init__(self, validator: Optional[IdeaRealityValidator] = None):
        self.validator = validator or MockIdeaRealityValidator()

    def run_discovery_validation(
        self,
        project_description: str
    ) -> Dict[str, Any]:
        """
        Run full discovery validation against idea-reality metrics.
        Returns structured validation results.
        """
        feasibility = self.validator.validate_feasibility(project_description)
        saturation = self.validator.check_market_saturation(project_description)
        innovation = self.validator.calculate_innovation_delta(project_description)

        return {
            "feasibility": feasibility,
            "market_saturation": saturation,
            "innovation": innovation,
            "validation_timestamp": __import__("datetime").datetime.now().isoformat()
        }

    def get_decision_factors(
        self,
        discovery_validation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract decision factors for BUILD/PIVOT/KILL determination.
        This feeds into PROMPT 5.
        """
        return {
            "feasibility_score": discovery_validation["feasibility"]["feasibility_score"],
            "market_saturation_score": discovery_validation["market_saturation"]["saturation_score"],
            "innovation_score": discovery_validation["innovation"]["innovation_score"],
            "market_gap_exists": discovery_validation["market_saturation"]["market_gap_identified"],
            "feasibility_risks": discovery_validation["feasibility"]["risks"],
            "novelty_factors": discovery_validation["innovation"]["novelty_factors"],
        }
