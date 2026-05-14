"""Helper assertions for state and FSM validation"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from state.fsm_engine import FSMEngine, FSMState
from state.state_manager import StateManager
from typing import Dict, List, Any


class AssertHelpers:
    """Custom assertions for NeuroForge testing."""

    @staticmethod
    def assert_fsm_valid(fsm: FSMEngine) -> None:
        """Assert FSM is in valid state."""
        history = fsm.get_history()
        assert len(history) > 0, "FSM history is empty"

        # Check chronological order
        for i in range(len(history) - 1):
            assert history[i]["timestamp"] <= history[i + 1]["timestamp"], \
                f"History not chronologically ordered at index {i}"

        # Current state must match last history entry
        current = fsm.get_state()
        last_entry = history[-1]
        assert current.value == last_entry["state"], \
            f"Current state {current.value} doesn't match history {last_entry['state']}"

    @staticmethod
    def assert_valid_transition(fsm: FSMEngine, target: FSMState) -> None:
        """Assert transition to target is valid."""
        assert fsm.can_transition_to(target), \
            f"Invalid transition from {fsm.get_state().value} to {target.value}"

    @staticmethod
    def assert_invalid_transition(fsm: FSMEngine, target: FSMState) -> None:
        """Assert transition to target is invalid."""
        assert not fsm.can_transition_to(target), \
            f"Transition from {fsm.get_state().value} to {target.value} should be invalid"

    @staticmethod
    def assert_state_valid(state_mgr: StateManager) -> None:
        """Assert StateManager is in valid state."""
        state = state_mgr.get_state()

        # Check append-only properties
        assert isinstance(state["requirements"], list), "Requirements must be list"
        assert isinstance(state["adrs"], list), "ADRs must be list"
        assert isinstance(state["risks"], list), "Risks must be list"
        assert isinstance(state["execution_history"], list), "History must be list"

        # Check version and timestamps
        assert state.get("version") > 0, "State version must be positive"
        assert state.get("created_at"), "State must have created_at"
        assert state.get("updated_at"), "State must have updated_at"

        # Check task graph structure
        graph = state.get("task_graph", {})
        assert isinstance(graph.get("nodes", []), list), "Task graph nodes must be list"
        assert isinstance(graph.get("edges", []), list), "Task graph edges must be list"

    @staticmethod
    def assert_state_consistency(state_mgr: StateManager) -> None:
        """Assert state data consistency."""
        state = state_mgr.get_state()

        # Requirements must have unique IDs
        req_ids = [r.get("id") for r in state["requirements"]]
        assert len(req_ids) == len(set(req_ids)), "Duplicate requirement IDs"

        # ADRs must have unique IDs
        adr_ids = [a.get("id") for a in state["adrs"]]
        assert len(adr_ids) == len(set(adr_ids)), "Duplicate ADR IDs"

        # Risks must have unique IDs
        risk_ids = [r.get("id") for r in state["risks"]]
        assert len(risk_ids) == len(set(risk_ids)), "Duplicate risk IDs"

        # Graph edges must reference valid nodes
        nodes = {n.get("id") for n in state["task_graph"]["nodes"]}
        for edge in state["task_graph"]["edges"]:
            assert edge.get("from") in nodes, f"Edge references unknown node: {edge.get('from')}"
            assert edge.get("to") in nodes, f"Edge references unknown node: {edge.get('to')}"

    @staticmethod
    def assert_history_valid(history: List[Dict[str, Any]]) -> None:
        """Assert execution history is valid."""
        assert len(history) > 0, "History cannot be empty"

        # Check chronological order
        for i in range(len(history) - 1):
            ts1 = history[i].get("timestamp")
            ts2 = history[i + 1].get("timestamp")
            assert ts1 <= ts2, f"History not chronologically ordered at index {i}"

    @staticmethod
    def assert_fsm_path_valid(fsm_history: List[Dict[str, str]]) -> None:
        """Assert FSM followed valid state transition path."""
        assert len(fsm_history) > 0, "FSM history is empty"

        for i in range(len(fsm_history) - 1):
            current_state = FSMState(fsm_history[i]["state"])
            next_state = FSMState(fsm_history[i + 1]["state"])

            valid_transitions = FSMEngine.VALID_TRANSITIONS
            assert next_state in valid_transitions.get(current_state, []), \
                f"Invalid path: {current_state.value} → {next_state.value}"

    @staticmethod
    def assert_artifact_exists(path: Path) -> None:
        """Assert artifact file exists."""
        assert path.exists(), f"Artifact not found: {path}"

    @staticmethod
    def assert_artifacts_complete(artifacts: Dict[str, Path]) -> None:
        """Assert all expected artifacts exist."""
        missing = [name for name, path in artifacts.items() if not path.exists()]
        assert not missing, f"Missing artifacts: {missing}"

    @staticmethod
    def assert_entropy_valid(entropy: Dict[str, float]) -> None:
        """Assert entropy metrics are valid."""
        assert 0 <= entropy.get("entropy_score", 0) <= 1, "Entropy score must be 0-1"
        assert 0 <= entropy.get("assumption_uncertainty", 0) <= 1, "Uncertainty must be 0-1"
        assert entropy.get("open_questions", 0) >= 0, "Open questions must be non-negative"
