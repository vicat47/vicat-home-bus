---
status: draft              # draft | proposed | accepted | implemented | superseded | deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: ""
decider: ""                # Person/team who made the decision
tags: ["adr"]
affected_c4_elements: []   # C4 element names this ADR affects
related:
  adr: ""
  c4: ""
  research: ""
  radar: ""
---

# ADR-[NNN]: [Decision Title]

> **When to write an ADR:**
> - Decision affects system structure or architecture boundaries
> - Reversal cost is high (exceeds one sprint)
> - Multiple viable options exist with trade-offs to document
> - Decision crosses team or service boundaries
> - Future you may question this choice
>
> **When NOT to write an ADR:**
> - Following established team standards or conventions
> - Decision is easily reversible with minimal impact
> - Purely cosmetic choice (code style, naming conventions)
> - Temporary experiment or prototype validation

## Context
[Describe the situation, constraints, and influencing factors. What problem or opportunity triggered this decision?]

## Decision
[State the decision clearly and concisely in active voice. One sentence summarizing the core decision.]

## Decision Drivers
- [Driver 1]: [description]
- [Driver 2]: [description]

## Considered Options
### Option 1: [Name]
**Pros:**
- ...
**Cons:**
- ...
**Rejection/Acceptance Reason:** ...

### Option 2: [Name]
**Pros:**
- ...
**Cons:**
- ...
**Rejection/Acceptance Reason:** ...

> **Common Pitfall Warnings:**
> - Do NOT write ADR retrospectively — write during the decision process, not weeks later
> - Do NOT make it too long — over one page means multiple decisions (split) or implementation details (move to design doc)
> - MUST record rejected alternatives — this is the most valuable part of an ADR long-term
> - Schedule quarterly review — mark superseded decisions, keep documentation current

## Impact
### Positive Impact
- ...
### Negative Impact / Risks
- ...
### Impact on C4 Model
- [Describe how this decision affects C4 elements and whether C4 documents need updating]

## Related Decisions
- [ADR-XXX](link) — [brief description of relationship]

## Follow-up Actions
- [ ] [Action item 1]
- [ ] [Action item 2]
- [ ] Update related C4 documents (if applicable)
