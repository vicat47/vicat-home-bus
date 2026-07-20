---
name: record-aha-moments
description: >-
  Activate when the user asks to record an insight, capture a sudden idea, or mentions 灵感、顿悟、
  非正式想法、insight、aha、灵光一闪、想法收集.
category: documentation
tags: ["aha-moments", "insight", "ideas", "lightweight", "capture"]
---

# Record Aha Moments — Lightweight Insight Capture

Lightweight, informal records of sudden insights, breakthroughs, or half-baked ideas during development. This is the **"idea collection box"** — ultra-low barrier to create, high potential for future inspiration.

**Dependencies**: Load `doc-structure` for directory infrastructure and naming conventions.

**Cross-reference**: Aha moments may graduate into any `record-*` document type. After creation, periodically check if the idea has matured enough to be promoted to a spec, RFC, ADR, or research report.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

## When to Capture — Decision Logic

### CAPTURE (create file in `doc/aha-moments/`):

- ✅ User suddenly understood a complex technical concept
- ✅ User made an unexpected discovery during debugging
- ✅ A conversation produced a new idea worth preserving
- ✅ A random thought that might connect knowledge points later
- ✅ Something "clicked" and the user wants to keep this moment

### DO NOT CAPTURE — Route elsewhere:

- ❌ Idea is fully formed and ready for implementation → use `record-docs` (spec/RFC/PRD) or `record-adr`
- ❌ Formal architecture decision → use `record-adr`
- ❌ Needs team review or approval → use `record-docs` (RFC/spec)

## Agent Behavior Rules

1. **Default routing**: When the user says "record an insight / 记一个灵感 / 灵光一闪", default to creating in `doc/aha-moments/`
2. **Naming**: Use `YYYYMMDD-kebab-title.md`
3. **Search prioritization**: When searching for "灵感、顿悟、非正式想法、insight、aha", search `doc/aha-moments/` first
4. **Back-reference**: When a formal document originates from an aha moment, include `Originating from: aha-moments/YYYYMMDD-title.md`
5. **FORBIDDEN auto-promotion**: NEVER use aha moment content directly for production decisions. Must be reviewed and explicitly migrated by the user.
6. **Format freedom**: Content can be one sentence, a sketch, a conversation fragment, or raw technical notes. No template is required — though a lightweight suggestion is available at `templates/AHA-MOMENT.md`

## Exact Creation Workflow

```
STEP 1: CAPTURE THE INSIGHT
  - Ask user: "What just clicked? Describe it in one sentence."
  - If user already provided content, use it directly

STEP 2: DETERMINE FILENAME
  - Run: date +%Y%m%d
  - Create kebab-case title from the insight summary
  - Format: YYYYMMDD-kebab-title.md
  - Example: 20250612-why-not-use-wal-for-cdc.md

STEP 3: CREATE FILE
  - Save to: doc/aha-moments/YYYYMMDD-kebab-title.md
  - Content: Raw insight text — NO minimum length, NO required structure
  - Optionally use the lightweight template: skills/record-aha-moments/templates/AHA-MOMENT.md

STEP 4: SUGGEST POTENTIAL MATURATION PATHS (do NOT execute)
  - Based on content, suggest where this idea COULD go:
    "This insight might eventually become: [an ADR / a research topic / a spec / an RFC]"
  - DO NOT create the suggested document — only flag the potential

STEP 5: UPDATE INDICES
  - Update doc/aha-moments/README.md (add row)
  - Update doc/README.md or doc/index.md
```

## Graduation Paths (Manual Only)

Aha moments graduate to formal documents ONLY when the user explicitly requests it:

| Aha Moment Content | Potential Graduation Target | Skill to Load |
|-------------------|----------------------------|---------------|
| "We should use X instead of Y because..." | ADR | `record-adr` |
| "I wonder how X compares to Y..." | Research Report | `record-research` |
| "We could implement X by doing Y..." | RFC or Spec | `record-docs` |
| "What if we changed the architecture to..." | ADR + C4 update | `record-adr`, `record-c4` |

When graduating, add back-reference in the new document:
```markdown
Originating from: [aha-moments/YYYYMMDD-title.md](../aha-moments/YYYYMMDD-title.md)
```

## Naming Convention

```
YYYYMMDD-kebab-title.md
```

Examples: `20250401-prompt-caching-insight.md`, `20250612-why-not-use-wal-for-cdc.md`

## Directory Structure

```
skills/record-aha-moments/
├── SKILL.md                  # This file
└── templates/
    └── AHA-MOMENT.md         # Lightweight optional template
```
