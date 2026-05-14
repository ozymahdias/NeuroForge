"""Discovery Engine - Entropy system and idea validation"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
from datetime import datetime


class QuestionSeverity(Enum):
    """Severity levels for open questions."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class OpenQuestion:
    """Represents an open question in the discovery phase."""
    id: str
    question: str
    severity: str
    domain: str
    discovered_at: str
    requires_validation: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class Assumption:
    """Represents an assumption made during discovery."""
    id: str
    assumption: str
    confidence: float  # 0.0 to 1.0
    dependencies: List[str]  # question IDs this depends on
    recorded_at: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class EntropyCalculator:
    """Calculates entropy metrics for project uncertainty."""

    @staticmethod
    def calculate_entropy(
        open_questions: List[OpenQuestion],
        assumptions: List[Assumption],
    ) -> Dict[str, float]:
        """
        Calculate entropy score based on questions and assumptions.
        Returns dict with individual metrics and overall entropy.
        """
        question_entropy = EntropyCalculator._question_entropy(open_questions)
        assumption_uncertainty = EntropyCalculator._assumption_uncertainty(assumptions)
        critical_blockers = sum(
            1 for q in open_questions if q.severity == QuestionSeverity.CRITICAL.value
        )

        total_entropy = (
            (question_entropy * 0.4) +
            (assumption_uncertainty * 0.4) +
            (min(critical_blockers / max(1, len(open_questions)), 1.0) * 0.2)
        )

        return {
            "question_entropy": round(question_entropy, 3),
            "assumption_uncertainty": round(assumption_uncertainty, 3),
            "critical_blockers": critical_blockers,
            "total_entropy": round(total_entropy, 3)
        }

    @staticmethod
    def _question_entropy(questions: List[OpenQuestion]) -> float:
        """Entropy from unresolved questions (0.0 = none, 1.0 = max)."""
        if not questions:
            return 0.0

        severity_weights = {
            QuestionSeverity.CRITICAL.value: 1.0,
            QuestionSeverity.HIGH.value: 0.7,
            QuestionSeverity.MEDIUM.value: 0.4,
            QuestionSeverity.LOW.value: 0.1,
        }

        total_weight = sum(
            severity_weights.get(q.severity, 0.5) for q in questions
        )
        max_possible = len(questions) * 1.0
        return min(total_weight / max(max_possible, 1.0), 1.0)

    @staticmethod
    def _assumption_uncertainty(assumptions: List[Assumption]) -> float:
        """Uncertainty from low-confidence assumptions."""
        if not assumptions:
            return 0.0

        avg_confidence = sum(a.confidence for a in assumptions) / len(assumptions)
        return round(1.0 - avg_confidence, 3)


class OpenQuestionGenerator:
    """Generates structured open questions from project description."""

    @staticmethod
    def generate_from_description(description: str) -> List[OpenQuestion]:
        """
        Generate open questions from project description.
        This is a basic template; in production would use LLM.
        """
        questions = []

        # Template patterns
        patterns = [
            {
                "trigger": ["user", "audience", "customer"],
                "question": "Who exactly is the primary user/audience?",
                "severity": QuestionSeverity.CRITICAL,
                "domain": "requirements"
            },
            {
                "trigger": ["scale", "performance", "load"],
                "question": "What are the performance and scale requirements?",
                "severity": QuestionSeverity.HIGH,
                "domain": "requirements"
            },
            {
                "trigger": ["integration", "api", "external"],
                "question": "What external integrations are required?",
                "severity": QuestionSeverity.MEDIUM,
                "domain": "architecture"
            },
            {
                "trigger": ["security", "compliance", "auth"],
                "question": "What security and compliance requirements apply?",
                "severity": QuestionSeverity.HIGH,
                "domain": "security"
            },
            {
                "trigger": ["timeline", "deadline", "schedule"],
                "question": "What is the project timeline and deadline?",
                "severity": QuestionSeverity.MEDIUM,
                "domain": "planning"
            },
        ]

        desc_lower = description.lower()
        seen = set()

        for pattern in patterns:
            if any(trigger in desc_lower for trigger in pattern["trigger"]):
                q_id = f"q_{len(questions)}"
                if q_id not in seen:
                    questions.append(OpenQuestion(
                        id=q_id,
                        question=pattern["question"],
                        severity=pattern["severity"].value,
                        domain=pattern["domain"],
                        discovered_at=datetime.now().isoformat()
                    ))
                    seen.add(q_id)

        return questions

    @staticmethod
    def add_custom_question(
        questions: List[OpenQuestion],
        question: str,
        severity: QuestionSeverity,
        domain: str
    ) -> List[OpenQuestion]:
        """Add a custom open question."""
        q_id = f"q_{len(questions)}"
        questions.append(OpenQuestion(
            id=q_id,
            question=question,
            severity=severity.value,
            domain=domain,
            discovered_at=datetime.now().isoformat()
        ))
        return questions


class AssumptionBuilder:
    """Builds and tracks assumptions."""

    @staticmethod
    def create_assumption(
        assumption: str,
        confidence: float,
        dependencies: Optional[List[str]] = None,
    ) -> Assumption:
        """Create a single assumption."""
        if not (0.0 <= confidence <= 1.0):
            raise ValueError("Confidence must be between 0.0 and 1.0")

        return Assumption(
            id=f"a_{datetime.now().timestamp()}",
            assumption=assumption,
            confidence=confidence,
            dependencies=dependencies or [],
            recorded_at=datetime.now().isoformat()
        )

    @staticmethod
    def validate_assumption(
        assumption: Assumption,
        open_questions: List[OpenQuestion]
    ) -> bool:
        """Check if all dependencies are resolved."""
        question_ids = {q.id for q in open_questions}
        unresolved = [dep for dep in assumption.dependencies if dep in question_ids]
        return len(unresolved) == 0


class DiscoveryOutput:
    """Structured discovery phase output."""

    def __init__(self):
        self.open_questions: List[OpenQuestion] = []
        self.assumptions: List[Assumption] = []
        self.entropy_metrics: Dict[str, float] = {}

    def add_question(self, question: OpenQuestion) -> None:
        self.open_questions.append(question)
        self._recalculate_entropy()

    def add_assumption(self, assumption: Assumption) -> None:
        self.assumptions.append(assumption)
        self._recalculate_entropy()

    def _recalculate_entropy(self) -> None:
        """Recalculate entropy metrics."""
        self.entropy_metrics = EntropyCalculator.calculate_entropy(
            self.open_questions,
            self.assumptions
        )

    def to_json(self) -> Dict[str, Any]:
        """Export as structured JSON."""
        return {
            "open_questions": [q.to_dict() for q in self.open_questions],
            "assumptions": [a.to_dict() for a in self.assumptions],
            "entropy_metrics": self.entropy_metrics,
            "ready_for_prd": self.entropy_metrics.get("total_entropy", 1.0) < 0.3
        }
