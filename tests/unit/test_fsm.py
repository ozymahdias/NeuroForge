"""Unit tests - FSM Engine correctness"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
from state.fsm_engine import FSMEngine, FSMState
from tests.fixtures.fsm_fixtures import FSMFixtures
from tests.helpers.assert_helpers import AssertHelpers


class TestFSMBasics:
    """Test FSM fundamental operations."""

    def test_init_state(self):
        """FSM starts in INIT state."""
        fsm = FSMEngine()
        assert fsm.get_state() == FSMState.INIT
        assert fsm.get_state_value() == "INIT"

    def test_state_history_initialization(self):
        """FSM initializes with one history entry."""
        fsm = FSMEngine()
        history = fsm.get_history()
        assert len(history) == 1
        assert history[0]["state"] == "INIT"
        assert history[0]["reason"] == "initialization"


class TestValidTransitions:
    """Test all valid FSM transitions."""

    def test_init_to_discovery(self):
        """INIT → DISCOVERY is valid."""
        fsm = FSMEngine()
        assert fsm.can_transition_to(FSMState.DISCOVERY)
        fsm.transition(FSMState.DISCOVERY)
        assert fsm.get_state() == FSMState.DISCOVERY

    def test_discovery_to_prd_ready(self):
        """DISCOVERY → PRD_READY is valid."""
        fsm = FSMFixtures.discovery_state()
        assert fsm.can_transition_to(FSMState.PRD_READY)
        fsm.transition(FSMState.PRD_READY)
        assert fsm.get_state() == FSMState.PRD_READY

    def test_full_forward_path(self):
        """Full INIT → DONE path is valid."""
        fsm = FSMEngine()
        path = [
            FSMState.DISCOVERY,
            FSMState.PRD_READY,
            FSMState.ARCHITECTURE_READY,
            FSMState.TASKS_READY,
            FSMState.IMPLEMENTING,
            FSMState.TESTING,
            FSMState.DONE
        ]

        for state in path:
            assert fsm.can_transition_to(state), f"Cannot transition to {state.value}"
            fsm.transition(state)
            assert fsm.get_state() == state

    def test_implementing_loop(self):
        """IMPLEMENTING can transition to itself."""
        fsm = FSMFixtures.implementing_state()
        assert fsm.can_transition_to(FSMState.IMPLEMENTING)
        fsm.transition(FSMState.IMPLEMENTING, "retry")
        assert fsm.get_state() == FSMState.IMPLEMENTING

    def test_testing_to_implementing(self):
        """TESTING → IMPLEMENTING is valid."""
        fsm = FSMFixtures.testing_state()
        assert fsm.can_transition_to(FSMState.IMPLEMENTING)
        fsm.transition(FSMState.IMPLEMENTING, "bug found")
        assert fsm.get_state() == FSMState.IMPLEMENTING

    def test_testing_to_done(self):
        """TESTING → DONE is valid."""
        fsm = FSMFixtures.testing_state()
        assert fsm.can_transition_to(FSMState.DONE)
        fsm.transition(FSMState.DONE)
        assert fsm.get_state() == FSMState.DONE


class TestInvalidTransitions:
    """Test invalid transitions are rejected."""

    def test_init_cannot_skip_to_prd(self):
        """INIT → PRD_READY is invalid."""
        fsm = FSMEngine()
        assert not fsm.can_transition_to(FSMState.PRD_READY)
        with pytest.raises(ValueError, match="Invalid transition"):
            fsm.transition(FSMState.PRD_READY)

    def test_init_cannot_jump_to_done(self):
        """INIT → DONE is invalid."""
        fsm = FSMEngine()
        assert not fsm.can_transition_to(FSMState.DONE)
        with pytest.raises(ValueError):
            fsm.transition(FSMState.DONE)

    def test_discovery_cannot_go_back_to_init(self):
        """DISCOVERY → INIT is invalid."""
        fsm = FSMFixtures.discovery_state()
        assert not fsm.can_transition_to(FSMState.INIT)
        with pytest.raises(ValueError):
            fsm.transition(FSMState.INIT)

    def test_prd_cannot_skip_to_tasks(self):
        """PRD_READY → TASKS_READY is invalid (skips ARCHITECTURE)."""
        fsm = FSMFixtures.prd_ready_state()
        assert not fsm.can_transition_to(FSMState.TASKS_READY)
        with pytest.raises(ValueError):
            fsm.transition(FSMState.TASKS_READY)

    def test_done_has_no_transitions(self):
        """DONE state has no valid transitions."""
        fsm = FSMFixtures.done_state()
        assert not fsm.can_transition_to(FSMState.INIT)
        assert not fsm.can_transition_to(FSMState.DISCOVERY)
        assert not fsm.can_transition_to(FSMState.DONE)
        with pytest.raises(ValueError):
            fsm.transition(FSMState.INIT)


class TestTransitionHistory:
    """Test FSM tracks transition history correctly."""

    def test_history_grows_with_transitions(self):
        """History records all transitions."""
        fsm = FSMEngine()
        assert len(fsm.get_history()) == 1

        fsm.transition(FSMState.DISCOVERY)
        assert len(fsm.get_history()) == 2

        fsm.transition(FSMState.PRD_READY)
        assert len(fsm.get_history()) == 3

    def test_history_includes_reasons(self):
        """History includes transition reasons."""
        fsm = FSMEngine()
        fsm.transition(FSMState.DISCOVERY, "starting discovery phase")
        history = fsm.get_history()

        assert history[-1]["reason"] == "starting discovery phase"

    def test_history_is_chronological(self):
        """History entries are ordered by timestamp."""
        fsm = FSMEngine()
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)
        fsm.transition(FSMState.ARCHITECTURE_READY)

        history = fsm.get_history()
        for i in range(len(history) - 1):
            assert history[i]["timestamp"] <= history[i + 1]["timestamp"]

    def test_history_immutable(self):
        """History copy cannot affect FSM."""
        fsm = FSMEngine()
        history1 = fsm.get_history()
        history1.append({"state": "FAKE", "timestamp": "2026-05-14"})

        history2 = fsm.get_history()
        assert len(history2) == len(fsm.get_history())


class TestPersistence:
    """Test FSM serialization and deserialization."""

    def test_serialize_init_state(self):
        """Can serialize INIT state."""
        fsm = FSMEngine()
        data = fsm.to_dict()

        assert data["current_state"] == "INIT"
        assert len(data["state_history"]) == 1

    def test_serialize_mid_lifecycle(self):
        """Can serialize mid-lifecycle state."""
        fsm = FSMFixtures.implementing_state()
        data = fsm.to_dict()

        assert data["current_state"] == "IMPLEMENTING"
        assert len(data["state_history"]) > 1

    def test_deserialize_matches_original(self):
        """Deserialized FSM matches original."""
        fsm1 = FSMFixtures.testing_state()
        fsm1.transition(FSMState.DONE, "tests pass")

        data = fsm1.to_dict()
        fsm2 = FSMEngine.from_dict(data)

        assert fsm2.get_state() == FSMState.DONE
        assert fsm2.get_state_value() == "DONE"
        assert len(fsm2.get_history()) == len(fsm1.get_history())

    def test_deserialized_fsm_is_valid(self):
        """Deserialized FSM is in valid state."""
        fsm1 = FSMFixtures.architecture_ready_state()
        data = fsm1.to_dict()
        fsm2 = FSMEngine.from_dict(data)

        AssertHelpers.assert_fsm_valid(fsm2)


class TestReset:
    """Test FSM reset functionality."""

    def test_reset_returns_to_init(self):
        """Reset moves FSM to INIT state."""
        fsm = FSMFixtures.done_state()
        fsm.reset()

        assert fsm.get_state() == FSMState.INIT

    def test_reset_clears_history(self):
        """Reset clears transition history."""
        fsm = FSMFixtures.implementing_state()
        assert len(fsm.get_history()) > 1

        fsm.reset()
        assert len(fsm.get_history()) == 1
        assert fsm.get_history()[0]["state"] == "INIT"

    def test_can_transition_after_reset(self):
        """FSM works correctly after reset."""
        fsm = FSMFixtures.done_state()
        fsm.reset()

        assert fsm.can_transition_to(FSMState.DISCOVERY)
        fsm.transition(FSMState.DISCOVERY)
        assert fsm.get_state() == FSMState.DISCOVERY


class TestComplexScenarios:
    """Test complex FSM scenarios."""

    def test_implementing_multiple_retries(self):
        """IMPLEMENTING can retry multiple times."""
        fsm = FSMFixtures.implementing_state()

        for i in range(5):
            assert fsm.get_state() == FSMState.IMPLEMENTING
            fsm.transition(FSMState.IMPLEMENTING, f"retry {i}")

        assert len(fsm.get_history()) > 5

    def test_testing_with_bug_fixes(self):
        """TESTING can loop to IMPLEMENTING and back."""
        fsm = FSMFixtures.testing_state()

        # First round of testing fails
        fsm.transition(FSMState.IMPLEMENTING, "bug found")
        assert fsm.get_state() == FSMState.IMPLEMENTING

        # Fix and retest
        fsm.transition(FSMState.TESTING, "retesting")
        assert fsm.get_state() == FSMState.TESTING

        # Test again fails
        fsm.transition(FSMState.IMPLEMENTING, "more bugs")

        # Eventually passes
        fsm.transition(FSMState.TESTING)
        fsm.transition(FSMState.DONE)

        assert fsm.get_state() == FSMState.DONE

    def test_full_lifecycle_with_loops(self):
        """Full lifecycle with IMPLEMENTING and TESTING loops."""
        fsm = FSMEngine()

        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)
        fsm.transition(FSMState.ARCHITECTURE_READY)
        fsm.transition(FSMState.TASKS_READY)

        # Implementing with retries
        fsm.transition(FSMState.IMPLEMENTING)
        fsm.transition(FSMState.IMPLEMENTING, "retry 1")
        fsm.transition(FSMState.IMPLEMENTING, "retry 2")

        # Testing with failures
        fsm.transition(FSMState.TESTING)
        fsm.transition(FSMState.IMPLEMENTING, "bugs found")
        fsm.transition(FSMState.TESTING, "retest")

        # Final success
        fsm.transition(FSMState.DONE)

        assert fsm.get_state() == FSMState.DONE
        AssertHelpers.assert_fsm_valid(fsm)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
