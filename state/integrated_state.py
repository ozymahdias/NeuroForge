"""Integrated State and FSM persistence"""

from typing import Optional
from .state_manager import StateManager
from .fsm_engine import FSMEngine, FSMState


class IntegratedState:
    """Manages both project state and FSM state together."""

    def __init__(self, state_file: str = "project_state.json"):
        self.state_manager = StateManager(state_file)
        self.fsm = self._load_fsm()

    def _load_fsm(self) -> FSMEngine:
        """Load FSM state from project state, or create new."""
        state = self.state_manager.get_state()
        if "fsm" in state:
            return FSMEngine.from_dict(state["fsm"])
        return FSMEngine()

    def transition_fsm(self, target_state: FSMState, reason: str = "") -> None:
        """Transition FSM and persist."""
        self.fsm.transition(target_state, reason)
        self._persist_fsm()

    def _persist_fsm(self) -> None:
        """Save FSM state to project state."""
        self.state_manager.state["fsm"] = self.fsm.to_dict()

    def save(self) -> None:
        """Persist all state (project + FSM)."""
        self._persist_fsm()
        self.state_manager.save()

    def get_fsm_state(self) -> FSMState:
        """Get current FSM state."""
        return self.fsm.get_state()

    def get_fsm_state_value(self) -> str:
        """Get current FSM state as string."""
        return self.fsm.get_state_value()

    def get_project_state(self):
        """Get project state snapshot."""
        return self.state_manager.get_state()

    def add_requirement(self, requirement: dict) -> None:
        """Add requirement to project state."""
        self.state_manager.add_requirement(requirement)

    def add_adr(self, adr: dict) -> None:
        """Add ADR to project state."""
        self.state_manager.add_adr(adr)

    def record_execution(self, task_id: str, status: str, output: str) -> None:
        """Record execution in project state."""
        self.state_manager.record_execution(task_id, status, output)
