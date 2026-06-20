from src.runbook import DEFAULT_RUNBOOK


def test_lookup_by_signal():
    step = DEFAULT_RUNBOOK.for_signal("pod_crashloop")
    assert step is not None and step.remediation == "restart_pod"


def test_lookup_by_step_id():
    assert DEFAULT_RUNBOOK.get("RB-001").symptom == "pod_crashloop"


def test_unknown_signal_returns_none():
    assert DEFAULT_RUNBOOK.for_signal("nope") is None


def test_step_with_no_remediation():
    assert DEFAULT_RUNBOOK.for_signal("disk_pressure").remediation is None
