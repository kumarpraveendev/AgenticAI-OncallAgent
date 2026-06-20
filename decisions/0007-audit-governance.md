# ADR-0007: Every incident is fully reconstructable

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering, SRE, Compliance |
| **Tags** | audit, governance, postmortem, observability |

## Context

On-call runs on blameless postmortems: when something goes wrong, you reconstruct exactly what happened, learn, and move on without blame. An agent in the loop breaks that the moment its actions aren't reconstructable — you cannot run a blameless postmortem on a black box, and "the agent did something" with no trail is the fastest way to lose the team's trust in it. There's also a hard requirement: an autonomous actor on production needs an audit trail for the same reasons any privileged access does.

## Decision

Every step is logged as a **structured, per-incident audit trail**: each observation, each decision, each proposed action with its verdict and grounding, each execution, each approval, each escalation — timestamped and attributable. The trail is complete enough to answer, for any incident, "what did the agent see, decide, and do, and why" without guesswork.

## Alternatives considered

**Logging as a side effect (whatever the framework emits).** Rejected — incidental logs don't reliably answer the postmortem question; the audit trail is a designed output, not exhaust.

**Log actions only, not reasoning/observations.** Rejected — "what it did" without "what it saw and decided" can't support a blameless review or explain a wrong action.

## Consequences

**Buys us:** any incident is fully reconstructable; the postmortem starts from a complete trail instead of a reconstruction. The same structure is the escalation package (ADR-0005), so it serves the live handoff and the retrospective both.

**Costs us:** logging overhead and a schema to maintain.

**Risks:** sensitive data in logs → the trail records action types, targets, verdicts, and grounding references, not raw payloads, and follows the same data-handling rules as any production log.

## How we operate it

The audit trail is the artifact a postmortem opens with. An agent action that can't be explained from the trail is treated as a defect in the trail, not an acceptable gap.

---

**In one line, if I had to defend it to a board:** *You can't run a blameless postmortem on a black box. Every incident the agent touches is fully reconstructable — what it saw, what it decided, what it did, and why — which is what lets the team trust an autonomous actor on production at all.*
