"""FSM test fixtures - reusable FSM instances at various states"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from state.fsm_engine import FSMEngine, FSMState
from datetime import datetime


class FSMFixtures:
    """Factory for FSM instances at various lifecycle states."""

    @staticmethod
    def init_state() -> FSMEngine:
        """FSM at INIT state."""
        return FSMEngine(FSMState.INIT)

    @staticmethod
    def discovery_state() -> FSMEngine:
        """FSM at DISCOVERY state."""
        fsm = FSMEngine()
        fsm.transition(FSMState.DISCOVERY, "starting discovery")
        return fsm

    @staticmethod
    def prd_ready_state() -> FSMEngine:
        """FSM at PRD_READY state."""
        fsm = FSMEngine()
        fsm.transition(FSMState.DISCOVERY, "discovery complete")
        fsm.transition(FSMState.PRD_READY, "prd generated")
        return fsm

    @staticmethod
    def architecture_ready_state() -> FSMEngine:
        """FSM at ARCHITECTURE_READY state."""
        fsm = FSMFixtures.prd_ready_state()
        fsm.transition(FSMState.ARCHITECTURE_READY, "architecture designed")
        return fsm

    @staticmethod
    def tasks_ready_state() -> FSMEngine:
        """FSM at TASKS_READY state."""
        fsm = FSMFixtures.architecture_ready_state()
        fsm.transition(FSMState.TASKS_READY, "tasks compiled")
        return fsm

    @staticmethod
    def implementing_state() -> FSMEngine:
        """FSM at IMPLEMENTING state."""
        fsm = FSMFixtures.tasks_ready_state()
        fsm.transition(FSMState.IMPLEMENTING, "starting implementation")
        return fsm

    @staticmethod
    def testing_state() -> FSMEngine:
        """FSM at TESTING state."""
        fsm = FSMFixtures.implementing_state()
        fsm.transition(FSMState.TESTING, "tests ready")
        return fsm

    @staticmethod
    def done_state() -> FSMEngine:
        """FSM at DONE state."""
        fsm = FSMFixtures.testing_state()
        fsm.transition(FSMState.DONE, "all tests pass")
        return fsm

    @staticmethod
    def full_lifecycle() -> FSMEngine:
        """Complete lifecycle: INIT → DONE."""
        return FSMFixtures.done_state()

    @staticmethod
    def implementing_loop() -> FSMEngine:
        """IMPLEMENTING state with multiple retries."""
        fsm = FSMEngine()
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)
        fsm.transition(FSMState.ARCHITECTURE_READY)
        fsm.transition(FSMState.TASKS_READY)
        fsm.transition(FSMState.IMPLEMENTING, "first attempt")
        fsm.transition(FSMState.IMPLEMENTING, "retry 1")
        fsm.transition(FSMState.IMPLEMENTING, "retry 2")
        return fsm

    @staticmethod
    def testing_with_failures() -> FSMEngine:
        """TESTING state with loop back to IMPLEMENTING."""
        fsm = FSMFixtures.implementing_state()
        fsm.transition(FSMState.TESTING, "first test run")
        fsm.transition(FSMState.IMPLEMENTING, "bug found")
        fsm.transition(FSMState.TESTING, "retest")
        return fsm
