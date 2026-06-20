# ADR-0008: Buy the plumbing, build the gated brain

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering, Finance |
| **Tags** | build-vs-buy, strategy, lock-in |

## Context

The on-call ecosystem is mature: alerting (PagerDuty/Opsgenie), observability (Datadog/Grafana), runbook and knowledge storage, the LLM gateway, the vector store. The reflex to build it all proves capability while reinventing solved problems; the reflex to buy an end-to-end "AI SRE" quietly outsources the one layer that decides whether an agent is allowed to change production. The leadership call is to draw the line at the risk.

## Decision

**Buy the plumbing** — alerting, observability, runbook/knowledge storage, the LLM gateway, the vector store. **Build the gated orchestrator, the action policy, and the eval harness** — the two-phase loop, the `AUTO/REQUIRE_APPROVAL/FORBIDDEN` gate, the grounding check, the safety invariants. That layer encodes *this* organisation's risk appetite about what an agent may do to production; it is the differentiated, risk-bearing part, so it is ours and kept **portable** above the vendor tools.

## Alternatives considered

**Build the observability/alerting stack.** Rejected — reinventing mature, well-run vendor products while the risk-bearing policy work waits.

**Buy an end-to-end agentic SRE product.** Rejected as the default — convenient, but it owns the action policy and the gate, which is precisely the layer that is our risk and our responsibility. The decision about what an agent may do to our production is not one to outsource to a vendor's defaults.

## Consequences

**Buys us:** fast to value on the commodity layers, effort concentrated on the gate and the loop, and freedom to swap vendors.

**Costs us:** an integration boundary, and one that moves as vendors ship their own agentic features.

**Risks:** a vendor's agent features tempt us to lean on them and cede the policy → keep the gate and orchestrator above the vendor tools and vendor-agnostic by rule.

## How we operate it

The boundary is revisited quarterly. The gate, the orchestrator, and the eval layer stay portable, so the question "could a vendor own this now?" can be re-answered without a rewrite — and the answer for the layer that touches production stays "no, we own that."

---

**In one line, if I had to defend it to a board:** *I'd buy the alerting and the dashboards and build the part that decides whether an agent is allowed to change production. That decision is our risk to own — handing it to a vendor's defaults is the one thing I won't do.*
