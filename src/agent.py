"""Agent interface, a deterministic runbook agent, and a read-only environment stub.

The orchestration is the differentiated logic (see orchestrator.py); the "agent"
is pluggable. ``RunbookAgent`` follows a runbook deterministically so the system
runs and is testable with no model call. A real LLM agent implements the same
``investigate`` / ``remediate`` interface.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Protocol, Sequence

from src.incident import Action, Incident, Observation
from src.runbook import DEFAULT_RUNBOOK, Runbook, RunbookStep


class Agent(Protocol):
    def investigate(self, incident: Incident, observations: Sequence[Observation]) -> list[Action]: ...
    def remediate(self, incident: Incident, observations: Sequence[Observation]) -> list[Action]: ...


class Environment(Protocol):
    def read(self, action_type: str, target: Optional[str]) -> str: ...
    def act(self, action: Action) -> None: ...


@dataclass
class StubEnvironment:
    """Deterministic environment: canned read findings, records executed actions."""

    findings: dict[str, str] = field(default_factory=dict)
    executed: list[Action] = field(default_factory=list)

    def read(self, action_type: str, target: Optional[str]) -> str:
        return self.findings.get(action_type, f"{action_type}: nominal")

    def act(self, action: Action) -> None:
        self.executed.append(action)


@dataclass
class RunbookAgent:
    """Follows the runbook for the incident's first matching signal."""

    runbook: Runbook = DEFAULT_RUNBOOK

    def _step(self, incident: Incident) -> Optional[RunbookStep]:
        for signal in incident.signals:
            step = self.runbook.for_signal(signal)
            if step is not None:
                return step
        return None

    def investigate(self, incident: Incident, observations: Sequence[Observation]) -> list[Action]:
        step = self._step(incident)
        if step is None:
            return []
        done = {o.action_type for o in observations}
        return [
            Action(type=c, environment=incident.environment, grounded_in=step.step_id)
            for c in step.checks
            if c not in done
        ]

    def remediate(self, incident: Incident, observations: Sequence[Observation]) -> list[Action]:
        step = self._step(incident)
        if step is None or step.remediation is None:
            return []
        return [
            Action(
                type=step.remediation,
                environment=incident.environment,
                grounded_in=step.step_id,
                target=step.remediation_target,
            )
        ]
