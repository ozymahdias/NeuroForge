"""State system - project state management and persistence"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


class StateManager:
    """Manages project state with versioned updates and append-only history."""

    def __init__(self, state_file: str = "project_state.json"):
        self.state_file = Path(state_file)
        self.state: Dict[str, Any] = self._load_state()

    def _load_state(self) -> Dict[str, Any]:
        """Load state from disk, or initialize empty."""
        if self.state_file.exists():
            with open(self.state_file) as f:
                return json.load(f)
        return self._init_empty_state()

    def _init_empty_state(self) -> Dict[str, Any]:
        """Create initial empty state structure."""
        return {
            "version": 1,
            "created_at": datetime.now().isoformat(),
            "requirements": [],
            "adrs": [],
            "risks": [],
            "task_graph": {
                "nodes": [],
                "edges": []
            },
            "execution_history": [],
            "entropy_metrics": {
                "open_questions": 0,
                "assumption_uncertainty": 0.0,
                "entropy_score": 0.0
            }
        }

    def save(self) -> None:
        """Persist state to disk."""
        self.state["updated_at"] = datetime.now().isoformat()
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2)

    def add_requirement(self, requirement: Dict[str, Any]) -> None:
        """Append requirement (immutable)."""
        requirement["id"] = len(self.state["requirements"])
        requirement["added_at"] = datetime.now().isoformat()
        self.state["requirements"].append(requirement)
        self._record_history("ADD_REQUIREMENT", requirement)

    def add_adr(self, adr: Dict[str, Any]) -> None:
        """Append Architecture Decision Record."""
        adr["id"] = len(self.state["adrs"])
        adr["added_at"] = datetime.now().isoformat()
        self.state["adrs"].append(adr)
        self._record_history("ADD_ADR", adr)

    def add_risk(self, risk: Dict[str, Any]) -> None:
        """Append risk item."""
        risk["id"] = len(self.state["risks"])
        risk["added_at"] = datetime.now().isoformat()
        self.state["risks"].append(risk)
        self._record_history("ADD_RISK", risk)

    def update_task_graph(self, nodes: List[Dict], edges: List[Dict]) -> None:
        """Update task graph (versioned)."""
        self.state["task_graph"] = {
            "nodes": nodes,
            "edges": edges,
            "updated_at": datetime.now().isoformat()
        }
        self._record_history("UPDATE_TASK_GRAPH",
                           {"node_count": len(nodes), "edge_count": len(edges)})

    def record_execution(self, task_id: str, status: str, output: str) -> None:
        """Append execution record (immutable)."""
        record = {
            "task_id": task_id,
            "status": status,
            "output": output,
            "timestamp": datetime.now().isoformat()
        }
        self.state["execution_history"].append(record)

    def update_entropy_metrics(self, metrics: Dict[str, float]) -> None:
        """Update entropy metrics."""
        self.state["entropy_metrics"].update(metrics)
        self.state["entropy_metrics"]["updated_at"] = datetime.now().isoformat()
        self._record_history("UPDATE_ENTROPY", metrics)

    def _record_history(self, action: str, payload: Any) -> None:
        """Internal: append to execution history."""
        entry = {
            "action": action,
            "timestamp": datetime.now().isoformat(),
            "payload": payload
        }
        self.state["execution_history"].append(entry)

    def get_state(self) -> Dict[str, Any]:
        """Return current state snapshot."""
        return self.state.copy()

    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """Get execution history, optionally limited."""
        history = self.state["execution_history"]
        return history[-limit:] if limit else history
