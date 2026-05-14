"""FSM Engine - Core orchestration state machine"""

from enum import Enum
from typing import Optional
from datetime import datetime


class FSMState(Enum):
    """Valid FSM states for NeuroForge OS orchestration."""
    INIT = "INIT"
    DISCOVERY = "DISCOVERY"
    PRD_READY = "PRD_READY"
    ARCHITECTURE_READY = "ARCHITECTURE_READY"
    TASKS_READY = "TASKS_READY"
    IMPLEMENTING = "IMPLEMENTING"
    TESTING = "TESTING"
    DONE = "DONE"


class FSMEngine:
    """Finite State Machine controller with strict transition validation."""

    # Define valid state transitions
    VALID_TRANSITIONS = {
        FSMState.INIT: [FSMState.DISCOVERY],
        FSMState.DISCOVERY: [FSMState.PRD_READY],
        FSMState.PRD_READY: [FSMState.ARCHITECTURE_READY],
        FSMState.ARCHITECTURE_READY: [FSMState.TASKS_READY],
        FSMState.TASKS_READY: [FSMState.IMPLEMENTING],
        FSMState.IMPLEMENTING: [FSMState.TESTING, FSMState.IMPLEMENTING],
        FSMState.TESTING: [FSMState.IMPLEMENTING, FSMState.DONE],
        FSMState.DONE: [],
    }

    def __init__(self, initial_state: FSMState = FSMState.INIT):
        self.current_state = initial_state
        self.state_history = [
            {
                "state": initial_state.value,
                "timestamp": datetime.now().isoformat(),
                "reason": "initialization"
            }
        ]

    def can_transition_to(self, target_state: FSMState) -> bool:
        """Check if transition is valid without changing state."""
        return target_state in self.VALID_TRANSITIONS.get(self.current_state, [])

    def transition(self, target_state: FSMState, reason: str = "") -> None:
        """Transition to target state with validation."""
        if not self.can_transition_to(target_state):
            valid = [s.value for s in self.VALID_TRANSITIONS.get(self.current_state, [])]
            raise ValueError(
                f"Invalid transition: {self.current_state.value} → {target_state.value}. "
                f"Valid transitions: {valid}"
            )

        self.current_state = target_state
        self.state_history.append({
            "state": target_state.value,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })

    def get_state(self) -> FSMState:
        """Get current state."""
        return self.current_state

    def get_state_value(self) -> str:
        """Get current state as string."""
        return self.current_state.value

    def get_history(self) -> list:
        """Get transition history."""
        return self.state_history.copy()

    def reset(self) -> None:
        """Reset FSM to initial state."""
        self.current_state = FSMState.INIT
        self.state_history = [{
            "state": FSMState.INIT.value,
            "timestamp": datetime.now().isoformat(),
            "reason": "reset"
        }]

    def to_dict(self) -> dict:
        """Serialize FSM state for persistence."""
        return {
            "current_state": self.current_state.value,
            "state_history": self.state_history
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FSMEngine":
        """Deserialize FSM state from persistence."""
        engine = cls(FSMState(data["current_state"]))
        engine.state_history = data["state_history"]
        return engine
