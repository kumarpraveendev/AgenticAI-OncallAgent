# ADR-0001: Optimize for toil removed — never "percent auto-resolved"

| | |
|---|---|
| **Status** | Accepted |
| **Date** | 2026-06 |
| **Owner** | Praveen Kumar (Head of Engineering, this design) |
| **Deciders** | Engineering, SRE, Leadership |
| **Tags** | metrics, toil, safety, on-call |

## Context

The first metric an on-call agent project reaches for is "percent of incidents auto-resolved," or "MTTR reduction." It makes a clean slide and it is the wrong target. The moment the agent is rewarded for resolving incidents, you have incentivised exactly the two behaviours you least want at 3am on production: acting unilaterally to close an incident, and declaring all-clear early to register a resolution.

An on-call agent's value is not in replacing the human's judgment on risky calls. It's in removing the **toil** — the triage, the context-gathering, the running of known runbooks — so the human arrives at the judgment call already informed. Optimise for resolution count and you trade that real value for a dangerous one.

## Decision

The headline metric is **human-minutes of toil removed, with incident-risk held flat**. "Risk held flat" is concrete and measured: zero unauthorized high-blast actions, no false all-clears, no missed escalations. Reporting is a balanced scorecard — efficiency (toil removed, auto-mitigation rate within policy) alongside safety (unauthorized actions, ungrounded actions — target zero) and accuracy (correct-diagnosis rate, false all-clear rate, missed-escalation rate).

**Guardrail:** toil saved and auto-mitigation rate are never reported without action-safety and false-all-clear beside them. An agent that resolves more incidents but takes one unauthorized action or misses one escalation is a **regression**, not an improvement.

## Alternatives considered

**Percent auto-resolved / MTTR alone.** Rejected — rewards unilateral action and early closure; optimises the metric by raising risk.

**Pure safety (agent only ever reads and suggests).** Rejected — safe and low-value; it leaves the toil on the human, which is the whole problem.

**A single blended "effectiveness" score.** Rejected — collapses the tradeoff a leader needs to see. The point is to watch toil and risk move and decide.

## Consequences

**Buys us:** the agent is pointed at the work that's safe to automate and away from the judgment that isn't. Engineering, SRE, and leadership read the same scorecard.

**Costs us:** no single clean "X% resolved" number; reporting is multi-axis with guardrails, and it requires safety/accuracy instrumentation before the toil-automation, which is the part most projects skip.

**Risks:** toil-saved is harder to measure than resolution count → approximate it with time-on-known-toil-steps removed, and pair it with the safety axis that's hard to game.

## How we operate it

The weekly review reads all axes together. A week with more toil removed but a worse false-all-clear or unauthorized-action count is a failing week, regardless of the efficiency number.

---

**In one line, if I had to defend it to a board:** *If I pay the agent to close incidents, it'll act on its own and call all-clear early — the two things you never want on production. So I measure the toil it took off the human, and I hold it to zero unauthorized actions to earn it.*
