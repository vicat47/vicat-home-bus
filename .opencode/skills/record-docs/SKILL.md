---
name: record-docs
description: >-
  Activate when the user asks to create specs, RFCs, PRDs, design docs, retrospectives, meeting notes,
  or agent session records. Covers 通用文档类型：规格说明、RFC 提案、产品需求、设计文档、迭代回顾、会议记录、Agent 工作记录.
category: documentation
tags: ["docs", "specs", "rfc", "prd", "design", "retrospective", "meeting-notes", "agent-sessions"]
---

# Record Docs — Common Documentation Assets

Create 7 types of common documentation assets in the `doc/` directory. These are "write-from-template" document types with straightforward creation workflows.

**Dependencies**: Load `doc-structure` for directory infrastructure, progressive indexing, and naming conventions.

**Cross-reference**: `record-adr` — RFCs that are implemented may produce ADRs. `record-c4` — specs and RFCs may reference C4 models. `drawio` — UI/UX design docs may reference .drawio diagrams.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

## Document Type Routing Table

| User asks to create... | Type | Destination | Template |
|------------------------|------|-------------|----------|
| Spec, technical spec, functional spec, module spec | Spec | `doc/specs/` | `templates/SPEC.md` |
| RFC, proposal, major change proposal | RFC | `doc/rfcs/` | `templates/RFC.md` |
| PRD, product requirement, feature requirement, 产品需求 | PRD | `doc/prd/` | `templates/PRD.md` |
| Design doc, UI design, UX design, architecture design | Design Doc | `doc/design/` | *(links to external design tool output; optionally use drawio for diagrams)* |
| Retrospective, retro, post-mortem, sprint review | Retrospective | `doc/retrospectives/` | `templates/RETROSPECTIVE.md` |
| Meeting notes, meeting minutes, 会议纪要 | Meeting Notes | `doc/meeting-notes/` | `templates/MEETING-NOTES.md` |
| Agent session, agent log, session record, 工作记录 | Agent Session | `doc/agent-sessions/` | `templates/AGENT-SESSION.md` |
| Glossary, terminology, term definition, abbreviation, 术语表、术语定义、缩写、专用词汇 | Glossary | `doc/glossary.md` (固定文件) | `templates/GLOSSARY.md` |

## Naming Rules by Type

### Numbered: RFCs
Use three-digit zero-padded numbering (001, 002, ...).

```bash
# Find next RFC number
ls doc/rfcs/*.md 2>/dev/null | grep -E '/[0-9]{3}-' | sort -V | tail -1
```

```
doc/rfcs/
├── 001-migrate-to-grpc.md
└── 002-event-sourcing-poc.md
```

### Date-based: Retrospectives, Meeting Notes, Agent Sessions

Use the current session date. Format: `YYYYMMDD-<topic>.md`

```bash
# Use today's date
date +%Y%m%d
```

```
doc/retrospectives/20260518-sprint-3-retro.md
doc/meeting-notes/20260518-cdc-pipeline-review.md
doc/agent-sessions/20260518-flink-cdc-wildcard-verify.md
```

### Module/Feature-based: Specs, PRD, Design Docs

Use the module name or feature name in kebab-case.

```
doc/specs/payment-service.md
doc/prd/user-dashboard.md
doc/design/checkout-flow.md
```

## Exact Creation Workflow — Per Type

### Workflow A: RFC (numbered type)

```
STEP A1: REGRESSION CHECK
  - Run: ls doc/rfcs/*.md
  - Read titles of existing RFCs: grep "^# RFC-" doc/rfcs/*.md
  - If similar topic exists → update existing, don't create duplicate

STEP A2: FIND NEXT NUMBER
  - Run: ls doc/rfcs/ | grep -E '^[0-9]{3}-' | sort | tail -1
  - Extract number, increment, zero-pad to 3 digits

STEP A3: GENERATE FROM TEMPLATE
  - Read: skills/record-docs/templates/RFC.md
  - Fill in ALL sections

STEP A4: SAVE
  - Save to: doc/rfcs/NNN-kebab-title.md

STEP A5: UPDATE INDICES
  - Update doc/rfcs/README.md
  - Update doc/README.md or doc/index.md
```

### Workflow B: Date-based types (Retrospective, Meeting Notes, Agent Session)

```
STEP B1: GET TODAY'S DATE
  - Run: date +%Y%m%d

STEP B2: CHECK FOR EXISTING
  - Run: ls doc/<dir>/<today-date>-* 2>/dev/null
  - If same-date file on same topic exists → update existing

STEP B3: GENERATE FROM TEMPLATE
  - Retrospective → skills/record-docs/templates/RETROSPECTIVE.md
  - Meeting Notes → skills/record-docs/templates/MEETING-NOTES.md
  - Agent Session → skills/record-docs/templates/AGENT-SESSION.md

STEP B4: SAVE
  - Save to: doc/<dir>/YYYYMMDD-<topic>.md

STEP B5: UPDATE INDICES
  - Update doc/<dir>/README.md
  - Update doc/README.md or doc/index.md
```

### Workflow C: Module/Feature-based types (Spec, PRD, Design)

```
STEP C1: DETERMINE NAME
  - Use kebab-case module or feature name
  - Ask user to confirm if ambiguous

STEP C2: CHECK FOR EXISTING
  - Run: ls doc/<dir>/ | grep -i "<name>"
  - If match → update existing, don't create duplicate

STEP C3: GENERATE FROM TEMPLATE
  - Spec → skills/record-docs/templates/SPEC.md
  - PRD → skills/record-docs/templates/PRD.md
  - Design Doc → no template (use drawio for diagrams if visual; link to external design tool output)

STEP C4: SAVE
  - Save to: doc/<dir>/<feature-name>.md

STEP C5: UPDATE INDICES
  - Update doc/<dir>/README.md
  - Update doc/README.md or doc/index.md
```

### Workflow D: Glossary (术语表) — Single File Update

```
STEP D1: CHECK FILE EXISTS
  - Run: ls doc/glossary.md 2>/dev/null
  - If not exists → create from template:
    cp skills/record-docs/templates/GLOSSARY.md doc/glossary.md

STEP D2: READ CURRENT GLOSSARY
  - Read: doc/glossary.md (to avoid duplicates and check existing terms)

STEP D3: ADD TERM ENTRY
  - Determine which table the term belongs to:
    - 项目专用术语 — project/domain-specific terms
    - 架构术语 — architecture patterns and concepts
    - 技术栈简称 — tech stack abbreviations
  - Add row with: 术语, 缩写, 定义, 上下文, 相关文档
  - If term already exists but definition differs → clarify with user before overwriting

STEP D4: CROSS-REFERENCE FROM SOURCE DOCUMENT
  - In the document that introduced this term (ADR, Spec, RFC), add a back-link:
    "术语定义见 [术语表](../glossary.md#<term-anchor>)"

STEP D5: NO INDEX UPDATE NEEDED
  - glossary.md is a standalone top-level file; no category README to update
```

## Design Doc + drawio Integration

When creating a design doc in `doc/design/`:

1. If the design involves architecture diagrams, load `record-c4` or `drawio` skill as needed
2. Store .drawio source files in `doc/assets/` (not in `doc/design/`)
3. Export diagram images to `doc/assets/` and link from the design doc
4. In the design doc markdown, reference both the .drawio source and the exported image

## Directory Structure

```
skills/record-docs/
├── SKILL.md                   # This file
└── templates/
    ├── SPEC.md                # Technical specification template
    ├── RFC.md                 # Request for Comments template
    ├── PRD.md                 # Product Requirement Document template
    ├── RETROSPECTIVE.md       # Sprint/project retrospective template
    ├── MEETING-NOTES.md       # Meeting notes template
    ├── AGENT-SESSION.md       # Agent work session record template
    └── GLOSSARY.md            # Glossary/术语表 template
```
