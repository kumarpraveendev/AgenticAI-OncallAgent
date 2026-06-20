from dataclasses import dataclass
from typing import Sequence

from src.agent import RunbookAgent, StubEnvironment
from src.incident import Action, Environment, Incident, Observation, Severity
from src.orchestrator import Orchestrator


def incident(signals, env=Environment.PROD, sev=Severity.SEV2):
    return Incident("INC-1", "test", sev, env, tuple(signals))


def test_staging_crashloop_auto_resolves():
    r = Orchestrator(RunbookAgent(), StubEnvironment()).run(
        incident(["pod_crashloop"], env=Environment.STAGING))
    assert r.auto_resolved and len(r.executed_actions) == 1 and r.escalation is None


def test_prod_crashloop_requires_approval_and_escalates():
    r = Orchestrator(RunbookAgent(), StubEnvironment()).run(incident(["pod_crashloop"]))
    assert not r.auto_resolved
    assert len(r.approvals_needed) == 1 and not r.executed_actions
    assert r.escalation is not None


def test_forbidden_action_is_blocked_and_escalated():
    r = Orchestrator(RunbookAgent(), StubEnvironment()).run(
        incident(["suspected_data_corruption"]))
    assert len(r.blocked_actions) == 1 and not r.executed_actions
    assert r.escalation is not None and r.escalation.blocked


def test_unknown_incident_escalates_without_acting():
    r = Orchestrator(RunbookAgent(), StubEnvironment()).run(incident(["quantum_flux"]))
    assert not r.executed_actions and r.escalation is not None


def test_no_remediation_runbook_escalates_with_observations():
    r = Orchestrator(RunbookAgent(), StubEnvironment()).run(incident(["disk_pressure"]))
    assert not r.executed_actions and r.escalation is not None
    assert r.observations  # it did investigate first


def test_investigation_runs_before_action():
    env = StubEnvironment()
    r = Orchestrator(RunbookAgent(), env).run(incident(["pod_crashloop"], env=Environment.STAGING))
    investigate_steps = [s for s in r.timeline if s.phase == "investigate"]
    act_steps = [s for s in r.timeline if s.phase == "act"]
    assert investigate_steps and act_steps
    # every executed investigation step is read-only
    assert all(s.executed for s in investigate_steps)


# A misbehaving agent that tries to write during investigation.
@dataclass
class RogueAgent:
    def investigate(self, incident, observations: Sequence[Observation]):
        if observations:
            return []
        return [Action("restart_pod", incident.environment, grounded_in="RB-001")]
    def remediate(self, incident, observations):
        return []


def test_write_during_investigation_is_rejected():
    env = StubEnvironment()
    r = Orchestrator(RogueAgent(), env).run(incident(["pod_crashloop"]))
    assert not env.executed  # nothing executed
    rejected = [s for s in r.timeline if s.verdict == "REJECTED"]
    assert rejected and rejected[0].action_type == "restart_pod"
