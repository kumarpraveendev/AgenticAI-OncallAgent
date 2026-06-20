# ADR-0006: New automation ships only through an incident-replay eval gate

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering, SRE |
| **Tags** | evaluation, safety, ci-cd, replay |

## Context

Every change to this agent is a change to something allowed to touch production: a new runbook, a widened action policy, a tweak to the orchestrator. The failures that matter most — an unauthorized action, a false all-clear, a missed escalation — are exactly the ones you cannot afford to discover on a live incident. "Ship it and watch the dashboards" tests the change on real production during real incidents, which is the one place this class of bug must never first appear.

## Decision

Any change to runbooks, action policy, or the agent passes an **incident-replay eval gate** before it ships. The gate runs the agent against a golden set of incidents — replayed real ones plus synthetic edge cases — and enforces **deterministic safety invariants**: no write executes during the investigation phase; no `FORBIDDEN` or unapproved action is ever auto-executed; no ungrounded action is executed; an escalation exists whenever something is left pending. Golden scenarios additionally check that diagnosis and routing are correct. The gate runs in CI on every push.

## Alternatives considered

**Ship-and-watch in production.** Rejected — surfaces the worst failures on live incidents.

**Manual review only.** Rejected — humans don't reliably catch "this change lets the agent auto-execute a prod restart it shouldn't" by reading a diff. A machine-checked invariant does.

**LLM-as-judge for the gate.** Used above the line for grading diagnosis quality; rejected for the hard safety invariants — "the judge thought the action was fine" is not the assurance I want on whether the agent touched production without approval.

## Consequences

**Buys us:** the catastrophic failures are caught at merge, deterministically, never on a live incident.

**Costs us:** an eval harness and an incident golden set to build and maintain — which is why a named owner holds it.

**Risks:** golden set staleness → it's fed from real incidents and every near-miss, so coverage tracks the production reality.

## How we operate it

The eval gate is wired into CI; a failing safety invariant or a golden regression blocks the merge. Every incident where the agent did something it shouldn't — or should have and didn't — becomes a new golden case the same week.

---

**In one line, if I had to defend it to a board:** *The bugs I most need to catch are the agent acting without approval or calling all-clear wrongly — and those are the ones you can't afford to find on a live incident. So every change replays a set of incidents and has to pass hard safety checks before it ships.*
