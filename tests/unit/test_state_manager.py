"""Unit tests - State Manager correctness"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
import json
from state.state_manager import StateManager
from tests.fixtures.state_fixtures import StateFixtures
from tests.helpers.assert_helpers import AssertHelpers


class TestStateInitialization:
    """Test StateManager initialization."""

    def test_empty_state_initialization(self):
        """StateManager initializes with empty state."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        Path(temp_file).unlink()  # Delete empty file
        manager = StateManager(temp_file)
        state = manager.get_state()

        assert state["version"] == 1
        assert state["requirements"] == []
        assert state["adrs"] == []
        assert state["risks"] == []
        assert state["task_graph"]["nodes"] == []
        assert state["task_graph"]["edges"] == []
        assert state["execution_history"] == []

    def test_state_file_created(self):
        """State file is created on initialization."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        Path(temp_file).unlink()  # Delete the file

        manager = StateManager(temp_file)
        manager.save()

        assert Path(temp_file).exists()


class TestRequirements:
    """Test requirement management."""

    def test_add_requirement(self):
        """Can add requirement."""
        manager = StateFixtures.empty_state()
        manager.add_requirement({
            "title": "Feature X",
            "description": "Implement Feature X",
            "priority": "P0"
        })

        state = manager.get_state()
        assert len(state["requirements"]) == 1
        assert state["requirements"][0]["title"] == "Feature X"

    def test_requirement_gets_id(self):
        """Requirements are assigned IDs."""
        manager = StateFixtures.empty_state()
        manager.add_requirement({"title": "Req 1"})
        manager.add_requirement({"title": "Req 2"})

        state = manager.get_state()
        assert state["requirements"][0]["id"] == 0
        assert state["requirements"][1]["id"] == 1

    def test_requirement_gets_timestamp(self):
        """Requirements are timestamped."""
        manager = StateFixtures.empty_state()
        manager.add_requirement({"title": "Req 1"})

        state = manager.get_state()
        assert "added_at" in state["requirements"][0]

    def test_requirements_append_only(self):
        """Requirements list is append-only."""
        manager = StateFixtures.state_with_requirements()
        state1 = manager.get_state()
        count1 = len(state1["requirements"])

        manager.add_requirement({"title": "New Req"})
        state2 = manager.get_state()
        count2 = len(state2["requirements"])

        assert count2 == count1 + 1


class TestADRs:
    """Test Architecture Decision Record management."""

    def test_add_adr(self):
        """Can add ADR."""
        manager = StateFixtures.empty_state()
        manager.add_adr({
            "title": "Use PostgreSQL",
            "status": "ACCEPTED",
            "decision": "PostgreSQL has ACID guarantees"
        })

        state = manager.get_state()
        assert len(state["adrs"]) == 1
        assert state["adrs"][0]["title"] == "Use PostgreSQL"

    def test_adr_gets_id(self):
        """ADRs are assigned IDs."""
        manager = StateFixtures.empty_state()
        manager.add_adr({"title": "ADR 1"})
        manager.add_adr({"title": "ADR 2"})

        state = manager.get_state()
        assert state["adrs"][0]["id"] == 0
        assert state["adrs"][1]["id"] == 1

    def test_adrs_append_only(self):
        """ADRs list is append-only."""
        manager = StateFixtures.state_with_adrs()
        count1 = len(manager.get_state()["adrs"])

        manager.add_adr({"title": "New ADR"})
        count2 = len(manager.get_state()["adrs"])

        assert count2 == count1 + 1


class TestRisks:
    """Test risk management."""

    def test_add_risk(self):
        """Can add risk."""
        manager = StateFixtures.empty_state()
        manager.add_risk({
            "description": "Tight deadline",
            "impact": "HIGH",
            "mitigation": "Increase team"
        })

        state = manager.get_state()
        assert len(state["risks"]) == 1
        assert state["risks"][0]["description"] == "Tight deadline"

    def test_risk_gets_id(self):
        """Risks are assigned IDs."""
        manager = StateFixtures.empty_state()
        manager.add_risk({"description": "Risk 1"})
        manager.add_risk({"description": "Risk 2"})

        state = manager.get_state()
        assert state["risks"][0]["id"] == 0
        assert state["risks"][1]["id"] == 1

    def test_risks_append_only(self):
        """Risks list is append-only."""
        manager = StateFixtures.state_with_risks()
        count1 = len(manager.get_state()["risks"])

        manager.add_risk({"description": "New Risk"})
        count2 = len(manager.get_state()["risks"])

        assert count2 == count1 + 1


class TestTaskGraph:
    """Test task graph management."""

    def test_update_task_graph(self):
        """Can update task graph."""
        manager = StateFixtures.empty_state()

        nodes = [
            {"id": "task_1", "name": "Setup"},
            {"id": "task_2", "name": "Implement"}
        ]
        edges = [{"from": "task_1", "to": "task_2"}]

        manager.update_task_graph(nodes, edges)

        state = manager.get_state()
        assert len(state["task_graph"]["nodes"]) == 2
        assert len(state["task_graph"]["edges"]) == 1

    def test_task_graph_versioned(self):
        """Task graph updates are tracked."""
        manager = StateFixtures.empty_state()

        nodes1 = [{"id": "t1"}]
        manager.update_task_graph(nodes1, [])

        first_update = manager.get_state()["task_graph"]["updated_at"]

        # Update again
        nodes2 = [{"id": "t1"}, {"id": "t2"}]
        manager.update_task_graph(nodes2, [])

        second_update = manager.get_state()["task_graph"]["updated_at"]
        assert first_update <= second_update


class TestExecutionHistory:
    """Test execution history tracking."""

    def test_record_execution(self):
        """Can record execution."""
        manager = StateFixtures.empty_state()
        manager.record_execution("task_1", "SUCCESS", "Task completed")

        state = manager.get_state()
        assert len(state["execution_history"]) == 1
        assert state["execution_history"][0]["task_id"] == "task_1"
        assert state["execution_history"][0]["status"] == "SUCCESS"

    def test_execution_history_append_only(self):
        """Execution history is append-only."""
        manager = StateFixtures.empty_state()

        manager.record_execution("t1", "SUCCESS", "Output 1")
        count1 = len(manager.get_state()["execution_history"])

        manager.record_execution("t2", "SUCCESS", "Output 2")
        count2 = len(manager.get_state()["execution_history"])

        assert count2 == count1 + 1

    def test_execution_record_includes_timestamp(self):
        """Execution records include timestamp."""
        manager = StateFixtures.empty_state()
        manager.record_execution("t1", "SUCCESS", "Output")

        record = manager.get_state()["execution_history"][0]
        assert "timestamp" in record


class TestEntropyMetrics:
    """Test entropy metrics management."""

    def test_update_entropy_metrics(self):
        """Can update entropy metrics."""
        manager = StateFixtures.empty_state()
        manager.update_entropy_metrics({
            "open_questions": 5,
            "assumption_uncertainty": 0.4,
            "entropy_score": 0.35
        })

        state = manager.get_state()
        metrics = state["entropy_metrics"]
        assert metrics["open_questions"] == 5
        assert metrics["assumption_uncertainty"] == 0.4
        assert metrics["entropy_score"] == 0.35

    def test_entropy_metrics_tracked(self):
        """Entropy metric updates are tracked."""
        manager = StateFixtures.empty_state()
        manager.update_entropy_metrics({"entropy_score": 0.5})
        first_update = manager.get_state()["entropy_metrics"]["updated_at"]

        manager.update_entropy_metrics({"entropy_score": 0.3})
        second_update = manager.get_state()["entropy_metrics"]["updated_at"]

        assert first_update <= second_update


class TestPersistence:
    """Test state persistence."""

    def test_save_creates_file(self):
        """Save creates state file."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        Path(temp_file).unlink()

        manager = StateManager(temp_file)
        manager.add_requirement({"title": "Test"})
        manager.save()

        assert Path(temp_file).exists()

    def test_save_contains_data(self):
        """Saved file contains state data."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        manager = StateManager(temp_file)
        manager.add_requirement({"title": "Feature X", "priority": "P0"})
        manager.save()

        # Read file
        with open(temp_file) as f:
            data = json.load(f)

        assert len(data["requirements"]) == 1
        assert data["requirements"][0]["title"] == "Feature X"

    def test_load_state_from_file(self):
        """Can load state from saved file."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        manager1 = StateManager(temp_file)
        manager1.add_requirement({"title": "Feature X"})
        manager1.save()

        # Load in new manager
        manager2 = StateManager(temp_file)
        state = manager2.get_state()

        assert len(state["requirements"]) == 1
        assert state["requirements"][0]["title"] == "Feature X"


class TestStateValidity:
    """Test state validity checks."""

    def test_state_is_valid(self):
        """Valid state passes validation."""
        manager = StateFixtures.complete_state()
        AssertHelpers.assert_state_valid(manager)

    def test_state_consistency(self):
        """State data is consistent."""
        manager = StateFixtures.complete_state()
        AssertHelpers.assert_state_consistency(manager)

    def test_empty_state_is_valid(self):
        """Empty state is valid."""
        manager = StateFixtures.empty_state()
        AssertHelpers.assert_state_valid(manager)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
