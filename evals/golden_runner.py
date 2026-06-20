"""Incident-replay runner. Doubles as the CI eval gate (exit 1 on any failure).

Each case replays an incident through the real orchestrator and asserts the
expected outcome *and* that every safety invariant holds. The seed set here is
representative; in production it grows from replayed real incidents and every
near-miss (ADR-0006).

Run: ``python -m evals.golden_runner``
"""
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from src.agent import RunbookAgent, StubEnvironment
from src.incident import Environment, Incident, Severity
from src.orchestrator import Orchestrator
from evals.safety_invariants import check_all

CASES_PATH = Path(__file__).with_name("golden_cases.json")


@dataclass(frozen=True)
class Result:
    name: str
    passed: bool
    detail: str


def _build_incident(i: dict[str, Any]) -> Incident:
    return Incident(
        incident_id=i.get("incident_id", "INC-golden"),
        title=i["title"],
        severity=Severity[i["severity"]],
        environment=Environment(i["environment"]),
        signals=tuple(i["signals"]),
    )


def _run_case(case: dict[str, Any]) -> Result:
    incident = _build_incident(case["incident"])
    orchestrator = Orchestrator(RunbookAgent(), StubEnvironment())
    result = orchestrator.run(incident)

    exp = case["expect"]
    problems = []
    if result.auto_resolved != exp["auto_resolved"]:
        problems.append(f"auto_resolved: want {exp['auto_resolved']}, got {result.auto_resolved}")
    escalated = result.escalation is not None
    if escalated != exp["escalated"]:
        problems.append(f"escalated: want {exp['escalated']}, got {escalated}")
    if len(result.executed_actions) != exp["executed"]:
        problems.append(f"executed: want {exp['executed']}, got {len(result.executed_actions)}")
    if len(result.approvals_needed) != exp["approvals"]:
        problems.append(f"approvals: want {exp['approvals']}, got {len(result.approvals_needed)}")
    if len(result.blocked_actions) != exp["blocked"]:
        problems.append(f"blocked: want {exp['blocked']}, got {len(result.blocked_actions)}")

    for r in check_all(result):
        if not r.passed:
            problems.append(f"invariant {r.name}: {r.detail}")

    return Result(case["name"], not problems, "; ".join(problems))


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text())


def run_all(cases: list[dict[str, Any]]) -> list[Result]:
    return [_run_case(c) for c in cases]


def main() -> int:
    results = run_all(load_cases())
    failures = [r for r in results if not r.passed]
    for r in results:
        mark = "PASS" if r.passed else "FAIL"
        print(f"[{mark}] {r.name}" + ("" if r.passed else f"  ({r.detail})"))
    print(f"\n{len(results) - len(failures)}/{len(results)} passed.")
    if failures:
        print("EVAL GATE: BLOCKED — regression(s) detected.")
        return 1
    print("EVAL GATE: PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
