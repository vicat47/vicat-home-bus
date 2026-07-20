---
name: record-adr
description: >-
  Activate when the user asks to create, write, or manage Architecture Decision Records (ADR),
  capture technical decisions, document architecture choices, evaluate alternatives,
  or mentions ADR、架构决策记录、技术决策、架构选择、决策文档、决策域.
category: documentation
tags: ["adr", "architecture", "decision", "documentation", "template", "c4-link", "domain"]
---

# Record ADR — Architecture Decision Records

Create and manage Architecture Decision Records in the `doc/adr/` directory. Each ADR captures a single architectural decision: what was decided, why, and what alternatives were considered.

**Dependencies**: Load `record-c4` (every ADR MUST link to affected C4 elements). Load `doc-structure` for directory infrastructure, progressive indexing, and naming conventions.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language. ADR document content itself should be written in Chinese unless the project convention specifies otherwise.

## What an ADR Is (and Is Not)

An ADR answers four questions: **Context** (what situation triggered the decision), **Decision** (the specific choice), **Alternatives** (what else was considered and why rejected), **Consequences** (trade-offs and risks).

- **IS**: A record of *why* a decision was made
- **IS NOT**: A design document (that describes *how* to implement)
- **IS NOT**: An RFC (RFCs propose; ADRs record concluded decisions)
- **IS NOT**: Meeting notes (ADRs capture outcomes, not discussion processes)

## When to Create an ADR

**CREATE when**: The decision affects system structure; reversal cost is high (>1 sprint); multiple viable options exist with trade-offs; decision crosses team/service boundaries; future engineers may question this choice.

**DO NOT CREATE when**: Following established standards; easily reversible choice; purely cosmetic choice (code style, naming); temporary experiment or prototype.

## ADR Organization — Two Modes

### Mode 1: Flat (no decision domains)

Use when the total ADR count is low and topics are centralized.

```
doc/adr/
├── 001-doris-partition-strategy.md
└── 002-history-table-naming.md
```

### Mode 2: Decision Domains (subdirectory structure)

Create a decision domain subdirectory when a topic accumulates **3+ ADRs** or clearly needs categorization. Domain-internal numbering starts from 001 independently.

```
doc/adr/
├── connector-customization/
│   ├── 001-table-model-override.md
│   └── 002-custom-filter-support.md
└── metadata/
    └── 001-dml-metadata-injection.md
```

**Domain creation commands (execute exactly)**:

```bash
# 1. Create domain directory
mkdir -p doc/adr/<domain-name>/

# 2. Optionally create README in the domain
cp skills/doc-structure/templates/README__TEMPLATE.md doc/adr/<domain-name>/README.md

# 3. Update the main ADR index
# Read doc/adr/README.md, add the new domain to the navigation table
```

**Domain naming**: kebab-case, e.g., `storage-partition`, `metadata-injection`.

## Numbering Rules

- **With domain**: Independent numbering within domain, starting from 001
- **Without domain**: Global numbering in `doc/adr/` root, starting from 001
- **Format**: Three-digit zero-padded (001, 002, ...)
- **Assign next number**: Run `ls doc/adr/<domain>/ 2>/dev/null || ls doc/adr/*.md`, extract highest number, increment by 1

```bash
# Find next ADR number (flat mode)
ls doc/adr/*.md 2>/dev/null | sort -V | tail -1

# Find next ADR number (domain mode)
ls doc/adr/<domain>/*.md 2>/dev/null | sort -V | tail -1
```

## C4 Element Association — MANDATORY

Every ADR MUST link to affected C4 elements. Without this, compliance rules cannot trace their lineage.

In the ADR YAML frontmatter, set `affected_c4_elements` to a list of C4 element names and `related.c4` to the primary C4 document.

In the "Impact" section, describe how the decision affects specific C4 elements and whether C4 documents need updating.

```bash
# Before writing an ADR, find relevant C4 documents
ls doc/c4/*.md | head -20
```

## ADR Lifecycle State Machine

```
                    ┌─────────┐
                    │  draft  │  ← 初稿撰写中
                    └────┬────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
        ┌──────────┐ ┌──────────┐ ┌───────────┐
        │ proposed │ │  draft   │ │ cancelled │  ← 放弃
        └────┬─────┘ └──────────┘ └───────────┘
             │        (退回修改)
        ┌────┼────┐
        ▼         ▼
  ┌──────────┐ ┌───────────┐
  │ accepted │ │ cancelled │  ← 评审驳回
  └────┬─────┘ └───────────┘
       │
  ┌────┼────┐
  ▼         ▼
┌───────────┐ ┌──────────┐
│implemented│ │ cancelled│  ← 实施中放弃
└─────┬─────┘ └──────────┘
      │
  ┌───┼───┐
  ▼       ▼
┌──────────┐ ┌──────────┐
│superseded│ │deprecated│  ← 决策不再适用
└──────────┘ └──────────┘

注: accepted → superseded 也允许（新 ADR 在实施前替代本决策）
```

### State Transition Rules

| From | To | Trigger |
|------|-----|---------|
| `draft` | `proposed` | 提交人工评审 |
| `draft` | `cancelled` | 决策不再相关或用户放弃 |
| `proposed` | `accepted` | 评审通过，决策被批准 |
| `proposed` | `cancelled` | 评审中驳回 |
| `proposed` | `draft` | 评审者要求修改 |
| `accepted` | `implemented` | 决策已实施并验证 |
| `accepted` | `superseded` | 被新 ADR 取代（实施前） |
| `accepted` | `cancelled` | 实施过程中放弃 |
| `implemented` | `superseded` | 被新 ADR 取代 |
| `implemented` | `deprecated` | 技术/方案已不再使用 |

### State Semantics

| 状态 | 含义 | 说明 |
|------|------|------|
| `draft` | 初稿 | 决策已识别，ADR 撰写中 |
| `proposed` | 提案中 | 内容已完成，提交人工评审 |
| `accepted` | 已批准 | 评审通过，决策被批准（尚未实施） |
| `implemented` | 已实施 | 决策已落地并验证 |
| `superseded` | 被取代 | 被更新的 ADR 替代 |
| `deprecated` | 已废弃 | 技术/方案不再使用，无替代 |

**NEVER delete an ADR.** Deprecated/superseded ADRs form the architectural evolution timeline — they explain why past decisions were made and when they changed.

## Smart Loading Strategy

When encountering the `doc/adr/` directory with many ADRs, use triage-first loading to prevent context window bloat:

```
STEP L.1: Read doc/adr/README.md first
STEP L.2: Scan the status column in the index table
STEP L.3: Prioritize loading:
          - proposed (pending review — always load)
          - accepted (approved, awaiting implementation — always load)
          - implemented (active decisions — load recent 3 by date)
STEP L.4: Skip unless explicitly referenced:
          - superseded, deprecated, cancelled (stale)
STEP L.5: If a domain has > 10 ADRs, load only the 5 most recent implemented
```

## Human Review Gate

After generating an ADR (STEP 4), a mandatory human review phase MUST be completed before the ADR status can change from `draft` to `proposed`:

```
REVIEW.1: Present the ADR to the user with a summary of:
          - Decision title and core choice
          - Rejected alternatives and reasons
          - Affected C4 elements
          - Risks and trade-offs

REVIEW.2: Ask user:
          1. 决策是否确认？(Confirm / Revise / Reject)
          2. 需要修改哪些部分？
          3. 是否需要补充其他替代方案？

REVIEW.3: On user confirmation → set status to proposed
REVIEW.4: On user revision request → update ADR, re-present for review
REVIEW.5: On user rejection → set status to cancelled, document reason
```

## Decision Approval & Implementation Gates

After the Human Review Gate (draft → proposed), two additional gates complete the lifecycle:

```
GATE 2 — Decision Approval (proposed → accepted):
  - The decider (frontmatter `decider` field) formally approves the decision
  - Update status to accepted
  - ADR is now ready for implementation

GATE 3 — Implementation Verification (accepted → implemented):
  - All non-cancelled follow-up actions in the ADR are completed
  - The decision has been validated in production (or equivalent)
  - Update status to implemented
```

### Status Migration for Existing ADRs

When adopting this state machine in a project that previously used the 5-state model:

| 旧状态 | 新状态 | 判断条件 |
|--------|--------|----------|
| `accepted` | `implemented` | 决策已落地，follow-up actions 已全部完成 |
| `accepted` | `accepted` | 决策已批准但尚未实施，或 follow-up actions 未完成 |

## Lightweight ADR (LADR) — Quick Decision Capture

For decisions that are important but don't warrant a full ADR, use the LADR format inline:

```
In the context of <situation>,
we decided <decision>, to achieve <goal>,
accepting <trade-offs>.
```

Place LADRs in the same `doc/adr/` directory with standard numbering.

## Common Pitfalls

| Pitfall | Prevention |
|---------|------------|
| Writing ADRs retrospectively | Write during the decision process, not weeks later |
| ADR is too long | >1 page = likely multiple decisions (split) or contains implementation details (move to design doc) |
| Not recording rejected alternatives | This is the most valuable part of an ADR long-term |
| Never reviewing/updating | Schedule quarterly review; mark superseded decisions |

## AI Agent Guardrail Role

AI agents use ADRs to understand:
- **Chosen technologies** → continue using these
- **Rejected alternatives** → do not re-propose them
- **Existing constraints** → compliance/performance thresholds
- **Accepted trade-offs** → eventual consistency, vendor dependencies

Before suggesting ANY technology or architecture change, the agent MUST read relevant ADRs.

## Exact Creation Workflow

Execute these steps in order:

```
STEP 1: IDENTIFY DECISION INFO
  - Extract: decision title, context, constraints from user input
  - Ask user clarifying questions if title/context is ambiguous

STEP 2: GATHER ALTERNATIVES
  - List at least 2 alternatives (more if obvious)
  - For each: pros, cons, rejection/acceptance reason

STEP 3: FIND AFFECTED C4 ELEMENTS (MANDATORY)
  - Run: ls doc/c4/*.md
  - Read relevant C4 files
  - Identify which systems/containers/components are affected

STEP 4: GENERATE ADR DOCUMENT
  - Read template: skills/record-adr/templates/ADR.md
  - Fill in ALL sections, especially:
    - YAML frontmatter fields (status: draft initially)
    - Affected C4 Elements (must contain links)
    - Alternatives (must include rejected options)
    - Impact on C4 Model
  - Read reference example: skills/record-adr/references/example-adr-kafka.md

STEP 4.5: HUMAN REVIEW GATE (MANDATORY)
  - Execute the Human Review Gate procedure documented above
  - ADR status remains draft until user explicitly confirms
  - On confirmation → update status to proposed

STEP 5: NUMBER AND SAVE
  - Determine if domain applies → select flat or domain mode
  - Find next available number:
    ls doc/adr/<domain-or-root>/ | grep -E '^[0-9]{3}-' | sort | tail -1
  - Save to: doc/adr/[<domain>/]NNN-kebab-title.md

STEP 6: UPDATE INDICES
  - Update doc/adr/README.md (add row to navigation table)
  - Update doc/README.md or doc/index.md (increment ADR count)

STEP 7: CROSS-LINK RELATED ADRs
  - Run: grep -l "<keyword>" doc/adr/**/*.md
  - Add "Related Decisions" section if matches found

STEP 8: EVALUATE KEY DECISION STATUS
  - Determine if this ADR qualifies as a "key decision":
    ✓ Affects multiple systems/services/modules
    ✓ Introduces a new core technology
    ✓ Supersedes or reverses a previous decision
    ✓ Has significant performance/cost/security trade-offs
    ✓ Future engineers may question "why this was chosen"
  - If YES → check if doc/key-decisions.md exists:
    ls doc/key-decisions.md 2>/dev/null
  - If not exists → create from template:
    cp skills/record-adr/templates/KEY-DECISIONS.md doc/key-decisions.md
  - If exists → read and update the relevant table:
    - Active Decisions table: add new row with ADR reference
    - Technology Platform table: if ADR involves tech selection, add/update row
  - If NO → skip (no key-decisions update needed)
```

## Decision Log (Optional)

Maintain a running decision log in `doc/adr/README.md`:

```markdown
| # | Date | Decision | Status |
|---|------|----------|--------|
| 23 | 2025-11-15 | Use Kafka for inter-service communication | Accepted |
```

## PR Template Integration

Include an architecture impact checklist in PR templates:

```markdown
## Architecture Impact

- [ ] No architecture change
- [ ] ADR created/updated: [link]
```

## Key Decisions Index Maintenance

The `doc/key-decisions.md` file is a cross-cutting decision index maintained by this skill. It aggregates key decisions from ADRs, tech-radar, and compliance rules.

**Update triggers**:
- New ADR created → evaluate if it's a "key decision" (STEP 8 in creation workflow)
- ADR status changes (Active → Superseded) → update Active Decisions table
- Tech-radar status changes received from `record-tech-radar` → update Technology Platform table

**Template**: `skills/record-adr/templates/KEY-DECISIONS.md`

## Directory Structure

```
skills/record-adr/
├── SKILL.md                        # This file
├── templates/
│   ├── ADR.md                      # ADR standard template
│   └── KEY-DECISIONS.md            # Key-decisions index template
└── references/
    └── example-adr-kafka.md        # Complete example (Kafka selection)
```
