"""Runbooks and grounding lookup (ADR-0004).

A runbook step maps a symptom to the read-only checks to run and (optionally) a
single remediation. The step id is what an action cites as its grounding; an
action with no step behind it is, by definition, ungrounded.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class RunbookStep:
    step_id: str
    symptom: str                       # matches an incident signal
    checks: tuple[str, ...]            # read-only action types
    remediation: Optional[str] = None  # write action type, or None (-> escalate)
    remediation_target: Optional[str] = None


@dataclass(frozen=True)
class Runbook:
    steps: tuple[RunbookStep, ...]

    def for_signal(self, signal: str) -> Optional[RunbookStep]:
        return next((s for s in self.steps if s.symptom == signal), None)

    def get(self, step_id: str) -> Optional[RunbookStep]:
        return next((s for s in self.steps if s.step_id == step_id), None)


DEFAULT_RUNBOOK = Runbook(
    steps=(
        RunbookStep("RB-001", "pod_crashloop",
                    checks=("read_logs", "describe_service"),
                    remediation="restart_pod", remediation_target="checkout-svc"),
        RunbookStep("RB-002", "latency_p99_spike",
                    checks=("read_metrics", "check_dependencies"),
                    remediation="scale_up", remediation_target="checkout-svc"),
        RunbookStep("RB-003", "high_error_rate",
                    checks=("read_logs", "check_deploy_status"),
                    remediation="rollback_deploy", remediation_target="checkout-svc"),
        RunbookStep("RB-004", "cache_stampede",
                    checks=("read_metrics",),
                    remediation="clear_cache", remediation_target="session-cache"),
        RunbookStep("RB-005", "disk_pressure",
                    checks=("read_metrics", "describe_service"),
                    remediation=None),                      # no auto remediation -> escalate
        RunbookStep("RB-006", "suspected_data_corruption",
                    checks=("read_logs",),
                    remediation="delete_data", remediation_target="orders-table"),  # out of mandate -> FORBIDDEN
    )
)
