# ADR-0005: Escalate with the whole story — never give up or press on silently

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Tags** | escalation, handoff, on-call, ux |

## Context

An agent reaches its limit several ways: it hits a forbidden action, an action that needs approval, an incident class with no runbook, or its own low confidence. The two failure modes at that moment are equal and opposite — **giving up silently** (the human discovers a stalled incident with no context) and **pressing on silently** (the agent continues past where it should have stopped). Both are dangerous, and the second is worse.

The handoff is where the agent earns trust or loses it. An on-call human paged into an incident should never start from zero; the agent has already done the triage, and that work has to transfer.

## Decision

When the agent reaches any limit, it **stops and escalates with a complete, reconstructable package**: the incident summary, the full timeline of what it checked, what it observed, what it ruled out, its current hypothesis, the specific action(s) it recommends (each with its runbook grounding), and anything it had to block and why. The agent never silently continues past a `REQUIRE_APPROVAL` or `FORBIDDEN` verdict, and never silently abandons an incident.

## Alternatives considered

**Silent failure (just stop).** Rejected — leaves the human a stalled incident and no context; deletes the triage value.

**Silently press on (best-effort).** Rejected — an agent that continues past its limit is the one that takes the action it shouldn't have. This is the failure mode the whole design exists to prevent.

**A terse "escalated, see logs" ping.** Rejected — making the human reconstruct the investigation from raw logs is the toil we were removing, handed back at the worst moment.

## Consequences

**Buys us:** the human handoff is fast — the on-call engineer arrives to a brief, not a blank page. The agent's value survives the boundary instead of evaporating at it.

**Costs us:** assembling the context package is real engineering, and it has to be good enough that a tired human trusts it.

**Risks:** an over-long package is as useless as a terse one → the package leads with hypothesis and recommendation, with the full timeline available beneath.

## How we operate it

The escalation package is the same artifact the postmortem starts from (ADR-0007) — the handoff and the audit trail are one structure, so the work isn't done twice.

---

**In one line, if I had to defend it to a board:** *An agent that quietly gives up wastes the triage; an agent that quietly presses on takes the action it shouldn't. So it does neither — it stops at its limit and hands the human a complete brief, every time.*
