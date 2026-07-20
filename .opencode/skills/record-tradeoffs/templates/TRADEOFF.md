---
source: deliberate | uncertain | divergence | discovered
severity: critical | high | medium | low
status: captured               # captured → verified → accepted → (resolved|promoted|absorbed|expired)
                               #               ↘ dismissed     ↘ rejected
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: ""                     # Creator agent model name or human
tags: ["tradeoff"]

# ── Creator sections ──

intended_approach: ""          # What should have been done (the correct/optimal approach)
obstacle: ""                   # What prevented the intended approach
obstacle_type: dependency-missing | api-unsupported | permission-denied | env-incompatible
                | context-window | token-budget | time-pressure | missing-info
                | model-limitation | other
actual_approach: ""            # What was implemented instead
gap_assessment: ""             # Functional / performance / security gap between intended and actual

# ── Lifecycle control ──

revisit_by: YYYY-MM-DD         # Latest date to re-evaluate this trade-off
revisit_trigger: ""            # Condition that should trigger revisit (e.g. "Maven restored in CI")

# ── Reviewer sections ──

reviewed_by: ""                # Reviewer agent model name or "human"
review_notes: ""
confidence: high | medium | low  # Reviewer's confidence in obstacle/discovery reality
intended_approach_verified: false  # Reviewer confirms intended_approach is correct

# ── Arbiter sections ──

arbitration:
  type: human | swarm_vote
  vote_details:                # swarm_vote only
    quorum: 0                  # Number of agents participating
    votes: []                  # [{agent, vote, reasoning}]
    result: ""                 # accepted | rejected | tie

# ── Detection (discovered only) ──

detected_by: ""                # Review bot / scanner agent
detected_in: ""                # PR diff location or session reference

# ── Cross-references ──

related:
  tradeoff: []                 # Related/dependent trade-off slugs
  pr: ""                       # PR where trade-off was introduced
  commit: ""                   # Commit hash
  adr: ""                      # If promoted to ADR
  session: ""                  # Agent session record

# ── Resolution (end state only) ──

resolution:
  type: resolved | promoted | absorbed | expired
  resolved_by: ""              # Resolver agent model name or human
  resolved_in: ""              # Commit hash that resolved the trade-off
  target:                      # promoted / absorbed only
    type: adr | prd | agents | rule | spec | rfc | research | aha-moment | other
    path: ""                   # Target file path (e.g. doc/adr/004-reentrantlock-mandatory.md)
    summary: ""                # How the trade-off was absorbed (e.g. "Added to AGENTS.md concurrency section")
---

# [Trade-off Title]

> **Source**: deliberate | uncertain | divergence | discovered
> **Severity**: critical | high | medium | low
> **Status**: captured
> **Revisit by**: YYYY-MM-DD

## 1. What Was Intended

[Describe the correct / optimal approach that should have been taken. Be precise — include API names, patterns, library versions.]

## 2. What Blocked It

[Describe the obstacle in detail. For divergence: include the exact tool error message. For deliberate: explain the constraint. For uncertain: explain what information was missing.]

## 3. What Was Done Instead

[Describe the actual implementation. Include enough detail that a future resolver agent can understand the gap.]

## 4. Gap Assessment

[Functional gap / performance gap / security gap / maintainability gap between intended and actual.]

## 5. Revisit Plan

[When and under what conditions should this trade-off be revisited? Be specific — "when Maven dependency resolution is restored in CI" rather than "when possible".]

## 6. Affected Locations

| File | Line(s) | Annotation | Impact |
|------|---------|-----------|--------|
| [path/to/file] | [lines] | @tradeoff([source]) | [brief description] |

## 7. Review Notes

[Reviewer fills: obstacle verified? severity appropriate? intended_approach correct?]

## 8. Arbitration Decision

[Arbiter fills: accepted / rejected / promoted / absorbed. Rationale. Revisit_by confirmed?]

## 9. Resolution

[Resolver fills: what was changed? Commit hash? Code review passed?]

---

> **For Agents Loading This Record**:
> - If you are a **creator** agent: this is a trade-off to be aware of in this module
> - If you are a **resolver** agent: read Sections 1-3 to understand the gap, Section 5 for the fix
> - If you are a **reviewer** agent: verify Sections 2-4 against session logs and code
> - If you are an **arbiter** agent: evaluate severity + domain overrides
