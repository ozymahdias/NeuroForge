"""State Manager test fixtures - reusable state data"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from state.state_manager import StateManager
import json
import tempfile
from datetime import datetime


class StateFixtures:
    """Factory for StateManager instances with various data."""

    @staticmethod
    def empty_state(temp_file=None) -> StateManager:
        """Empty state, freshly initialized."""
        if temp_file is None:
            temp_file = str(tempfile.NamedTemporaryFile(delete=False, suffix=".json").name)
            Path(temp_file).unlink()  # Delete empty file, StateManager will create it
        manager = StateManager(temp_file)
        return manager

    @staticmethod
    def state_with_requirements(temp_file=None) -> StateManager:
        """State with sample requirements."""
        manager = StateFixtures.empty_state(temp_file)
        manager.add_requirement({
            "title": "User Authentication",
            "description": "Implement OAuth2 flow",
            "priority": "P0"
        })
        manager.add_requirement({
            "title": "Database Migration",
            "description": "Set up PostgreSQL",
            "priority": "P1"
        })
        manager.save()
        return manager

    @staticmethod
    def state_with_task_graph(temp_file=None) -> StateManager:
        """State with sample task graph."""
        manager = StateFixtures.empty_state(temp_file)

        nodes = [
            {"id": "task_1", "name": "Setup DB", "status": "PENDING"},
            {"id": "task_2", "name": "Create User Model", "status": "PENDING"},
            {"id": "task_3", "name": "Implement Auth", "status": "PENDING"}
        ]

        edges = [
            {"from": "task_1", "to": "task_2"},
            {"from": "task_2", "to": "task_3"}
        ]

        manager.update_task_graph(nodes, edges)
        manager.save()
        return manager

    @staticmethod
    def state_with_execution_history(temp_file=None) -> StateManager:
        """State with sample execution history."""
        manager = StateFixtures.state_with_task_graph(temp_file)

        manager.record_execution("task_1", "SUCCESS", "Database initialized")
        manager.record_execution("task_2", "SUCCESS", "User model created")
        manager.save()
        return manager

    @staticmethod
    def state_with_adrs(temp_file=None) -> StateManager:
        """State with Architecture Decision Records."""
        manager = StateFixtures.empty_state(temp_file)

        manager.add_adr({
            "title": "Use PostgreSQL for persistence",
            "status": "ACCEPTED",
            "context": "Need ACID compliance",
            "decision": "PostgreSQL provides ACID guarantees"
        })

        manager.add_adr({
            "title": "Use OAuth2 for authentication",
            "status": "ACCEPTED",
            "context": "Need third-party login support",
            "decision": "OAuth2 is industry standard"
        })

        manager.save()
        return manager

    @staticmethod
    def state_with_risks(temp_file=None) -> StateManager:
        """State with identified risks."""
        manager = StateFixtures.empty_state(temp_file)

        manager.add_risk({
            "description": "Tight deadline",
            "impact": "HIGH",
            "mitigation": "Increase team size"
        })

        manager.add_risk({
            "description": "Third-party API dependency",
            "impact": "MEDIUM",
            "mitigation": "Build fallback implementation"
        })

        manager.save()
        return manager

    @staticmethod
    def state_with_entropy(temp_file=None) -> StateManager:
        """State with entropy metrics."""
        manager = StateFixtures.empty_state(temp_file)

        manager.update_entropy_metrics({
            "open_questions": 5,
            "assumption_uncertainty": 0.35,
            "entropy_score": 0.40
        })

        manager.save()
        return manager

    @staticmethod
    def complete_state(temp_file=None) -> StateManager:
        """State with all components populated."""
        manager = StateFixtures.empty_state(temp_file)

        # Add requirements
        manager.add_requirement({
            "title": "Complete Feature X",
            "description": "Implement all Feature X capabilities",
            "priority": "P0"
        })

        # Add ADR
        manager.add_adr({
            "title": "Architecture Decision",
            "status": "ACCEPTED",
            "decision": "Use microservices"
        })

        # Add risk
        manager.add_risk({
            "description": "Performance risk",
            "impact": "MEDIUM",
            "mitigation": "Load testing"
        })

        # Add task graph
        nodes = [
            {"id": "t1", "name": "Task 1", "status": "DONE"},
            {"id": "t2", "name": "Task 2", "status": "DONE"}
        ]
        edges = [{"from": "t1", "to": "t2"}]
        manager.update_task_graph(nodes, edges)

        # Add execution history
        manager.record_execution("t1", "SUCCESS", "Completed")
        manager.record_execution("t2", "SUCCESS", "Completed")

        # Add entropy
        manager.update_entropy_metrics({
            "open_questions": 0,
            "assumption_uncertainty": 0.1,
            "entropy_score": 0.15
        })

        manager.save()
        return manager
