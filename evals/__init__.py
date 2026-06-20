"""Evaluation harness: deterministic safety invariants + an incident-replay runner.

The gate from decisions/0006-evaluation-gate.md. The safety invariants are
deterministic on purpose — the failures that matter (an unauthorized action, a
false all-clear) are the ones you cannot afford to discover on a live incident.
"""
