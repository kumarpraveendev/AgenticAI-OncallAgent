# ADR-0002: Bounded autonomy by blast radius and environment — never by confidence

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering, SRE |
| **Tags** | autonomy, safety, gating, production |

## Context

The seductive design is to gate the agent's actions on confidence: act when sure, ask when not. It is exactly backwards for production. A confidently wrong action — restart the wrong service, scale the wrong tier, roll back a good deploy — is the worst outcome, and confidence is precisely the signal that fails silently when the model is wrong. Autonomy on production has to be bounded by what an action can break, not by how the model feels about it.

There is also an axis a support agent doesn't have: **environment**. The same action — restart a service — is routine in staging and consequential in production. The gate has to know where it is.

## Decision

Every proposed action is classified by a gate into **`AUTO` / `REQUIRE_APPROVAL` / `FORBIDDEN`**, keyed on blast radius and environment — never on confidence:

- **Read-only diagnostics** (logs, metrics, traces, status) → `AUTO`, always.
- **Reversible writes** → `AUTO` in staging; `REQUIRE_APPROVAL` in production (a human's name goes on a production change), except a small set of low-blast, grounded actions explicitly cleared for prod auto-execution.
- **Irreversible actions** → `REQUIRE_APPROVAL`.
- **Out-of-mandate actions** (delete data, modify IAM, disable security controls, scale to zero) → `FORBIDDEN`, regardless of grounding or confidence.

The model's confidence is recorded for the audit trail and **never read by the gate**.

## Alternatives considered

**Confidence-thresholded autonomy.** Rejected — gates on the signal that fails silently; a confident wrong action is the worst case.

**A single global "ask before any write" rule.** Rejected — too blunt; it leaves obvious staging toil on the human and ignores that some prod actions are genuinely low-blast.

**Full autonomy with a rollback.** Rejected — "we can undo it" is not true of every action, and the incident is the worst time to discover which.

## Consequences

**Buys us:** the agent is autonomous exactly where autonomy is cheap and supervised exactly where it's expensive. The boundary is legible — anyone can read which actions auto-run where.

**Costs us:** the agent is slower on consequential actions, by design, and the policy table is a thing to maintain as the action set grows.

**Risks:** a new action type slips in unclassified → unknown actions default to `REQUIRE_APPROVAL`, never `AUTO`. The agent never silently grants itself a new power.

## How we operate it

The action policy is reviewed like any production-access policy. Adding an action to the prod-auto-execute set is an explicit, evidence-backed decision (it passes the eval gate, ADR-0006), not a quiet config change.

---

**In one line, if I had to defend it to a board:** *The agent's permission to touch production depends on what the action can break and where — not on how confident it is. A confident wrong action is the worst thing that can happen on a bad night, so confidence buys it nothing.*
