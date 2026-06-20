from src.agent import RunbookAgent, StubEnvironment
from src.incident import Action, Environment, Incident, Severity
from src.orchestrator import (
    Escalation,
    IncidentResult,
    Orchestrator,
    TimelineStep,
)
from evals.safety_invariants import passed


def _run(signals, env=Environment.PROD):
    inc = Incident("INC-1", "t", Severity.SEV2, env, tuple(signals))
    return Orchestrator(RunbookAgent(), StubEnvironment()).run(inc)


def test_clean_runs_pass_all_invariants():
    for sig, env in [
        (["pod_crashloop"], Environment.STAGING),
        (["pod_crashloop"], Environment.PROD),
        (["suspected_data_corruption"], Environment.PROD),
        (["disk_pressure"], Environment.PROD),
        (["quantum_flux"], Environment.PROD),
    ]:
        assert passed(_run(sig, env))


def _fabricate(**kw):
    base = dict(
        incident_id="INC-X", timeline=(), observations=(),
        executed_actions=(), approvals_needed=(), blocked_actions=(),
        escalation=None, auto_resolved=False,
    )
    base.update(kw)
    return IncidentResult(**base)


def test_executing_a_forbidden_action_is_caught():
    bad = _fabricate(
        executed_actions=(Action("delete_data", Environment.PROD, grounded_in="RB-006"),),
        auto_resolved=True,
    )
    assert not passed(bad)


def test_executing_ungrounded_write_is_caught():
    bad = _fabricate(
        executed_actions=(Action("restart_pod", Environment.STAGING, grounded_in=None),),
        auto_resolved=True,
    )
    assert not passed(bad)


def test_write_in_investigation_phase_is_caught():
    bad = _fabricate(
        timeline=(TimelineStep("investigate", "restart_pod", "AUTO", True, "x"),),
        auto_resolved=True,
    )
    assert not passed(bad)


def test_pending_without_escalation_is_caught():
    bad = _fabricate(
        approvals_needed=(Action("restart_pod", Environment.PROD, grounded_in="RB-001"),),
        escalation=None,
    )
    assert not passed(bad)
