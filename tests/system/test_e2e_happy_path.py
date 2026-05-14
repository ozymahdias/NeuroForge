"""System tests - End-to-end full lifecycle execution"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import pytest
import tempfile
from state.fsm_engine import FSMEngine, FSMState
from state.state_manager import StateManager
from brain.validation_engine import IdeaRealityValidator, ValidationReport
from tests.helpers.assert_helpers import AssertHelpers


class TestE2EHappyPath:
    """Test complete system execution INIT → DONE."""

    def test_full_lifecycle_execution(self):
        """Execute full system lifecycle from INIT to DONE."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # INIT state
        assert fsm.get_state() == FSMState.INIT
        state_mgr.update_entropy_metrics({
            "open_questions": 10,
            "assumption_uncertainty": 0.7,
            "entropy_score": 0.8
        })
        state_mgr.save()

        # DISCOVERY phase
        fsm.transition(FSMState.DISCOVERY, "Starting discovery")
        state_mgr.add_requirement({
            "title": "Core Feature",
            "description": "Main functionality",
            "priority": "P0"
        })
        state_mgr.update_entropy_metrics({
            "open_questions": 5,
            "assumption_uncertainty": 0.5,
            "entropy_score": 0.6
        })
        state_mgr.save()
        assert fsm.get_state() == FSMState.DISCOVERY

        # PRD_READY phase
        fsm.transition(FSMState.PRD_READY, "PRD generated")
        state_mgr.add_requirement({
            "title": "UI Components",
            "description": "User interface elements",
            "priority": "P1"
        })
        state_mgr.add_adr({
            "title": "Use React for Frontend",
            "status": "ACCEPTED",
            "decision": "React provides component reusability"
        })
        state_mgr.update_entropy_metrics({
            "open_questions": 3,
            "assumption_uncertainty": 0.3,
            "entropy_score": 0.4
        })
        state_mgr.save()
        assert fsm.get_state() == FSMState.PRD_READY

        # ARCHITECTURE_READY phase
        fsm.transition(FSMState.ARCHITECTURE_READY, "Architecture designed")
        state_mgr.add_adr({
            "title": "PostgreSQL for Database",
            "status": "ACCEPTED",
            "decision": "ACID compliance required"
        })
        state_mgr.add_adr({
            "title": "Microservices Architecture",
            "status": "ACCEPTED",
            "decision": "Scale independently"
        })
        state_mgr.update_entropy_metrics({
            "open_questions": 1,
            "assumption_uncertainty": 0.1,
            "entropy_score": 0.2
        })
        state_mgr.save()
        assert fsm.get_state() == FSMState.ARCHITECTURE_READY

        # TASKS_READY phase
        fsm.transition(FSMState.TASKS_READY, "Tasks compiled")
        nodes = [
            {"id": "task_1", "name": "Setup Database", "status": "PENDING"},
            {"id": "task_2", "name": "Create User Model", "status": "PENDING"},
            {"id": "task_3", "name": "Implement Auth", "status": "PENDING"},
            {"id": "task_4", "name": "Build UI", "status": "PENDING"}
        ]
        edges = [
            {"from": "task_1", "to": "task_2"},
            {"from": "task_2", "to": "task_3"},
            {"from": "task_3", "to": "task_4"}
        ]
        state_mgr.update_task_graph(nodes, edges)
        state_mgr.save()
        assert fsm.get_state() == FSMState.TASKS_READY

        # IMPLEMENTING phase
        fsm.transition(FSMState.IMPLEMENTING, "Starting implementation")
        for i, task in enumerate(nodes, 1):
            state_mgr.record_execution(
                task["id"],
                "SUCCESS",
                f"Task {i} completed successfully"
            )
        state_mgr.save()
        assert fsm.get_state() == FSMState.IMPLEMENTING

        # TESTING phase
        fsm.transition(FSMState.TESTING, "Tests ready")
        state_mgr.update_entropy_metrics({
            "open_questions": 0,
            "assumption_uncertainty": 0.0,
            "entropy_score": 0.0
        })
        state_mgr.save()
        assert fsm.get_state() == FSMState.TESTING

        # DONE phase
        fsm.transition(FSMState.DONE, "All tests pass")
        state_mgr.save()
        assert fsm.get_state() == FSMState.DONE

        # Verify complete state
        final_state = state_mgr.get_state()
        assert len(final_state["requirements"]) == 2
        assert len(final_state["adrs"]) == 3
        assert len(final_state["task_graph"]["nodes"]) == 4
        assert final_state["entropy_metrics"]["entropy_score"] == 0.0

        # Verify state is valid
        AssertHelpers.assert_state_valid(state_mgr)
        AssertHelpers.assert_fsm_valid(fsm)
        AssertHelpers.assert_fsm_path_valid(fsm.get_history())


class TestE2EWithImplementingLoop:
    """Test lifecycle with IMPLEMENTING retry loops."""

    def test_implementing_with_multiple_retries(self):
        """IMPLEMENTING phase can have multiple retry loops."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Progress to IMPLEMENTING
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)
        fsm.transition(FSMState.ARCHITECTURE_READY)
        fsm.transition(FSMState.TASKS_READY)
        fsm.transition(FSMState.IMPLEMENTING)

        # Multiple implementation attempts
        attempts = 3
        for i in range(attempts):
            state_mgr.record_execution(
                f"task_batch_{i}",
                "SUCCESS" if i == attempts - 1 else "FAILED",
                f"Attempt {i + 1}"
            )

            if i < attempts - 1:
                fsm.transition(FSMState.IMPLEMENTING, f"Retry attempt {i + 1}")
            else:
                fsm.transition(FSMState.TESTING)

        state_mgr.save()

        # Verify all attempts recorded
        exec_history = [
            r for r in state_mgr.get_state()["execution_history"]
            if "task_id" in r
        ]
        assert len(exec_history) == attempts

        # Verify FSM path is valid
        AssertHelpers.assert_fsm_path_valid(fsm.get_history())


class TestE2EWithTestingLoop:
    """Test lifecycle with TESTING failure loops."""

    def test_testing_with_bug_fixes(self):
        """TESTING phase can loop back to IMPLEMENTING."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Progress to TESTING
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)
        fsm.transition(FSMState.ARCHITECTURE_READY)
        fsm.transition(FSMState.TASKS_READY)
        fsm.transition(FSMState.IMPLEMENTING)
        fsm.transition(FSMState.TESTING)

        # Testing cycle 1: fails, go back to IMPLEMENTING
        state_mgr.record_execution("test_1", "FAILED", "Test failed")
        fsm.transition(FSMState.IMPLEMENTING, "Bug found")

        # Implement fix
        state_mgr.record_execution("fix_1", "SUCCESS", "Fixed bug")

        # Testing cycle 2: still fails
        fsm.transition(FSMState.TESTING)
        state_mgr.record_execution("test_2", "FAILED", "Still failing")
        fsm.transition(FSMState.IMPLEMENTING, "More issues")

        # Implement final fix
        state_mgr.record_execution("fix_2", "SUCCESS", "Fixed all issues")

        # Testing cycle 3: success
        fsm.transition(FSMState.TESTING)
        state_mgr.record_execution("test_3", "SUCCESS", "All tests pass")
        fsm.transition(FSMState.DONE)

        state_mgr.save()

        # Verify final state
        assert fsm.get_state() == FSMState.DONE
        assert len(fsm.get_history()) > 7  # Multiple transitions

        # Verify valid path
        AssertHelpers.assert_fsm_path_valid(fsm.get_history())


class TestE2EDeterministicReplay:
    """Test deterministic replay of execution."""

    def test_replay_execution_deterministically(self):
        """Can replay execution from history deterministically."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name

        # Original execution
        fsm1 = FSMEngine()
        state_mgr1 = StateManager(temp_file)

        transitions = [
            (FSMState.DISCOVERY, "starting discovery"),
            (FSMState.PRD_READY, "prd complete"),
            (FSMState.ARCHITECTURE_READY, "arch complete"),
            (FSMState.TASKS_READY, "tasks ready"),
            (FSMState.IMPLEMENTING, "implementing"),
            (FSMState.TESTING, "testing"),
            (FSMState.DONE, "done")
        ]

        for target, reason in transitions:
            fsm1.transition(target, reason)

        state_mgr1.add_requirement({"title": "Feature"})
        state_mgr1.add_adr({"title": "ADR"})
        state_mgr1.save()

        # Replay execution
        original_history = fsm1.get_history()
        original_state = state_mgr1.get_state()

        # Load from file and verify
        fsm2 = FSMEngine.from_dict(fsm1.to_dict())
        state_mgr2 = StateManager(temp_file)

        # Replay should match
        assert fsm2.get_state() == FSMState.DONE
        assert len(state_mgr2.get_state()["requirements"]) == 1
        assert len(state_mgr2.get_state()["adrs"]) == 1

        # History should match
        assert len(fsm2.get_history()) == len(original_history)

    def test_execution_produces_same_results_on_replay(self):
        """Replaying same execution produces identical results."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        fsm = FSMEngine()
        state_mgr = StateManager(temp_file)

        # Record execution
        fsm.transition(FSMState.DISCOVERY)
        fsm.transition(FSMState.PRD_READY)

        state_mgr.add_requirement({"title": "Feature"})
        state_mgr.update_entropy_metrics({"entropy_score": 0.5})
        state_mgr.save()

        # Snapshot original
        snapshot1 = state_mgr.get_state()
        history1 = fsm.get_history()

        # Reload and verify identical
        fsm2 = FSMEngine.from_dict(fsm.to_dict())
        state_mgr2 = StateManager(temp_file)
        snapshot2 = state_mgr2.get_state()
        history2 = fsm2.get_history()

        assert snapshot1 == snapshot2
        assert len(history1) == len(history2)


class TestArtifactGeneration:
    """Test that all expected artifacts are generated."""

    def test_artifacts_generated_at_each_phase(self):
        """Artifacts are generated at critical phases."""
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".json").name
        state_mgr = StateManager(temp_file)

        # DISCOVERY artifacts
        state_mgr.add_requirement({"title": "Requirement 1"})
        state_mgr.save()

        # PRD artifacts
        state_mgr.add_adr({"title": "ADR 1"})
        state_mgr.save()

        # ARCHITECTURE artifacts
        state_mgr.add_adr({"title": "ADR 2"})
        state_mgr.add_risk({"description": "Risk 1", "impact": "MEDIUM"})
        state_mgr.save()

        # TASKS artifacts
        nodes = [{"id": "t1", "name": "Task 1"}]
        state_mgr.update_task_graph(nodes, [])
        state_mgr.save()

        # IMPLEMENTING artifacts
        state_mgr.record_execution("t1", "SUCCESS", "Executed")
        state_mgr.save()

        # Verify all present
        state = state_mgr.get_state()
        assert len(state["requirements"]) > 0
        assert len(state["adrs"]) > 0
        assert len(state["risks"]) > 0
        assert len(state["task_graph"]["nodes"]) > 0

        # Verify state file exists
        assert Path(temp_file).exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
