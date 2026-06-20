# evals — evaluation harness

The gate from [ADR-0006](../decisions/0006-evaluation-gate.md), built and running.
New automation ships only through it.

| File | What it is |
|------|------------|
| [`safety_invariants.py`](safety_invariants.py) | Deterministic checks: no write during investigation; only AUTO actions auto-execute; every executed write is grounded; an escalation exists whenever something is pending |
| [`golden_cases.json`](golden_cases.json) | Representative incident scenarios. In production this set grows from replayed real incidents and every near-miss |
| [`golden_runner.py`](golden_runner.py) | Replays each incident through the real orchestrator and exits non-zero on any regression — a CI gate |

The invariants are deliberately deterministic, not model-judged: the failures that
matter most — an unauthorized action, a false all-clear — are exactly the ones you
cannot afford to discover on a live incident, so the checks on them are hard rules,
not a judge model's opinion.

```bash
python -m evals.golden_runner   # PASS/FAIL report, exit 1 on regression
```

This runs in CI on every push (see `.github/workflows/ci.yml`), which makes "new
automation ships only through the eval gate" literally true in this repo.
