"""Test FSM Engine functionality"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from state.fsm_engine import FSMEngine, FSMState


def test_initial_state():
    """Test FSM starts in INIT state."""
    fsm = FSMEngine()
    assert fsm.get_state() == FSMState.INIT
    assert fsm.get_state_value() == "INIT"


def test_valid_forward_transitions():
    """Test all valid forward transitions."""
    fsm = FSMEngine()

    # INIT → DISCOVERY
    fsm.transition(FSMState.DISCOVERY, "starting discovery")
    assert fsm.get_state() == FSMState.DISCOVERY

    # DISCOVERY → PRD_READY
    fsm.transition(FSMState.PRD_READY, "prd complete")
    assert fsm.get_state() == FSMState.PRD_READY

    # PRD_READY → ARCHITECTURE_READY
    fsm.transition(FSMState.ARCHITECTURE_READY, "architecture designed")
    assert fsm.get_state() == FSMState.ARCHITECTURE_READY

    # ARCHITECTURE_READY → TASKS_READY
    fsm.transition(FSMState.TASKS_READY, "tasks compiled")
    assert fsm.get_state() == FSMState.TASKS_READY

    # TASKS_READY → IMPLEMENTING
    fsm.transition(FSMState.IMPLEMENTING, "starting implementation")
    assert fsm.get_state() == FSMState.IMPLEMENTING


def test_implementing_loop():
    """Test IMPLEMENTING can loop to itself and go to TESTING."""
    fsm = FSMEngine()
    fsm.current_state = FSMState.IMPLEMENTING

    # IMPLEMENTING → IMPLEMENTING (retry loop)
    fsm.transition(FSMState.IMPLEMENTING, "retry after failure")
    assert fsm.get_state() == FSMState.IMPLEMENTING

    # IMPLEMENTING → TESTING
    fsm.transition(FSMState.TESTING, "tests ready")
    assert fsm.get_state() == FSMState.TESTING


def test_testing_loop():
    """Test TESTING can loop to IMPLEMENTING or go to DONE."""
    fsm = FSMEngine()
    fsm.current_state = FSMState.TESTING

    # TESTING → IMPLEMENTING (bugs found)
    fsm.transition(FSMState.IMPLEMENTING, "fixing bugs")
    assert fsm.get_state() == FSMState.IMPLEMENTING

    # Back to TESTING
    fsm.transition(FSMState.TESTING, "retesting")
    assert fsm.get_state() == FSMState.TESTING

    # TESTING → DONE
    fsm.transition(FSMState.DONE, "all tests pass")
    assert fsm.get_state() == FSMState.DONE


def test_invalid_transition():
    """Test invalid transitions raise errors."""
    fsm = FSMEngine()

    # Can't skip states
    try:
        fsm.transition(FSMState.PRD_READY)
        assert False, "Should have raised error"
    except ValueError as e:
        assert "Invalid transition" in str(e)
        assert "INIT → PRD_READY" in str(e)


def test_transition_from_done():
    """Test DONE state has no valid transitions."""
    fsm = FSMEngine()
    fsm.current_state = FSMState.DONE

    try:
        fsm.transition(FSMState.INIT)
        assert False, "Should have raised error"
    except ValueError:
        pass


def test_can_transition_check():
    """Test can_transition_to validation."""
    fsm = FSMEngine()
    assert fsm.can_transition_to(FSMState.DISCOVERY) is True
    assert fsm.can_transition_to(FSMState.PRD_READY) is False


def test_state_history():
    """Test transition history is recorded."""
    fsm = FSMEngine()
    fsm.transition(FSMState.DISCOVERY, "starting")
    fsm.transition(FSMState.PRD_READY, "complete")

    history = fsm.get_history()
    assert len(history) == 3
    assert history[0]["state"] == "INIT"
    assert history[1]["state"] == "DISCOVERY"
    assert history[2]["state"] == "PRD_READY"
    assert history[1]["reason"] == "starting"


def test_persistence():
    """Test FSM can be serialized and deserialized."""
    fsm1 = FSMEngine()
    fsm1.transition(FSMState.DISCOVERY)
    fsm1.transition(FSMState.PRD_READY)

    # Serialize
    data = fsm1.to_dict()

    # Deserialize
    fsm2 = FSMEngine.from_dict(data)
    assert fsm2.get_state() == FSMState.PRD_READY
    assert len(fsm2.get_history()) == 3


def test_reset():
    """Test FSM can be reset to initial state."""
    fsm = FSMEngine()
    fsm.transition(FSMState.DISCOVERY)
    fsm.transition(FSMState.PRD_READY)

    fsm.reset()
    assert fsm.get_state() == FSMState.INIT
    assert len(fsm.get_history()) == 1


if __name__ == "__main__":
    test_initial_state()
    test_valid_forward_transitions()
    test_implementing_loop()
    test_testing_loop()
    test_invalid_transition()
    test_transition_from_done()
    test_can_transition_check()
    test_state_history()
    test_persistence()
    test_reset()
    print("✅ All FSM engine tests passed")
