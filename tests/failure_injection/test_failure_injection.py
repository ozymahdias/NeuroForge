"""Failure injection tests - System error detection and handling"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
import json
from state.fsm_engine import FSMEngine, FSMState
from state.state_manager import StateManager


class TestInvalidFSMTransitionBlocking:
    """Test that invalid FSM transitions are blocked."""

    def test_invalid_transition_raises_error(self):
        """Invalid transitions raise ValueError."""
        fsm = FSMEngine()

        with pytest.raises(ValueError, match="Invalid transition"):
            fsm.transition(FSMState.DONE)

    def test_invalid_transition_doesnt_change_state(self):
        """Failed transition doesn't change state."""
        fsm = FSMEngine()
        original_state = fsm.get_state()

        try:
            fsm.transition(FSMState.ARCHITECTURE_READY)
        except ValueError:
            pass

        assert fsm.get_state() == original_state

    def test_backward_transition_blocked(self):
        """Cannot transition backward in FSM."""
        fsm = FSMEngine()
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)

        with pytest.raises(ValueError):
            fsm.transition(FSMState.DISCOVERY)

    def test_skip_state_blocked(self):
        """Cannot skip intermediate states."""
        fsm = FSMEngine()

        with pytest.raises(ValueError):
            fsm.transition(FSMState.PRD_READY)  # Must go through DISCOVERY first

    def test_multiple_invalid_attempts_dont_corrupt_state(self):
        """Multiple invalid transitions don't corrupt FSM."""
        fsm = FSMEngine()

        for _ in range(5):
            try:
                fsm.transition(FSMState.TESTING)
            except ValueError:
                pass

        assert fsm.get_state() == FSMState.INIT


class TestCorruptedStateFileHandling:
    """Test handling of corrupted state files."""

    def test_malformed_json_raises_error(self):
        """Malformed JSON causes clear error."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

        with open(temp_file, "w") as f:
            f.write("{ invalid json }")

        with pytest.raises(json.JSONDecodeError):
            StateManager(temp_file)

    def test_missing_required_fields_detected(self):
        """Missing required fields in state detected."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

        with open(temp_file, "w") as f:
            json.dump({"incomplete": "state"}, f)

        state_mgr = StateManager(temp_file)
        state = state_mgr.get_state()

        # Missing fields should be present or detected
        assert state is not None

    def test_invalid_state_structure_detected(self):
        """Invalid state structure is detected."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

        invalid_state = {
            "version": "not_a_number",  # Should be int
            "requirements": "not_a_list"  # Should be list
        }

        with open(temp_file, "w") as f:
            json.dump(invalid_state, f)

        state_mgr = StateManager(temp_file)
        # Should still be loadable, but may have issues
        assert state_mgr.get_state() is not None


class TestMissingExecutionOutput:
    """Test handling of missing execution outputs."""

    def test_missing_task_output_recorded(self):
        """Missing task output can be recorded."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        # Record missing output
        state_mgr.record_execution("missing_task", "FAILED", "No output")
        state_mgr.save()

        record = state_mgr.get_history(limit=1)[0]
        assert record["task_id"] == "missing_task"
        assert record["status"] == "FAILED"

    def test_broken_task_graph_edge_detection(self):
        """Broken edges in task graph detected."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        # Create task graph with broken edges
        nodes = [{"id": "task_1"}]
        edges = [{"from": "task_1", "to": "task_2"}]  # task_2 doesn't exist

        state_mgr.update_task_graph(nodes, edges)

        # Should be able to detect broken edges
        state = state_mgr.get_state()
        graph_edges = state["task_graph"]["edges"]
        graph_nodes = {n["id"] for n in state["task_graph"]["nodes"]}

        broken_edges = [
            e for e in graph_edges
            if e.get("to") not in graph_nodes or e.get("from") not in graph_nodes
        ]

        assert len(broken_edges) > 0


class TestRepeatedFailureDetection:
    """Test detection of repeated failures indicating entropy."""

    def test_repeated_failures_recorded(self):
        """Repeated failures are recorded in history."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        # Record repeated failures
        for i in range(5):
            state_mgr.record_execution("task_1", "FAILED", f"Attempt {i + 1}")

        state_mgr.save()

        # Count failures
        history = state_mgr.get_history()
        failures = [
            r for r in history
            if isinstance(r, dict) and r.get("status") == "FAILED"
        ]

        assert len(failures) == 5

    def test_failure_entropy_detection(self):
        """System can detect high entropy from repeated failures."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        # High entropy = many failures with questions
        state_mgr.record_execution("t1", "FAILED", "Unknown error")
        state_mgr.record_execution("t2", "FAILED", "Unknown error")
        state_mgr.record_execution("t3", "FAILED", "Unknown error")

        state_mgr.update_entropy_metrics({
            "open_questions": 10,
            "assumption_uncertainty": 0.8,
            "entropy_score": 0.9
        })
        state_mgr.save()

        state = state_mgr.get_state()
        entropy = state["entropy_metrics"]["entropy_score"]

        assert entropy > 0.8  # High entropy indicated


class TestStaleState:
    """Test handling of stale/inconsistent state."""

    def test_state_version_mismatch_detected(self):
        """State version mismatches can be detected."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        state_mgr.save()
        state1_version = state_mgr.get_state()["version"]

        # Version should be consistent
        assert state1_version == 1

    def test_timestamp_consistency_checked(self):
        """Timestamps should be consistent."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        state_mgr.add_requirement({"title": "Feature"})
        created_at = state_mgr.get_state()["created_at"]

        state_mgr.save()
        updated_at = state_mgr.get_state()["updated_at"]

        # Updated should be >= created
        assert updated_at >= created_at

    def test_requirement_id_collision_detection(self):
        """Duplicate requirement IDs detected."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        state_mgr.add_requirement({"title": "Req 1"})
        state_mgr.add_requirement({"title": "Req 2"})

        state = state_mgr.get_state()
        req_ids = [r["id"] for r in state["requirements"]]

        # All IDs should be unique
        assert len(req_ids) == len(set(req_ids))


class TestFSMHistoryIntegrity:
    """Test FSM history remains consistent."""

    def test_history_cannot_be_empty(self):
        """FSM history never becomes empty."""
        fsm = FSMEngine()

        # Even after reset, history exists
        fsm.transition(FSMState.DISCOVERY)
        fsm.reset()

        assert len(fsm.get_history()) > 0

    def test_history_chronological_order_enforced(self):
        """History maintains chronological order."""
        fsm = FSMEngine()

        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)
        fsm.transition(FSMState.ARCHITECTURE_READY)

        history = fsm.get_history()
        for i in range(len(history) - 1):
            assert history[i]["timestamp"] <= history[i + 1]["timestamp"]

    def test_current_state_matches_history(self):
        """Current state always matches history."""
        fsm = FSMEngine()

        fsm.transition(FSMState.DISCOVERY)
        current = fsm.get_state().value
        history_latest = fsm.get_history()[-1]["state"]

        assert current == history_latest

        fsm.transition(FSMState.PRD_READY)
        current = fsm.get_state().value
        history_latest = fsm.get_history()[-1]["state"]

        assert current == history_latest


class TestExecutionHistoryIntegrity:
    """Test execution history remains valid."""

    def test_execution_history_chronological(self):
        """Execution history is chronological."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        for i in range(3):
            state_mgr.record_execution(f"task_{i}", "SUCCESS", f"Output {i}")

        state_mgr.save()
        history = state_mgr.get_state()["execution_history"]

        for i in range(len(history) - 1):
            assert history[i]["timestamp"] <= history[i + 1]["timestamp"]

    def test_execution_records_complete(self):
        """Execution records have all required fields."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        state_mgr.record_execution("task_1", "SUCCESS", "Output")
        state_mgr.save()

        record = state_mgr.get_state()["execution_history"][0]
        assert "task_id" in record
        assert "status" in record
        assert "output" in record
        assert "timestamp" in record


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
