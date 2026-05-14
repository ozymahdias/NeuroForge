Below is a **Codex-ready prompt pack** to build the full **NeuroForge OS (AI Factory 2026-grade)** step-by-step.

Each prompt is:

* isolated
* strictly sequential
* no missing dependencies
* safe for another AI to execute without context drift

---

# PROMPT 0 — BOOTSTRAP RULES (MANDATORY FIRST)

You are building a system called **NeuroForge OS** in a single Python monorepo.

## Core constraints:

* Strict sequential execution only (no parallelism)
* Brain and Shell are strictly separated
* Brain = reasoning only
* Shell = execution only
* No agent swarms
* No autonomous runtime loops

## Output rule:

* Only produce code for the requested module
* Do NOT implement other modules

---

# PROMPT 1 — MONOREPO SCAFFOLD

Create the full Python monorepo structure for **NeuroForge OS**.

## Requirements:

* create all folders (empty init files included)
* ensure clean import boundaries
* no logic yet

## Must include:

brain/
memory/
skills/
shell/
quality_gates/
protocols/
state/
tests/
main.py
config.yaml

## Output:

* directory tree
* empty **init**.py files where needed

---

# PROMPT 2 — STATE SYSTEM (project_state.json + loader)

Implement the state system.

## Requirements:

* project_state.json schema
* state loader/saver in Python
* versioned state updates
* append-only execution history

## Must support:

* requirements
* ADRs
* risks
* task graph
* execution history
* entropy metrics

## Constraints:

* no FSM logic yet
* no execution logic

---

# PROMPT 3 — FSM ENGINE (CORE ORCHESTRATION)

Implement the FSM controller.

## States:

INIT → DISCOVERY → PRD_READY → ARCHITECTURE_READY → TASKS_READY → IMPLEMENTING → TESTING → DONE

## Requirements:

* strict transitions only
* invalid transition throws error
* supports persistence via state system
* no task execution logic

---

# PROMPT 4 — DISCOVERY ENGINE (ENTROPY SYSTEM)

Implement DISCOVERY module.

## Must include:

* entropy calculator
* open-question generator
* assumption builder
* integration hook for idea-reality MCP

## Output:

* structured JSON only
* no PRD generation yet

---

# PROMPT 5 — IDEA REALITY VALIDATION MODULE

Implement **idea_reality_mcp adapter layer**.

## Must compute:

* market saturation score
* redundancy score
* feasibility score
* innovation delta

## Output:

```json
{
  "decision": "BUILD | PIVOT | KILL",
  "scores": {}
}
```

---

# PROMPT 6 — PRD GENERATOR

Implement PRD builder.

## Input:

* discovery output

## Output:

* structured PRD JSON:

  * requirements
  * constraints
  * assumptions
  * success metrics

## No architecture allowed here.

---

# PROMPT 7 — ARCHITECTURE + ADR ENGINE

Implement architecture generator.

## Must include:

* system design description
* ADR generation
* interface definitions
* dependency graph (logical only)

## MUST NOT:

* write code
* create tasks

---

# PROMPT 8 — TASK COMPILER (TDD ENGINE)

Implement task generator.

## Must:

* convert architecture → task graph
* enforce TDD order:

  1. test
  2. implement
  3. refactor

## Output:

* DAG of tasks
* sequential execution order enforced

---

# PROMPT 9 — BRAIN → SHELL PROTOCOL

Implement communication layer.

## Must define:

### Task Packet:

* files
* actions
* tests
* constraints

### Shell Response:

* status
* logs
* error signatures
* stacktrace hash

## Must include:

* context hashing
* sanitization rules
* no reasoning leakage

---

# PROMPT 10 — SHELL EXECUTOR (CODEx ENGINE)

Implement execution engine.

## Must:

* execute tasks sequentially
* write files
* run tests
* return structured results

## Forbidden:

* no planning
* no branching logic

---

# PROMPT 11 — QUALITY GATES PIPELINE

Implement validation pipeline:

Order:

1. idea-reality check
2. feasibility validator
3. unit tests
4. mutation testing (mutpy)
5. lint (plumbline)
6. security scan (shannon)
7. frontend check (react-doctor if applicable)

## Must:

* block on failure
* return structured failure reason

---

# PROMPT 12 — MEMORY SYSTEM ADAPTER

Implement memory layer.

## Option A:

* agentmemory adapter

## Option B:

* graph memory (Mnemograph style)

## Must support:

* decision replay
* causal tracing
* retrieval by:

  * task_id
  * ADR
  * risk event

---

# PROMPT 13 — SKILL ROUTER SYSTEM

Implement skill injection system.

## Skills:

* UI/UX Pro Max
* Shannon security model
* OracleTrace audit system
* React Doctor
* Mutpy analysis adapter
* Plumbline quality layer

## Must:

* select skills per FSM state
* no execution logic inside skills

---

# PROMPT 14 — ENTROPY + RESCUE SYSTEM

Implement failure detection system.

## Trigger Rescue Agent if:

* repeated stacktrace hash ≥ 2
* mutation score stagnant
* repeated test failure pattern

## Output:

* replan request (task-level only)

---

# PROMPT 15 — MAIN ORCHESTRATOR

Implement main.py.

## Must:

* load state
* run FSM step-by-step
* call Brain modules sequentially
* send tasks to Shell
* process results
* persist state

## STRICT RULE:

* no parallel execution
* no background workers
* no async orchestration

---

# PROMPT 16 — END-TO-END TEST HARNESS

Create system-level test.

## Must simulate:

* one full FSM cycle
* dummy project
* verify:

  * state transitions
  * task execution
  * persistence

---

# PROMPT 17 — CONFIG SYSTEM

Create config.yaml:

Must include:

* model endpoints (Ollama + GPT fallback)
* retry limits (max 3)
* mutation threshold
* security severity threshold
* execution mode (sequential ONLY)

---

## If you want next step

I can generate:

* 🔥 “single Codex mega-prompt” that builds the whole repo in one run
* or
* 🔥 step-by-step execution script (run prompts automatically in order)
* or
* 🔥 architecture diagram + data flow visualization of NeuroForge OS
