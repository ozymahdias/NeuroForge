# NeuroForge Self-Testing Harness - Architecture

## Test System Overview

The NeuroForge test harness is a **black-box validation system** that treats NeuroForge as a complete system under test. It validates:

1. **FSM Correctness** - State transitions, history, persistence
2. **Module Separation** - Each module respects strict boundaries
3. **Integration Behavior** - Modules work together correctly
4. **System Lifecycle** - Full INIT → DONE execution works deterministically
5. **Failure Handling** - System detects and responds to failures correctly
6. **Quality Gates** - Mutation, lint, security gates function properly

## Test Layers

### Layer 1: Unit Tests (tests/unit/)
**Scope:** Single module in isolation
**Goal:** Each module functions correctly independently

- `test_fsm.py` - FSM state machine correctness
- `test_state_manager.py` - State persistence and history
- `test_validation_engine.py` - Validation logic and scoring
- `test_discovery_engine.py` - Discovery phase logic
- `test_skill_router.py` - Skill selection logic
- `test_shell_executor.py` - Shell task execution

**Execution:** Independent, order-agnostic
**Coverage:** Edge cases, boundary conditions, error states

---

### Layer 2: Integration Tests (tests/integration/)
**Scope:** Two or more modules interacting
**Goal:** Modules collaborate correctly across boundaries

- `test_fsm_state_integration.py` - FSM + StateManager synchronization
- `test_brain_memory_integration.py` - Brain + Memory consistency
- `test_shell_quality_gates_integration.py` - Shell execution + quality gates
- `test_discovery_validation_integration.py` - Discovery → Validation flow

**Execution:** Ordered dependency chains
**Coverage:** Data flow, state consistency, error propagation

---

### Layer 3: System Tests (tests/system/)
**Scope:** Full NeuroForge system end-to-end
**Goal:** Complete system behaves correctly from INIT → DONE

- `test_e2e_happy_path.py` - Full lifecycle: INIT → DISCOVERY → PRD → ARCHITECTURE → TASKS → IMPLEMENTING → TESTING → DONE
- `test_e2e_implementing_loop.py` - Retry loops in IMPLEMENTING state
- `test_e2e_testing_loop.py` - Retry loops in TESTING state
- `test_e2e_state_replay.py` - Deterministic replay of execution

**Execution:** Sequential (order required)
**Coverage:** Full workflows, artifact generation, history accuracy

---

### Layer 4: Regression Tests (tests/regression/)
**Scope:** Previously discovered failures + fixes
**Goal:** Ensure past failures don't resurface

- `test_regression_state_corruption.py` - State file corruption detection/recovery
- `test_regression_invalid_transitions.py` - Invalid FSM transitions blocked
- `test_regression_missing_artifacts.py` - Missing files detected
- `test_regression_entropy_calc.py` - Entropy calculation consistency

**Execution:** Sequential
**Coverage:** Known failure modes

---

### Layer 5: Failure Injection Tests (tests/failure_injection/)
**Scope:** System under adverse conditions
**Goal:** System correctly detects and responds to failures

- `test_repeated_stacktrace.py` - Entropy detection for repeated failures
- `test_broken_task_graph.py` - Dependency graph corruption handling
- `test_corrupted_state_file.py` - State file corruption recovery
- `test_invalid_fsm_transition.py` - Invalid transition blocking
- `test_missing_execution_output.py` - Missing execution output detection

**Execution:** Sequential
**Coverage:** Failure modes, error messages, recovery logic

---

### Layer 6: Quality Gates Tests (tests/quality_gates/)
**Scope:** Quality gate enforcement
**Goal:** Quality gates block invalid states

- `test_mutation_gate.py` - Mutation detection blocks execution
- `test_lint_gate.py` - Lint failures block execution
- `test_security_gate.py` - Security issues block execution
- `test_feasibility_gate.py` - Infeasible tasks blocked

**Execution:** Sequential
**Coverage:** Gate logic, blocking behavior, error reporting

---

## Test Execution Flow

### Sequential Execution Order (Required)

```
1. Unit Tests (all parallel)
   ├── test_fsm.py
   ├── test_state_manager.py
   ├── test_validation_engine.py
   ├── test_discovery_engine.py
   ├── test_skill_router.py
   └── test_shell_executor.py

2. Integration Tests (sequential)
   ├── test_fsm_state_integration.py
   ├── test_brain_memory_integration.py
   ├── test_shell_quality_gates_integration.py
   └── test_discovery_validation_integration.py

3. System Tests (sequential)
   ├── test_e2e_happy_path.py
   ├── test_e2e_implementing_loop.py
   ├── test_e2e_testing_loop.py
   └── test_e2e_state_replay.py

4. Regression Tests (sequential)
   ├── test_regression_state_corruption.py
   ├── test_regression_invalid_transitions.py
   ├── test_regression_missing_artifacts.py
   └── test_regression_entropy_calc.py

5. Failure Injection Tests (sequential)
   ├── test_repeated_stacktrace.py
   ├── test_broken_task_graph.py
   ├── test_corrupted_state_file.py
   ├── test_invalid_fsm_transition.py
   └── test_missing_execution_output.py

6. Quality Gates Tests (sequential)
   ├── test_mutation_gate.py
   ├── test_lint_gate.py
   ├── test_security_gate.py
   └── test_feasibility_gate.py
```

---

## Test Infrastructure

### Fixtures (tests/fixtures/)
Reusable test data and mocks:

- `fsm_fixtures.py` - FSM instances at various states
- `state_fixtures.py` - StateManager with pre-populated data
- `task_fixtures.py` - Task graphs, execution results
- `artifact_fixtures.py` - Sample PRD, architecture, task descriptions

### Helpers (tests/helpers/)
Utility functions for test execution:

- `state_reader.py` - Load/validate project_state.json
- `fsm_validator.py` - Validate FSM consistency
- `execution_replayer.py` - Replay execution history deterministically
- `assert_helpers.py` - Custom assertions for state/execution validation

---

## Key Validation Rules

### FSM Validation
- Current state must match last history entry
- History must be chronologically ordered
- Transitions must be valid per VALID_TRANSITIONS
- No duplicate consecutive states (except IMPLEMENTING→IMPLEMENTING, TESTING→TESTING)

### State Validation
- requirements/adrs/risks must be append-only
- task_graph.updated_at ≥ all node/edge timestamps
- execution_history must be append-only
- entropy_metrics.updated_at must be recent

### Integration Validation
- FSM state matches StateManager state
- Brain decisions correlate with state transitions
- Shell execution results recorded in execution_history
- Memory updates reflected in state version

### System Validation
- All artifacts exist when expected
- History is complete and consistent
- Final state is DONE
- All tasks executed in dependency order

---

## Determinism & Reproducibility

### Seeding
- All random operations use fixed seeds (test fixtures)
- Timestamps use frozen time or mock datetime
- Task IDs are deterministic (based on content, not random)

### Replay Mode
- Load execution_history from project_state.json
- Re-execute with same inputs
- Validate outputs match recorded history

### State Snapshots
- Save complete state before/after each test
- Compare snapshots for regressions
- Archive snapshots for replay validation

---

## Success Criteria

### Test Coverage
- ✅ All FSM states tested
- ✅ All state transitions tested
- ✅ All valid + invalid transitions covered
- ✅ All quality gate scenarios tested
- ✅ All module integration points tested
- ✅ Full lifecycle INIT→DONE executed
- ✅ Failure detection working
- ✅ State recovery functional

### Quality Metrics
- ✅ Zero production code modifications
- ✅ 100% deterministic execution
- ✅ All tests replayable
- ✅ Clear failure messages
- ✅ Structured JSON output
- ✅ <5 second test execution per test file

---

## Running the Tests

```bash
# Run all tests in order
python test_runner.py

# Run specific layer
pytest tests/unit/

# Run specific test
pytest tests/integration/test_fsm_state_integration.py::test_fsm_state_sync

# Run in replay mode
python test_runner.py --replay

# Generate coverage report
pytest --cov=. tests/
```

---

## Output Format

All tests output structured JSON:

```json
{
  "test_run": {
    "timestamp": "2026-05-14T12:00:00Z",
    "total_tests": 150,
    "passed": 145,
    "failed": 0,
    "skipped": 5,
    "duration_seconds": 12.34,
    "layers": {
      "unit": {"passed": 60, "failed": 0},
      "integration": {"passed": 30, "failed": 0},
      "system": {"passed": 35, "failed": 0},
      "regression": {"passed": 15, "failed": 0},
      "failure_injection": {"passed": 10, "failed": 0},
      "quality_gates": {"passed": 5, "failed": 0}
    },
    "system_health": "HEALTHY"
  }
}
```

---

## Maintenance

### Adding New Tests
1. Identify layer (unit/integration/system/regression/failure/gates)
2. Create test in appropriate directory
3. Update test_runner.py execution order
4. Run full suite to verify no conflicts
5. Commit with "test: add [test_name]" message

### Updating for System Changes
1. New states → add tests in test_fsm.py
2. New modules → add tests in tests/unit/
3. New quality gates → add tests in tests/quality_gates/
4. Never modify production code in test files
