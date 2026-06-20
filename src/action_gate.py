"""The action gate: AUTO / REQUIRE_APPROVAL / FORBIDDEN.

Classifies a proposed action by blast radius and environment (ADR-0002) and by
whether it is grounded in a runbook (ADR-0004). The model's confidence is never
an input. Read-only diagnostics are always AUTO; production writes need a human;
out-of-mandate actions are forbidden regardless of grounding or confidence.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from src.incident import Action, Environment


class Verdict(Enum):
    AUTO = "AUTO"
    REQUIRE_APPROVAL = "REQUIRE_APPROVAL"
    FORBIDDEN = "FORBIDDEN"


@dataclass(frozen=True)
class ActionPolicy:
    action_type: str
    read_only: bool
    in_mandate: bool                       # False -> FORBIDDEN, always
    reversible: bool
    prod_requires_approval: bool = True     # reversible writes that still need a human in prod


@dataclass(frozen=True)
class VerdictDecision:
    verdict: Verdict
    action_type: str
    reason: str


def _ro(t: str) -> ActionPolicy:
    return ActionPolicy(t, read_only=True, in_mandate=True, reversible=True)


DEFAULT_POLICIES: dict[str, ActionPolicy] = {
    p.action_type: p
    for p in [
        # Read-only diagnostics — always AUTO.
        _ro("read_logs"), _ro("read_metrics"), _ro("read_traces"),
        _ro("check_deploy_status"), _ro("check_dependencies"), _ro("describe_service"),
        # Reversible writes.
        ActionPolicy("clear_cache", read_only=False, in_mandate=True, reversible=True,
                     prod_requires_approval=False),   # low blast: auto even in prod, when grounded
        ActionPolicy("restart_pod", read_only=False, in_mandate=True, reversible=True,
                     prod_requires_approval=True),
        ActionPolicy("scale_up", read_only=False, in_mandate=True, reversible=True,
                     prod_requires_approval=True),
        ActionPolicy("drain_node", read_only=False, in_mandate=True, reversible=True,
                     prod_requires_approval=True),
        ActionPolicy("rollback_deploy", read_only=False, in_mandate=True, reversible=True,
                     prod_requires_approval=True),
        # Irreversible (in mandate, but a human decides).
        ActionPolicy("failover_region", read_only=False, in_mandate=True, reversible=False),
        # Out of mandate — FORBIDDEN regardless of grounding or confidence.
        ActionPolicy("delete_data", read_only=False, in_mandate=False, reversible=False),
        ActionPolicy("modify_iam", read_only=False, in_mandate=False, reversible=False),
        ActionPolicy("disable_security_control", read_only=False, in_mandate=False, reversible=False),
        ActionPolicy("scale_to_zero", read_only=False, in_mandate=False, reversible=False),
    ]
}


def is_read_only(action_type: str, registry: dict[str, ActionPolicy] = DEFAULT_POLICIES) -> bool:
    policy = registry.get(action_type)
    return policy is not None and policy.read_only


def classify(
    action: Action,
    registry: dict[str, ActionPolicy] = DEFAULT_POLICIES,
) -> VerdictDecision:
    """Classify a proposed action. ``action.confidence`` is never read."""
    policy = registry.get(action.type)

    if policy is None:
        return VerdictDecision(
            Verdict.REQUIRE_APPROVAL, action.type,
            "unknown action type; a human decides, never silent AUTO",
        )
    if policy.read_only:
        return VerdictDecision(Verdict.AUTO, action.type, "read-only diagnostic")
    if not policy.in_mandate:
        return VerdictDecision(Verdict.FORBIDDEN, action.type, "outside the agent's mandate")
    if action.grounded_in is None:
        return VerdictDecision(
            Verdict.REQUIRE_APPROVAL, action.type,
            "no runbook grounding; a human decides",
        )
    if not policy.reversible:
        return VerdictDecision(
            Verdict.REQUIRE_APPROVAL, action.type, "irreversible action; a human decides",
        )
    if action.environment is Environment.PROD and policy.prod_requires_approval:
        return VerdictDecision(
            Verdict.REQUIRE_APPROVAL, action.type, "reversible write in production",
        )
    return VerdictDecision(
        Verdict.AUTO, action.type, "grounded, reversible, low blast radius",
    )
