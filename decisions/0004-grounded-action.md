# ADR-0004: Cite the runbook or don't act

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering, SRE |
| **Tags** | grounding, runbooks, safety, rag |

## Context

An agent that remediates on its model priors — "I think restarting this will help" — is running a guess against production. The fix for hallucinated *answers* in a support agent is grounding; the fix for hallucinated *actions* in an on-call agent is the same, and the stakes are higher because the output isn't a sentence, it's a change to a live system.

## Decision

**Every remediation must be grounded** in a runbook step or a prior incident: the action carries the identifier of the step or incident it's based on. An **ungrounded action is never auto-executed** — it's escalated to a human, who can choose to authorize it. The agent's autonomy is bounded by the documented operational knowledge, not by what the model can invent.

## Alternatives considered

**Let the agent act on model priors.** Rejected — an ungrounded remediation is a guess executed against a live system; the failure mode is a confident, wrong, autonomous action.

**Require grounding for reads too.** Rejected — reads are safe and exploratory; demanding a runbook citation to *look* defeats investigation. Grounding is a gate on *acting*, not on knowing.

**Free-text "reasoning" as grounding.** Rejected — a model explaining itself is not the same as a reference to vetted operational knowledge. Grounding has to point at something a human wrote and trusts.

## Consequences

**Buys us:** the agent can only auto-act within the operational knowledge the team has vetted. An ungrounded action surfaces as an escalation, not as a silent production change.

**Costs us:** the agent is exactly as autonomous as the runbooks are good — thin runbook coverage means more escalations.

**Risks:** that coverage gap could read as a limitation. It's the opposite — it makes autonomy a **measurable, fixable** function of runbook quality, instead of a hidden risk. Escalation-due-to-no-runbook is a metric that tells you precisely which runbook to write next.

## How we operate it

"Escalated: no runbook" is tracked as a first-class reason. It's not a failure — it's the backlog of runbooks worth writing, ranked by how often the agent hit the gap.

---

**In one line, if I had to defend it to a board:** *The agent doesn't get to act on a hunch against production. Every change it makes points back to a runbook a human wrote — and when there's no runbook, it escalates instead of guessing. Its autonomy is capped by our documented knowledge, on purpose.*
