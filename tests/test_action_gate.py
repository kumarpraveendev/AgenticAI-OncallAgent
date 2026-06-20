from src.action_gate import Verdict, classify
from src.incident import Action, Environment

PROD = Environment.PROD
STG = Environment.STAGING


def test_read_only_is_auto():
    assert classify(Action("read_logs", PROD)).verdict is Verdict.AUTO


def test_reversible_write_auto_in_staging():
    a = Action("restart_pod", STG, grounded_in="RB-001")
    assert classify(a).verdict is Verdict.AUTO


def test_reversible_write_needs_approval_in_prod():
    a = Action("restart_pod", PROD, grounded_in="RB-001")
    assert classify(a).verdict is Verdict.REQUIRE_APPROVAL


def test_low_blast_action_auto_even_in_prod():
    a = Action("clear_cache", PROD, grounded_in="RB-004")
    assert classify(a).verdict is Verdict.AUTO


def test_ungrounded_write_needs_approval():
    a = Action("restart_pod", STG, grounded_in=None)
    assert classify(a).verdict is Verdict.REQUIRE_APPROVAL


def test_irreversible_needs_approval():
    a = Action("failover_region", PROD, grounded_in="RB-X")
    assert classify(a).verdict is Verdict.REQUIRE_APPROVAL


def test_out_of_mandate_is_forbidden():
    a = Action("delete_data", PROD, grounded_in="RB-006")
    assert classify(a).verdict is Verdict.FORBIDDEN


def test_unknown_action_needs_approval():
    a = Action("frobnicate", PROD, grounded_in="RB-Z")
    assert classify(a).verdict is Verdict.REQUIRE_APPROVAL


import pytest


@pytest.mark.parametrize("confidence", [0.01, 0.5, 0.99, 1.0])
def test_confidence_never_changes_a_prod_write_verdict(confidence):
    a = Action("restart_pod", PROD, grounded_in="RB-001", confidence=confidence)
    assert classify(a).verdict is Verdict.REQUIRE_APPROVAL


@pytest.mark.parametrize("confidence", [0.01, 0.99])
def test_confidence_never_authorizes_a_forbidden_action(confidence):
    a = Action("delete_data", PROD, grounded_in="RB-006", confidence=confidence)
    assert classify(a).verdict is Verdict.FORBIDDEN
