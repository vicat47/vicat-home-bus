---
name: record-compliance
description: >-
  Activate when the user asks to create compliance rules, architecture constraints, coding guardrails,
  or mentions 合规规则、架构约束、编码前检查、层边界、技术约束.
category: documentation
tags: ["compliance", "rules", "guardrails", "constraints", "validation", "architecture-lint"]
---

# Record Compliance — Architecture Guardrails

Compliance rules are deterministic checks (no AI involved in enforcement) that validate code changes against architecture decisions — an architecture-level ESLint. Every rule MUST trace back to an ADR or C4 element.

**Dependencies**: Load `record-adr` and `record-c4` (every compliance rule must derive from an ADR or C4 element). Load `doc-structure` for directory infrastructure.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

## Init Workflow — Initialize Compliance Rules Directory

When the user asks to "初始化合规规则" or "init compliance rules", execute this workflow. This workflow **depends on `doc-structure`** for directory infrastructure and then collects compliance-specific context.

```
STEP 1: DELEGATE DIRECTORY SETUP TO doc-structure
  - Load doc-structure skill
  - Run doc-structure creation workflow:
      mkdir -p doc/compliance-rules/
      cp skills/doc-structure/templates/README__TEMPLATE.md doc/compliance-rules/README.md
      cp skills/doc-structure/templates/AGENTS__TEMPLATE.md doc/compliance-rules/AGENTS.md
  - Copy the compliance rule template:
      cp skills/record-compliance/templates/COMPLIANCE-RULE.md doc/compliance-rules/_TEMPLATE.md

STEP 2: COLLECT COMPLIANCE-SPECIFIC CONTEXT
  Gather existing architecture context to populate traceability references:
  - List available ADRs: ls doc/adr/ 2>/dev/null
  - List available C4 containers: ls doc/c4/ 2>/dev/null
  - Read existing architecture constraints from codebase if any (e.g., .eslintrc, archlint.yml, package.json dependencies)

STEP 3: CUSTOMIZE README.md FOR COMPLIANCE CONTEXT
  Edit doc/compliance-rules/README.md:
  - Replace placeholder description with compliance-specific scope
  - Add "Related Architecture Documents" section:
    - List discovered ADRs with links (from STEP 2)
    - List discovered C4 containers with links (from STEP 2)
  - Ensure navigation table includes severity level column
  - Add link to _TEMPLATE.md

STEP 4: CUSTOMIZE AGENTS.md FOR COMPLIANCE CONTEXT
  Edit doc/compliance-rules/AGENTS.md (created from doc-structure template):
  - Update "When to Create Documents":
    - Add triggers: ADR introduces constraint, C4 defines boundary, recurring violation pattern
    - Add exclusions: cannot trace to ADR/C4, purely stylistic rules
  - Update "Regression Checks":
    - Add ADR traceability check: grep -rli "<keyword>" doc/adr/
    - Add C4 traceability check: grep -rli "<keyword>" doc/c4/
    - Add duplicate rule check
  - Replace Core Principles table with compliance-specific DO/DON'T:
    - DO: trace to ADR, trace to C4, be specific, provide examples
    - DON'T: orphan rules, vague conditions, duplicates, stylistic-only rules
  - Replace Template Structure with compliance rule template skeleton (from COMPLIANCE-RULE.md)
  - Add "7 Rule Types" reference table
  - Update File Naming Convention to: [category-]kebab-rule.md

STEP 5: UPDATE PARENT INDICES
  - If doc/README.md exists → add compliance-rules entry
  - Run doc-structure index update if available

STEP 6: VERIFY
  - Confirm doc/compliance-rules/ contains: README.md, AGENTS.md, _TEMPLATE.md
  - Confirm README.md lists available ADRs and C4 containers for traceability
  - Confirm AGENTS.md includes compliance-specific regression checks
```

## Compliance Rule Lifecycle State Machine

```
                  ┌─────────┐
                  │  draft  │  ← Rule being authored
                  └────┬────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
        ┌──────────┐ ┌──────┐ ┌───────────┐
        │  active  │ │ draft│ │ cancelled │  ← Abandoned
        └────┬─────┘ └──────┘ └───────────┘
             │        (revision)
        ┌────┼────┐
        ▼         ▼
  ┌──────────┐ ┌───────────┐
  │ revoked  │ │ deprecated│  ← ADR superseded / C4 changed
  └──────────┘ └───────────┘
```

### State Transition Rules

| From | To | Trigger |
|------|-----|---------|
| `draft` | `active` | Human review approves the rule |
| `draft` | `cancelled` | Rule no longer needed or user abandons |
| `active` | `deprecated` | Underlying ADR is superseded or C4 element changes |
| `active` | `draft` | Rule needs revision |
| `active` | `revoked` | Rule found to be incorrect or overly restrictive |

## Smart Loading Strategy

Use triage-first loading instead of loading all compliance rules. The old pattern of loading ALL files is FORBIDDEN.

```
STEP L.1: Read doc/compliance-rules/README.md first
STEP L.2: Scan the status column — identify active rules
STEP L.3: Load ONLY:
          - Rules with status: active (always)
          - Rules whose scope (container/language) matches the current task
STEP L.4: Skip: deprecated, draft, cancelled rules unless explicitly referenced
STEP L.5: If > 10 active rules, load only the 5 most recently updated
```

## Agent Pre-Code Checklist — MANDATORY

Before writing ANY code, the agent MUST execute these steps:

```
STEP 0.1: Read doc/compliance-rules/README.md first (triage by status)

STEP 0.2: Identify which rules apply to the current task
  - Match by: scope.containers, scope.languages
  - Only consider rules with status: active

STEP 0.3: Print applicable rules to the user as a checklist
  Output: "The following compliance rules apply to this change:"
  - [RULE-001] naming-convention-api-endpoints.md (Critical)
  - [RULE-003] layer-boundary-ui-repository.md (Blocker)

STEP 0.4: If a rule would be violated, STOP and ask user for override approval
  DO NOT silently bypass compliance rules.
```

## 7 Rule Types

| Rule Type | What It Enforces | Example |
|-----------|-----------------|---------|
| **Required Pattern** | Patterns that must or must not exist in code | "All DB queries must use parameterized queries" |
| **Naming Convention** | File, type, function naming standards | "API endpoints must use kebab-case" |
| **Technology Constraint** | Lock tech stack by container | "Order service can only use PostgreSQL" |
| **Layer Boundary** | Import relationships between layers | "UI layer must not import Repository layer directly" |
| **Contract Compliance** | Code endpoints match API contracts | "All /api/v2/* endpoints must have OpenAPI docs" |
| **Dependency Rule** | Every import must have a documented C4 relationship | "No unapproved external dependencies" |
| **Event Channel** | Producers/consumers match declared channels | "Order events must publish to `orders` topic" |

## Trade-Off Arbitration Domain Override Rules

These rules are consumed by `record-tradeoffs` during the arbitration phase. When a trade-off falls into one of the following domains, the default swarm voting mechanism is bypassed and the decision is escalated to a human Arbiter.

| Domain | Override | Rationale |
|--------|----------|-----------|
| **Security** | Swarm vote bypassed → human Arbiter mandatory | Security compromises cannot be auto-accepted regardless of vote outcome. A human must explicitly sign off. |
| **Data Integrity** | Swarm vote bypassed → human Arbiter mandatory | Data correctness trade-offs carry irreversible risk. Corrupted or lost data may not be recoverable. |
| **Compliance / Regulatory** | Swarm vote bypassed → human Arbiter mandatory | Regulatory violations cannot be delegated to agent voting. Legal and compliance risk requires human accountability. |
| **Any `severity: critical`** | Swarm vote SKIPPED → immediate human escalation | Critical severity implies the trade-off should not exist as a deferrable item. Must be addressed before any deployment. |

### How `record-tradeoffs` Consumes These Rules

1. Before arbitration, `record-tradeoffs` SHOULD query `record-compliance` for active domain override rules
2. If the trade-off's `tags` or `obstacle_type` matches any override domain → bypass swarm voting
3. Escalate to human Arbiter with: trade-off summary + domain match + override note
4. Human MUST explicitly confirm before status changes to `accepted`

### Creating a Compliance Rule from Trade-Off Override Logic

When a trade-off is resolved and the lesson is absorbed into `record-compliance` as a formal rule:

```
Rule template fields:
  Associated ADR: ADR-003 (record-tradeoffs design decision)
  Associated C4 Container: N/A (this is process-level, not container-level)
  Rule condition: "Any trade-off tagged with [security|data-integrity|compliance]
    MUST NOT be auto-accepted by agent swarm voting."
  Severity: Blocker
  Enforcement: PR review bot checks. See record-tradeoffs §6.3.
```

## Rule-to-ADR/C4 Traceability — MANDATORY

Every compliance rule MUST trace to one or more ADRs or C4 elements. Rules cannot be created from thin air — they derive from architecture decisions or models.

In the rule template, fill in:
- `Associated ADR`: Link to the ADR that justifies this rule
- `Associated C4 Container`: Link to the C4 element whose boundary this rule protects

```bash
# When creating a new rule, find relevant ADRs and C4 files:
grep -rl "<keyword>" doc/adr/ doc/c4/
```

## Exact Creation Workflow

```
STEP 1: IDENTIFY RULE SOURCE
  - Which ADR or C4 element drives this rule?
  - Run: grep -rl "<related term>" doc/adr/ doc/c4/
  - Read the ADR/C4 source to extract the constraint

STEP 2: DETERMINE RULE TYPE
  - Match the constraint to one of the 7 rule types above
  - Use the most specific type that applies (e.g., "Layer Boundary" is more specific than "Required Pattern")

STEP 3: GENERATE RULE DOCUMENT
  - Read: skills/record-compliance/templates/COMPLIANCE-RULE.md
  - Fill in:
    - Associated ADR field (mandatory, with link)
    - Associated C4 Container field (mandatory, with link)
    - Rule condition (use natural language or pseudo-code)
    - Violation example (code snippet showing the break)
    - Compliance example (code snippet showing correct usage)

STEP 4: SET SEVERITY
  - Blocker: merge is blocked
  - Critical: requires explicit approval to bypass
  - Warning: advisory, can be bypassed with documentation
  - Info: informational only

STEP 5: NAME AND SAVE
  - Format: <category>-kebab-rule.md (category prefix MANDATORY)
  - Valid categories: naming-convention, technology-constraint, layer-boundary,
              contract-compliance, dependency-rule, event-channel, required-pattern
  - Example: naming-convention-api-endpoints.md
  - Save to: doc/compliance-rules/<filename>

STEP 6: HUMAN REVIEW GATE (MANDATORY)
  - Present the rule to the user with:
    - Rule name, type, severity
    - Associated ADR and C4 element
    - Rule condition, violation/compliance examples
    - Enforcement method and failure behavior
  - Ask user:
    1. 规则是否确认？(Confirm / Revise / Reject)
    2. 严重级别是否合适？
    3. 是否需要补充例外情况？
  - On confirmation → update status: active
  - On revision → update status: draft, return to STEP 3
  - On rejection → update status: cancelled, document reason

STEP 7: UPDATE INDICES
  - Update doc/compliance-rules/README.md
  - Update doc/README.md or doc/index.md
```

## Enforcement Methods

| Check Timing | Tool | Failure Behavior |
|-------------|------|-----------------|
| PR Review | Automated agent | Warning, requires approval |
| CI Pipeline | Custom script | Block merge |
| Pre-commit hook | ESLint-like tool | Block commit |
| Preflight check | AI agent (this skill) | Revise plan before coding |

## Naming Convention

```
<category>-kebab-rule.md
```

Category prefix is MANDATORY. Valid categories: `naming-convention`, `technology-constraint`, `layer-boundary`, `contract-compliance`, `dependency-rule`, `event-channel`, `required-pattern`.

Examples: `naming-convention-api-endpoints.md`, `technology-constraint-database.md`, `layer-boundary-ui-repository.md`.

```bash
# All compliance rule files include a category prefix:
ls doc/compliance-rules/*.md | grep -v README | grep -v AGENTS | grep -v _TEMPLATE
# Expected: all filenames match <category>-<name>.md
```

## Directory Structure

```
skills/record-compliance/
├── SKILL.md                     # This file
└── templates/
    └── COMPLIANCE-RULE.md       # Rule template (markdown + YAML)
```
