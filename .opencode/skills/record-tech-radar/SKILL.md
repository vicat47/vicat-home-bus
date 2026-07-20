---
name: record-tech-radar
description: >-
  Activate when the user asks to record tech radar entries, evaluate technology adoption status,
  check technology recommendations, or mentions 技术雷达、技术选型、Adopt、Trial、Assess、Hold.
category: documentation
tags: ["tech-radar", "technology", "adoption", "evaluation", "selection"]
---

# Record Tech Radar — Technology Adoption Tracking

Track technology adoption status across the organization. AI agents MUST reference the tech radar when suggesting technologies for new features, evaluating dependencies, or reviewing PRs.

**Dependencies**: Load `doc-structure` for directory infrastructure, progressive indexing, and naming conventions.

**Cross-reference**: `record-adr` — technology adoption decisions are ADRs; ADRs drive radar status changes. `record-research` — research reports inform radar assessments. `record-compliance` — compliance rules may enforce radar status (e.g., "Hold" = no new usage).

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

## 4 Technology States

| State | Meaning | Agent Guidance |
|-------|---------|---------------|
| **Adopt** | Proven, recommended for wide use | "Default choice for new projects. Suggest this technology unless specific reasons to deviate." |
| **Trial** | Promising, needs real-project validation | "Suitable for non-critical projects. Collect feedback and report results." |
| **Assess** | Worth exploring, needs further research | "Schedule time to evaluate fit. Do NOT recommend for production yet." |
| **Hold** | Not recommended or deprecated | "Avoid in new projects. For existing usage, plan migration." |

## When the Agent MUST Check the Radar

The agent MUST read `doc/tech-radar/*.md` before:
1. Suggesting any technology for a new feature
2. Proposing a new dependency in a PR
3. Reviewing a PR that introduces new technology
4. Answering "what should we use for X?" questions

```bash
# Load all radar entries at once
for f in doc/tech-radar/*.md; do read "$f"; done
```

## Cross-Reference Actions

### When creating/updating a tech radar entry → check ADRs
```bash
# Find ADRs mentioning the technology
grep -rl "<tech-name>" doc/adr/**/*.md
```
If ADRs exist that justify the current radar status, link them in the radar entry.

### When creating an ADR about technology adoption → create/update radar entry
After creating an ADR that selects or rejects a technology, update the corresponding `doc/tech-radar/<tech-name>.md` to reflect the new status. Change the status history table.

### When creating a research report → update radar assessment
Research reports provide evidence for radar assessments. After publishing a research report, check if it affects any radar assessments and update accordingly.

### When radar status changes (especially Assess → Adopt or Adopt → Hold) → update Key Decisions
A radar status change to **Adopt** or **Hold** is a significant decision that should be reflected in `doc/key-decisions.md`:
```bash
# Check if key-decisions.md exists
ls doc/key-decisions.md 2>/dev/null

# If exists, evaluate: does this status change qualify as a key decision?
# Criteria: new core technology adopted (Adopt), major deprecation (Hold), technology platform shift
# If yes → read doc/key-decisions.md and update Technology Platform table
# If not exists → load record-adr skill for full key-decisions creation workflow
```
This cross-reference is a trigger action — the actual key-decisions update is handled by `record-adr`.

## Exact Creation Workflow

```
STEP 1: DETERMINE TECHNOLOGY NAME
  - Use official technology name: "Apache Kafka" not "kafka"
  - Normalize to lowercase kebab-case for filename: apache-kafka.md

STEP 2: CHECK FOR EXISTING ENTRY
  - Run: ls doc/tech-radar/ | grep -i "<tech-name>"
  - If exists → UPDATE the existing file, do not create a duplicate

STEP 3: GATHER EVIDENCE
  - Check research reports: grep -rl "<tech-name>" doc/research/**/*.md
  - Check ADRs: grep -rl "<tech-name>" doc/adr/**/*.md
  - Check compliance rules: grep -rl "<tech-name>" doc/compliance-rules/*.md

STEP 4: DETERMINE STATUS
  - Use the 4-state definitions above
  - If uncertain, default to "Assess" and recommend research

STEP 5: GENERATE FROM TEMPLATE
  - Read: skills/record-tech-radar/templates/TECH-RADAR.md
  - Fill in ALL sections:
    - Status (one of: Adopt / Trial / Assess / Hold)
    - Technology details (version, license, maintainer, url)
    - Pros/cons (at least 3 each)
    - Use/avoid scenarios
    - Comparison with existing alternatives
    - Validation results (PoC status)

STEP 6: SAVE
  - Format: kebab-tech-name.md (e.g., apache-kafka.md, typescript.md)
  - Save to: doc/tech-radar/<filename>

STEP 7: UPDATE STATUS HISTORY
  - If creating new: add initial status row
  - If updating: add new row with date and reason for status change

STEP 8: UPDATE INDICES
  - Update doc/tech-radar/README.md (add row)
  - Update doc/README.md or doc/index.md (increment radar count)
```

## Naming Convention

```
kebab-tech-name.md
```

Examples: `typescript.md`, `apache-kafka.md`, `apache-doris.md`, `react.md`

Each technology gets exactly ONE independent file. Never split evaluations of the same technology across multiple files.

## Directory Structure

```
skills/record-tech-radar/
├── SKILL.md              # This file
└── templates/
    └── TECH-RADAR.md     # Tech radar template (markdown + YAML)
```
