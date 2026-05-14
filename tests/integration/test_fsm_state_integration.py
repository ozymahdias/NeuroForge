"""Integration tests - FSM and StateManager synchronization"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
from state.fsm_engine import FSMEngine, FSMState
from state.state_manager import StateManager
from tests.helpers.assert_helpers import AssertHelpers


class TestFSMStateSync:
    """Test FSM and StateManager work together."""

    def test_fsm_transitions_recorded_in_history(self):
        """FSM transitions should be recorded in state history."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Transition FSM
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)

        # Record in state
        state_mgr.state["execution_history"].append({
            "fsm_state": fsm.get_state_value(),
            "timestamp": fsm.get_history()[-1]["timestamp"],
            "action": "FSM_TRANSITION"
        })

        state_mgr.save()

        # Verify state contains FSM info
        assert state_mgr.get_state()["execution_history"][-1]["fsm_state"] == "PRD_READY"

    def test_state_persisted_during_fsm_lifecycle(self):
        """State can be persisted at each FSM state."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Record initial state
        state_mgr.add_requirement({"title": "Initial Requirement"})
        state_mgr.save()

        fsm.transition(FSMState.DISCOVERY)
        state_mgr.add_requirement({"title": "Discovery Requirement"})
        state_mgr.save()

        fsm.transition(FSMState.PRD_READY)
        state_mgr.add_requirement({"title": "PRD Requirement"})
        state_mgr.save()

        # Reload and verify
        state_mgr2 = StateManager(temp_file)
        state = state_mgr2.get_state()
        assert len(state["requirements"]) == 3

    def test_fsm_state_consistency(self):
        """FSM state remains consistent across transitions."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        path = [
            FSMState.DISCOVERY,
            FSMState.PRD_READY,
            FSMState.ARCHITECTURE_READY
        ]

        for target_state in path:
            fsm.transition(target_state)
            AssertHelpers.assert_fsm_valid(fsm)
            AssertHelpers.assert_state_valid(state_mgr)

    def test_state_recovery_from_checkpoint(self):
        """System can recover state from checkpoint."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

        # Create state at checkpoint
        fsm1 = FSMEngine()
        state_mgr1 = StateManager(temp_file)

        fsm1.transition(FSMState.DISCOVERY)
        fsm1.transition(FSMState.PRD_READY)

        state_mgr1.add_requirement({"title": "Feature"})
        state_mgr1.add_adr({"title": "ADR 1"})
        state_mgr1.save()

        # Recover from checkpoint
        fsm2 = FSMEngine.from_dict(fsm1.to_dict())
        state_mgr2 = StateManager(temp_file)

        assert fsm2.get_state() == FSMState.PRD_READY
        assert len(state_mgr2.get_state()["requirements"]) == 1
        assert len(state_mgr2.get_state()["adrs"]) == 1


class TestFSMStateIntegration:
    """Test FSM and StateManager integrated behavior."""

    def test_full_lifecycle_with_state_updates(self):
        """Full lifecycle with state updates at each phase."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # INIT phase
        state_mgr.update_entropy_metrics({"entropy_score": 0.8})
        state_mgr.save()

        # DISCOVERY phase
        fsm.transition(FSMState.DISCOVERY)
        state_mgr.add_requirement({"title": "Feature 1"})
        state_mgr.update_entropy_metrics({"entropy_score": 0.6})
        state_mgr.save()

        # PRD_READY phase
        fsm.transition(FSMState.PRD_READY)
        state_mgr.add_adr({"title": "ADR 1"})
        state_mgr.update_entropy_metrics({"entropy_score": 0.4})
        state_mgr.save()

        # ARCHITECTURE_READY phase
        fsm.transition(FSMState.ARCHITECTURE_READY)
        state_mgr.add_adr({"title": "ADR 2"})
        state_mgr.update_entropy_metrics({"entropy_score": 0.3})
        state_mgr.save()

        # TASKS_READY phase
        fsm.transition(FSMState.TASKS_READY)
        nodes = [{"id": "t1", "name": "Task 1"}]
        edges = []
        state_mgr.update_task_graph(nodes, edges)
        state_mgr.save()

        # IMPLEMENTING phase
        fsm.transition(FSMState.IMPLEMENTING)
        state_mgr.record_execution("t1", "SUCCESS", "Completed")
        state_mgr.save()

        # TESTING phase
        fsm.transition(FSMState.TESTING)
        state_mgr.update_entropy_metrics({"entropy_score": 0.1})
        state_mgr.save()

        # DONE phase
        fsm.transition(FSMState.DONE)
        state_mgr.save()

        # Verify final state
        assert fsm.get_state() == FSMState.DONE
        final_state = state_mgr.get_state()
        assert len(final_state["requirements"]) == 1
        assert len(final_state["adrs"]) == 2
        assert final_state["entropy_metrics"]["entropy_score"] == 0.1
        AssertHelpers.assert_state_valid(state_mgr)
        AssertHelpers.assert_fsm_valid(fsm)

    def test_fsm_history_matches_state_history(self):
        """FSM history should align with state history."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        fsm.transition(FSMState.DISCOVERY, "discovery started")
        fsm.transition(FSMState.PRD_READY, "prd generated")

        # FSM history
        fsm_history = fsm.get_history()
        assert len(fsm_history) == 3
        assert fsm_history[1]["state"] == "DISCOVERY"
        assert fsm_history[2]["state"] == "PRD_READY"

        # Verify order is chronological
        for i in range(len(fsm_history) - 1):
            assert fsm_history[i]["timestamp"] <= fsm_history[i + 1]["timestamp"]


class TestConcurrentStateUpdates:
    """Test state updates during FSM transitions."""

    def test_state_update_during_transition(self):
        """State can be updated during FSM transition."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Transition and update atomically
        fsm.transition(FSMState.DISCOVERY)
        state_mgr.add_requirement({"title": "Discovery Phase Requirement"})
        state_mgr.save()

        # Verify both updated
        assert fsm.get_state() == FSMState.DISCOVERY
        assert len(state_mgr.get_state()["requirements"]) == 1

    def test_multiple_state_updates_in_phase(self):
        """Multiple state updates can occur in single FSM state."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        fsm.transition(FSMState.IMPLEMENTING)

        # Multiple updates
        state_mgr.record_execution("t1", "SUCCESS", "Step 1")
        state_mgr.record_execution("t2", "SUCCESS", "Step 2")
        state_mgr.record_execution("t3", "SUCCESS", "Step 3")
        state_mgr.save()

        # Verify all recorded
        state = state_mgr.get_state()
        exec_records = [r for r in state["execution_history"] if "task_id" in r]
        assert len(exec_records) == 3


class TestStateRecoveryAfterFSMError:
    """Test state consistency after FSM errors."""

    def test_state_unchanged_after_invalid_transition(self):
        """State is not modified if FSM transition fails."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Add requirement
        state_mgr.add_requirement({"title": "Feature"})
        state_mgr.save()

        # Try invalid transition
        with pytest.raises(ValueError):
            fsm.transition(FSMState.DONE)  # Invalid from INIT

        # State should be unchanged
        assert len(state_mgr.get_state()["requirements"]) == 1
        assert fsm.get_state() == FSMState.INIT


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
