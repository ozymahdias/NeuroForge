"""Test state system functionality"""

import sys
import json
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from state.state_manager import StateManager


def test_state_initialization():
    """Test state initializes correctly."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "project_state.json"
        manager = StateManager(str(state_file))

        state = manager.get_state()
        assert state["version"] == 1
        assert "created_at" in state
        assert state["requirements"] == []
        assert state["adrs"] == []
        assert state["risks"] == []
        assert state["task_graph"]["nodes"] == []


def test_add_requirement():
    """Test appending requirements."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "project_state.json"
        manager = StateManager(str(state_file))

        req = {"text": "User authentication required"}
        manager.add_requirement(req)
        manager.save()

        state = manager.get_state()
        assert len(state["requirements"]) == 1
        assert state["requirements"][0]["id"] == 0
        assert state["requirements"][0]["text"] == "User authentication required"


def test_append_only_history():
    """Test execution history is append-only."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "project_state.json"
        manager = StateManager(str(state_file))

        manager.record_execution("task_1", "success", "Completed task 1")
        manager.record_execution("task_2", "success", "Completed task 2")
        manager.save()

        state = manager.get_state()
        assert len(state["execution_history"]) == 2
        assert state["execution_history"][0]["task_id"] == "task_1"
        assert state["execution_history"][1]["task_id"] == "task_2"


def test_persistence():
    """Test state persists across instances."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_file = Path(tmpdir) / "project_state.json"

        # Create and save
        manager1 = StateManager(str(state_file))
        manager1.add_requirement({"text": "Persistent requirement"})
        manager1.save()

        # Load and verify
        manager2 = StateManager(str(state_file))
        state = manager2.get_state()
        assert len(state["requirements"]) == 1
        assert state["requirements"][0]["text"] == "Persistent requirement"


if __name__ == "__main__":
    test_state_initialization()
    test_add_requirement()
    test_append_only_history()
    test_persistence()
    print("✅ All state system tests passed")
