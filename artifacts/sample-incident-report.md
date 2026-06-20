# Sample Incident Report — agentic-oncall

> **Illustrative sample with synthetic data.** It shows the output of the audit
> trail and scorecard described in [ADR-0001](../decisions/0001-incident-scorecard.md)
> and [ADR-0007](../decisions/0007-audit-governance.md): a per-incident handling
> trail that's fully reconstructable, plus the period scorecard that reports toil
> saved *with* safety beside it. Every figure is fabricated; the operating posture
> reflects production experience, not this design.

This artifact answers the two questions an engineering panel and an SRE lead ask:
1. *For this incident, what did the agent see, decide, and do — and what did it leave to a human?* (Part A)
2. *Across the period, did the agent save toil without raising incident risk?* (Part B)

---

## Part A — Single incident trail

**Incident:** `INC-2026-0612-0441` (synthetic) · **SEV1** · **prod** · checkout service
**Signal:** `high_error_rate` · **Detected:** 2026-06-12 02:14:09 CET

### Phase 1 — Investigate (read-only, auto)

| Time | Action | Verdict | Finding |
|------|--------|---------|---------|
| 02:14:11 | `read_logs` | AUTO | 5xx rate 18%, errors trace to `checkout-svc` v412 |
| 02:14:13 | `check_deploy_status` | AUTO | v412 deployed 02:09, 5 min before alert |

**Hypothesis (grounded in RB-003):** error spike correlates with deploy v412; recommended remediation is a rollback.

### Phase 2 — Act (gated)

| Time | Proposed action | Verdict | Outcome |
|------|-----------------|---------|---------|
| 02:14:15 | `rollback_deploy` → checkout-svc (grounded in RB-003) | **REQUIRE_APPROVAL** | not executed — reversible write on production needs a human ([ADR-0002](../decisions/0002-bounded-autonomy.md)) |

### Escalation package handed to on-call (02:14:16)

- **Summary:** SEV1, prod — elevated 5xx on checkout, onset 02:14, correlated with deploy v412.
- **Ruled out:** dependency latency (metrics nominal), infra (no node events).
- **Hypothesis:** bad deploy v412.
- **Recommended:** `rollback_deploy` → checkout-svc, grounded in RB-003. One approval click.
- **Blocked:** none.

**Human approved the rollback at 02:15:40. Mitigated 02:16:55.**

> The agent did the toil — triage, correlation, the runbook lookup — in **7 seconds**,
> and stopped exactly at the production change. The human arrived to a one-line
> decision, not a blank page. Time-to-mitigate: **2m 46s**; human-attention time:
> **~75s** of approving, not investigating.

---

## Part B — Period scorecard

**Period:** 2026-06-08 → 2026-06-14 (synthetic) · **Incidents handled:** 412

### The headline, reported honestly

| Axis | Metric | Value | Guardrail |
|------|--------|-------|-----------|
| Efficiency | Human-minutes of toil removed | **~5,900 min** | — |
| Efficiency | Auto-mitigated within policy | 41% | — |
| Efficiency | First-pass triage handled by agent | 96% | — |
| Speed | Time-to-mitigation p50 / p95 | 3.1m / 14.2m | — |
| Safety | Unauthorized high-blast actions | **0** | ✅ must be 0 |
| Safety | Ungrounded actions executed | **0** | ✅ must be 0 |
| Accuracy | Correct-diagnosis rate | 94.1% | — |
| Accuracy | False all-clear rate | **0.0%** | ✅ |
| Accuracy | Missed-escalation rate | **0.0%** | ✅ |

> **Guardrail note:** auto-mitigation rate rose 6 points this period (a low-blast
> action was cleared for prod auto-execution, via the eval gate). The safety axis
> held at zero and false-all-clear held at 0.0%, so it's a genuine gain. **Had a
> single unauthorized action or false all-clear appeared, this reads FAIL regardless
> of the toil number** — the point of [ADR-0001](../decisions/0001-incident-scorecard.md).

### Where the agent stopped (escalation reasons)

| Reason | Count | Note |
|--------|-------|------|
| Prod write needs approval | 121 | Working as designed — human owns the prod change |
| No runbook for incident class | 38 | The runbook backlog, ranked ([ADR-0004](../decisions/0004-grounded-action.md)) |
| Out-of-mandate action blocked | 2 | Runbook proposed something forbidden; flagged for review |
| Low confidence / inconclusive | 17 | Handed off with full context |

### Governance

- Agent changes shipped this period: 2. **Eval-gate blocks: 1** (a policy change would have let a prod restart auto-execute; never reached production — [ADR-0006](../decisions/0006-evaluation-gate.md)).
- Every incident above has a complete, reconstructable audit trail ([ADR-0007](../decisions/0007-audit-governance.md)).

---

## How to read this report

- **Part A** is the postmortem/handoff view: pick any incident, see exactly what the agent saw, decided, and did, and where it stopped.
- **Part B** is the leadership view: did toil fall *with safety and accuracy holding*?

Together they turn "the agent saved us time" into evidence — and they make a toil
win that hides an unauthorized action or a false all-clear impossible to report as
a success.

---

*Sample artifact for a reference design by Praveen Kumar. Synthetic data throughout; the toil-reduction posture reflects a production system, not this reference implementation.*
