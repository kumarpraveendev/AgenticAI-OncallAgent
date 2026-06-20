# ADR-0003: Diagnose first, act second — a structural boundary, not a guideline

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering |
| **Tags** | orchestration, safety, react, control-flow |

## Context

The default agent pattern is a single ReAct loop where the model freely interleaves reads and writes: think, observe, act, repeat. For an information task that's fine. For an agent on production it has a quiet failure mode: the autonomy that's completely safe in investigation (read anything, freely) sits in the same loop as the autonomy that is not (act on production). Nothing structural separates "I'm allowed to look at this" from "I'm allowed to do this," so the agent's freedom to investigate can bleed into freedom to act — one prompt away.

## Decision

Split the loop into **two phases with a hard boundary**:

1. **Investigate (read-only, unbounded within a step budget):** the agent proposes only read-only diagnostics. It can think and gather as much as it wants — reads are free and safe. A *write* proposed during this phase is **rejected, not executed** — that's the boundary, enforced in the orchestrator.
2. **Act (gated):** only after investigation does the agent propose remediations, and every one passes the action gate (ADR-0002).

Crossing from knowing to doing is a single, checked transition — not something that can happen incidentally mid-loop.

## Alternatives considered

**Single interleaved ReAct loop.** Rejected — no structural separation between read-autonomy and write-autonomy; the safe freedom and the dangerous one share a code path.

**Prompt-level instruction ("investigate before acting").** Rejected — a guideline the model can ignore is not a boundary. The separation has to be in the orchestrator, not the prompt.

**Human approval before every read.** Rejected — reads are safe and high-volume; gating them buries the human in noise and defeats the toil-reduction purpose.

## Consequences

**Buys us:** investigation autonomy can never become action autonomy by accident. The phase boundary is the single place "the agent is about to do something" is decided.

**Costs us:** more orchestration than a single loop, and a little latency from the explicit transition.

**Risks:** an incident genuinely needs to act, observe, and act again (e.g. mitigate, then verify, then adjust) → the loop can re-enter investigation after an action, but each action still crosses the same gated boundary. The boundary is per-action, not once-per-incident.

## How we operate it

The phase boundary is a tested invariant (ADR-0006): the eval gate fails if any write executes during the investigation phase. The boundary is not a convention engineers remember; it's a check that blocks the merge.

---

**In one line, if I had to defend it to a board:** *Reading production is safe; changing it isn't — so I don't let those two live in the same loop. The agent investigates freely, and there's one hard, checked line it crosses to act. That line can't be blurred by a clever prompt.*
