# src — reference implementation

The differentiated layer from the decision record, as real runnable code
([ADR-0008](../decisions/0008-build-vs-buy.md) is the argument for owning exactly
this much and buying the plumbing). Pure standard library — no API keys, no network.

| File | What it is | Decision |
|------|------------|----------|
| [`incident.py`](incident.py) | Incident / action / observation model + environment + phases | — |
| [`action_gate.py`](action_gate.py) | AUTO / REQUIRE_APPROVAL / FORBIDDEN by blast radius + environment | [ADR-0002](../decisions/0002-bounded-autonomy.md) |
| [`runbook.py`](runbook.py) | Runbooks + grounding lookup | [ADR-0004](../decisions/0004-grounded-action.md) |
| [`agent.py`](agent.py) | Agent interface + deterministic runbook agent + env stub | — |
| [`orchestrator.py`](orchestrator.py) | The gated two-phase diagnose→act loop + escalation | [ADR-0003](../decisions/0003-diagnose-then-act.md), [ADR-0005](../decisions/0005-escalation.md) |

Two lines carry most of the weight:

1. In `orchestrator.run`, a write proposed during the **investigation phase is
   rejected, never executed** — the read/write boundary of ADR-0003, with a test
   that fails if it ever leaks.
2. In `action_gate.classify`, `action.confidence` is recorded but **never read** —
   the verdict is blast radius and environment, not confidence (ADR-0002), again
   with a test enforcing it.

```bash
pip install -e ".[dev]"   # from the repo root
make test                 # unit tests
make eval                 # the incident-replay eval gate
```

The agent here is a deterministic runbook follower so the system runs with no model
call; a real LLM agent implements the same `investigate` / `remediate` interface.
The orchestration — the gate, the phase boundary, the escalation — is the real,
differentiated logic and is fully exercised either way.
