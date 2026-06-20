# agentic-oncall

[![ci](https://github.com/kumarpraveendev/agentic-oncall/actions/workflows/ci.yml/badge.svg)](https://github.com/<your-username>/agentic-oncall/actions/workflows/ci.yml)

> A reference design for an AI on-call agent that triages, diagnoses, and mitigates production incidents — written as the decisions a Head of Engineering owns when an agent is allowed to touch production, not a tour of the orchestration.

An on-call agent is the highest-stakes place to put autonomy: it operates during incidents, on production, where a wrong action makes a bad night worse. The cheap way to look good is to maximise the percentage of incidents "auto-resolved." The honest way is harder: take the *toil* off the human — the triage, the context-gathering, the known runbooks — **without taking on the judgment calls that should stay with a person, and without ever raising incident risk to do it.**

This repo is a record of the decisions that hold that line — and the differentiated layer (the gated two-phase orchestrator, the action gate, the grounding check) is built as real, runnable code underneath. If you only read this README, you should understand how I'd let an agent near production safely, not just how the loop is wired.

---

## A note on the numbers

This is a reference design. The figures below (toil reduction, time-to-mitigate, auto-mitigation rate) are **design targets**, not production results.

The judgment behind them is real: I built a LangGraph multi-agent on-call system in production that cut **manual toil roughly 50%** by automating triage, context-gathering, and known-runbook execution — with a human firmly in the loop on anything consequential. Where I draw on that, I say so. The numbers in the sample incident report are illustrative; the operating posture that produces them is not.

---

## The problem, framed as a leader sees it

Three decisions made badly up front turn an on-call agent from an asset into a liability:

1. **They optimize for "auto-resolved."** Reward the agent for closing incidents and you get an agent that acts unilaterally and declares all-clear early — exactly the behaviour you least want at 3am on production.
2. **They let investigation autonomy leak into action autonomy.** An agent that can freely read logs is fine; the moment "reading freely" blurs into "acting freely," you've handed production to a model's confidence.
3. **They let the agent act on its priors.** An ungrounded remediation — "I think restarting will help" — with no runbook behind it is a guess executed against production.

This design treats all three as deliberate decisions. The agent does the toil and stops at the judgment; investigation and action are structurally separated; and no action touches production without a runbook or prior incident behind it.

---

## The decisions

The spine. Each links to a full ADR in [`/decisions`](./decisions); each is a tradeoff I can defend out loud.

### 1. Optimize for toil removed — never "percent auto-resolved"
**Decided:** the headline metric is human-minutes of toil removed *with incident-risk held flat* (zero unauthorized actions, no false all-clears, no missed escalations). **Rejected:** percent auto-resolved / MTTR alone. **Why:** rewarding auto-resolution incentivises an agent to act unilaterally and close early — raising risk to score the metric. **Consequence:** an agent that resolves more incidents but takes one unauthorized action or misses one escalation is a regression. → [ADR-0001](./decisions/0001-incident-scorecard.md)

### 2. Bounded autonomy by blast radius and environment — never by confidence
**Decided:** every action is gated `AUTO` / `REQUIRE_APPROVAL` / `FORBIDDEN` by what it can break and where, not how sure the model is. Read-only diagnostics run free; reversible writes auto-run in staging but need approval in production; irreversible or out-of-mandate actions are blocked. **Rejected:** confidence-thresholded autonomy. **Why:** a confident wrong action on production is the worst case, not the safe one. **Consequence:** the agent is slower on consequential actions, on purpose. → [ADR-0002](./decisions/0002-bounded-autonomy.md)

### 3. Diagnose first, act second — a structural boundary, not a guideline
**Decided:** a two-phase loop — an unbounded read-only **investigation** phase, then a gated **action** phase. The agent can think and gather as much as it wants for free; crossing from knowing to doing is a hard boundary checked every time. A write proposed during investigation is rejected, not executed. **Rejected:** a single ReAct loop where reads and writes interleave freely. **Why:** investigation autonomy must never leak into action autonomy. **Consequence:** more orchestration, slightly more latency — worth it for the boundary. → [ADR-0003](./decisions/0003-diagnose-then-act.md)

### 4. Cite the runbook or don't act
**Decided:** every remediation must reference a runbook step or a prior incident; an ungrounded action is escalated to a human, never auto-executed. **Rejected:** letting the agent act on model priors. **Why:** an ungrounded remediation is a guess run against production. **Consequence:** the agent is only as autonomous as the runbooks are good — which makes runbook coverage a measurable, fixable thing rather than a hidden risk. → [ADR-0004](./decisions/0004-grounded-action.md)

### 5. Escalate with the whole story — never give up or press on silently
**Decided:** on a forbidden action, an approval-needed action, low confidence, or an unknown incident class, the agent hands off to a human with a complete, reconstructable package: timeline, what it checked, what it ruled out, its hypothesis, and what it recommends. **Rejected:** silent failure, or silently pressing on. **Why:** the on-call human should never start from zero, and an agent that quietly continues past its limit is the dangerous one. **Consequence:** building the context package is real work — and it's the work that makes the human handoff fast. → [ADR-0005](./decisions/0005-escalation.md)

### 6. New automation ships only through an incident-replay eval gate
**Decided:** any new runbook, action policy, or agent change is validated against a golden set of replayed and synthetic incidents — correct diagnosis, zero unauthorized actions, escalates when it should — before it ships. Deterministic safety invariants gate it; the eval runs in CI. **Rejected:** ship-and-watch in production. **Why:** the failures you most need to catch (an unauthorized action, a false all-clear) are the ones you cannot afford to discover live. **Consequence:** an eval harness and incident golden set to maintain — the safety system for the safety system. → [ADR-0006](./decisions/0006-evaluation-gate.md)

### 7. Every incident is fully reconstructable
**Decided:** every observation, decision, action, verdict, and approval is logged as a structured, per-incident audit trail. **Rejected:** logs as a side effect. **Why:** on-call runs on blameless postmortems, and you cannot run one on an agent whose actions you can't reconstruct. **Consequence:** logging overhead — and a postmortem artifact that writes itself. → [ADR-0007](./decisions/0007-audit-governance.md)

### 8. Buy the plumbing, build the gated brain
**Decided:** buy alerting, observability, and runbook storage (PagerDuty, Datadog, the LLM gateway, the vector store); build the gated orchestrator, the action policy, and the eval harness — the layer that decides whether an agent touches production. **Rejected:** building the observability stack, or buying an agent that owns the action policy. **Why:** the differentiated, risk-bearing layer is the gate and the loop, not the telemetry. **Consequence:** revisit the boundary as vendors add agentic features. → [ADR-0008](./decisions/0008-build-vs-buy.md)

---

## How I'd staff and operate it

- **The agent is a teammate on the rotation, not a replacement for it.** It takes the first pass — triage, context, known runbooks — and a human owns every consequential call. Framed that way, on-call engineers adopt it; framed as a replacement, they (rightly) distrust it.
- **One engineer owns the runbook and eval golden set** as a standing responsibility, because the agent's autonomy is exactly as good as those two things.
- **The agent has its own on-call posture:** a kill-switch that drops it to read-only-only, and a runbook for when the agent itself misbehaves.
- **The weekly review reads the scorecard, not the auto-resolution rate:** toil saved never appears without action-safety and false-all-clear rate beside it.

---

## What I'd measure

| Axis | Metric | Why it's on the board pack |
|------|--------|----------------------------|
| Efficiency | Human-minutes of toil removed · auto-mitigation rate (within policy) | The value, and the lever |
| Speed | Time-to-mitigation p50 / p95 | The thing on-call actually feels |
| Safety | Unauthorized high-blast actions · ungrounded actions executed | Target zero — the line that can't move |
| Accuracy | Correct-diagnosis rate · false all-clear rate · missed-escalation rate | The failures that hide inside a good toil number |

**Guardrail rule:** toil saved and auto-mitigation rate are never reported without action-safety and false-all-clear beside them.

---

## Architecture (the evidence, briefly)

An incident flows: **investigate (read-only, unbounded) → transition → act (every action gated) → escalate with full context if anything is pending.** Full walkthrough, with a diagram, in [`/docs/architecture.md`](./docs/architecture.md) — linked, not led with.

## Running the reference slice

The differentiated layer is real, runnable code — pure standard library, no API keys.

```bash
pip install -e ".[dev]"
make test   # unit tests
make eval   # the incident-replay eval gate (exits non-zero on regression)
```

The same eval gate runs in CI on every push, which makes "new automation ships only through the eval gate" ([ADR-0006](./decisions/0006-evaluation-gate.md)) true in this repo rather than asserted.

## Repository map

```
.
├── README.md                     ← you are here (the decisions)
├── decisions/                    ← ADRs, one per decision above (0001–0008)
├── artifacts/
│   └── sample-incident-report.md ← the reconstructable incident handling trail
├── docs/
│   └── architecture.md           ← the wiring, as evidence
├── src/                          ← reference implementation (runs, no API keys)
│   ├── incident.py               ← incident / action / observation model
│   ├── action_gate.py            ← AUTO / REQUIRE_APPROVAL / FORBIDDEN, by blast radius + environment
│   ├── runbook.py                ← runbooks + grounding lookup
│   ├── agent.py                  ← agent interface + deterministic runbook agent + env stub
│   └── orchestrator.py           ← the gated two-phase diagnose→act loop + escalation
├── evals/                        ← the eval gate from ADR-0006
│   ├── safety_invariants.py      ← deterministic must-hold checks
│   ├── golden_cases.json         ← seed incident scenarios
│   └── golden_runner.py          ← runs the gate; exit 1 on regression
├── tests/                        ← pytest
└── .github/workflows/ci.yml      ← tests + eval gate on every push
```

---

*Reference design and write-up by Praveen Kumar. The judgment is drawn from production experience building a LangGraph multi-agent on-call system (~50% manual toil reduction); the figures here are design targets, not shipped results.*
