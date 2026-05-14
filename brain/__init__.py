# Brain module - reasoning only, no execution
from .discovery_engine import (
    OpenQuestion,
    Assumption,
    QuestionSeverity,
    EntropyCalculator,
    OpenQuestionGenerator,
    AssumptionBuilder,
    DiscoveryOutput
)
from .idea_reality_mcp import (
    IdeaRealityValidator,
    MockIdeaRealityValidator,
    DiscoveryMCPAdapter
)
from .validation_engine import (
    IdeaRealityValidator as IdeaRealityValidationEngine,
    ValidationDecision,
    ValidationScores,
    ValidationReport
)

__all__ = [
    "OpenQuestion",
    "Assumption",
    "QuestionSeverity",
    "EntropyCalculator",
    "OpenQuestionGenerator",
    "AssumptionBuilder",
    "DiscoveryOutput",
    "IdeaRealityValidator",
    "MockIdeaRealityValidator",
    "DiscoveryMCPAdapter",
    "IdeaRealityValidationEngine",
    "ValidationDecision",
    "ValidationScores",
    "ValidationReport",
]
