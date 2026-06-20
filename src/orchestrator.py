"""The gated two-phase diagnose->act orchestrator (ADR-0003).

Phase 1 (INVESTIGATE) runs only read-only diagnostics — a write proposed here is
rejected, not executed; that rejection IS the read/write boundary. Phase 2 (ACT)
sends every proposed remediation through the action gate (ADR-0002): AUTO runs,
REQUIRE_APPROVAL is packaged for a human, FORBIDDEN is blocked. Anything left
pending produces a full-context escalation (ADR-0005). The whole run is a
reconstructable audit trail (ADR-0007).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.action_gate import DEFAULT_POLICIES, ActionPolicy, Verdict, classify, is_read_only
from src.agent import Agent, Environment
from src.incident import Action, Incident, Observation, Phase


@dataclass(frozen=True)
class TimelineStep:
    phase: str
    action_type: str
    verdict: str
    executed: bool
    detail: str


@dataclass(frozen=True)
class Escalation:
    incident_id: str
    summary: str
    hypothesis: str
    recommended: tuple[str, ...]    # approval-needed actions, with grounding
    blocked: tuple[str, ...]        # forbidden actions
    timeline: tuple[TimelineStep, ...]
    reason: str


@dataclass(frozen=True)
class IncidentResult:
    incident_id: str
    timeline: tuple[TimelineStep, ...]
    observations: tuple[Observation, ...]
    executed_actions: tuple[Action, ...]
    approvals_needed: tuple[Action, ...]
    blocked_actions: tuple[Action, ...]
    escalation: Escalation | None
    auto_resolved: bool


class Orchestrator:
    def __init__(
        self,
        agent: Agent,
        environment: Environment,
        registry: dict[str, ActionPolicy] = DEFAULT_POLICIES,
        max_investigation_steps: int = 8,
    ):
        self._agent = agent
        self._env = environment
        self._registry = registry
        self._max_steps = max_investigation_steps

    def run(self, incident: Incident) -> IncidentResult:
        timeline: list[TimelineStep] = []
        observations: list[Observation] = []

        # --- Phase 1: INVESTIGATE (read-only only) -------------------------
        for _ in range(self._max_steps):
            proposals = self._agent.investigate(incident, observations)
            if not proposals:
                break
            progressed = False
            for action in proposals:
                if not is_read_only(action.type, self._registry):
                    # The read/write boundary: a write in the investigation phase
                    # is rejected, never executed.
                    timeline.append(TimelineStep(
                        Phase.INVESTIGATE.value, action.type, "REJECTED", False,
                        "writes are not permitted during investigation",
                    ))
                    continue
                finding = self._env.read(action.type, action.target)
                observations.append(Observation(action.type, finding))
                timeline.append(TimelineStep(
                    Phase.INVESTIGATE.value, action.type, Verdict.AUTO.value, True, finding,
                ))
                progressed = True
            if not progressed:
                break

        # --- Phase 2: ACT (every action gated) -----------------------------
        executed: list[Action] = []
        approvals: list[Action] = []
        blocked: list[Action] = []
        for action in self._agent.remediate(incident, observations):
            decision = classify(action, self._registry)
            if decision.verdict is Verdict.AUTO:
                self._env.act(action)
                executed.append(action)
                timeline.append(TimelineStep(
                    Phase.ACT.value, action.type, "AUTO", True,
                    f"executed; {decision.reason}; grounded in {action.grounded_in}",
                ))
            elif decision.verdict is Verdict.REQUIRE_APPROVAL:
                approvals.append(action)
                timeline.append(TimelineStep(
                    Phase.ACT.value, action.type, "REQUIRE_APPROVAL", False,
                    f"needs approval; {decision.reason}",
                ))
            else:  # FORBIDDEN
                blocked.append(action)
                timeline.append(TimelineStep(
                    Phase.ACT.value, action.type, "FORBIDDEN", False,
                    f"blocked; {decision.reason}",
                ))

        # --- Escalation & resolution --------------------------------------
        unresolved = not executed and not approvals and not blocked
        auto_resolved = bool(executed) and not approvals and not blocked
        escalation = None
        if approvals or blocked or unresolved:
            escalation = self._build_escalation(
                incident, tuple(timeline), tuple(observations),
                tuple(approvals), tuple(blocked), unresolved,
            )

        return IncidentResult(
            incident_id=incident.incident_id,
            timeline=tuple(timeline),
            observations=tuple(observations),
            executed_actions=tuple(executed),
            approvals_needed=tuple(approvals),
            blocked_actions=tuple(blocked),
            escalation=escalation,
            auto_resolved=auto_resolved,
        )

    @staticmethod
    def _build_escalation(incident, timeline, observations, approvals, blocked, unresolved) -> Escalation:
        if blocked:
            reason = "an action the agent must not take was required"
        elif approvals:
            reason = "a consequential action needs human approval"
        else:
            reason = "no automated remediation applies to this incident"
        hypothesis = (
            observations[-1].finding if observations
            else "no read-only signal was conclusive"
        )
        return Escalation(
            incident_id=incident.incident_id,
            summary=f"{incident.title} [{incident.severity.name}, {incident.environment.value}]",
            hypothesis=hypothesis,
            recommended=tuple(f"{a.type} (grounded in {a.grounded_in})" for a in approvals),
            blocked=tuple(f"{a.type}: forbidden" for a in blocked),
            timeline=timeline,
            reason=reason,
        )
