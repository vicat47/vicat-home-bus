---
name: record-architecture
description: >-
  Activate when the user asks to record architecture assets but is unsure which type, or mentions
  "record architecture"、记录架构、架构文档、路由. Acts as router and lifecycle orchestrator.
  Routes to record-adr, record-c4, record-compliance, record-tech-radar, record-research,
  record-docs, record-aha-moments based on content type. Supports preflight → code → review → postship lifecycle.
category: documentation
tags: ["router", "orchestrator", "lifecycle", "preflight", "review", "postship", "drift"]
---

# Record Architecture — Router & Lifecycle Orchestrator

**ROLE**: This skill routes architecture documentation requests to the appropriate `record-*` skill and orchestrates the 4-phase architecture-aware development lifecycle.

**Dependencies**: This skill depends on `doc-structure` for directory infrastructure and progressive indexing. All `record-*` sub-skills listed below are also dependencies.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

## Skill Dependency Graph

The following directed graph governs all `record-*` skills. Load this graph from `doc-structure` before routing any request. See `doc-structure/SKILL.md` for the authoritative GraphViz definition.

```
                    ┌──────────────────────┐
                    │   record-architecture │  ← Router / Orchestrator
                    └─┬──┬──┬──┬──┬──┬──┬─┘
                      │  │  │  │  │  │  │
          ┌───────────┘  │  │  │  │  │  └───────────┐
          ▼              ▼  ▼  ▼  ▼  ▼              ▼
┌─────────────────┐  ┌──────────┐  ┌──────────┐  ┌─────────────────────┐
│  record-adr     │  │record-c4 │  │record-   │  │   record-docs        │
│  ◄── requires ->│  │          │  │contracts │  │   (specs, RFCs, PRDs, │
│  record-c4       │  │◄─ draws ─┘  │◄── req ──│  │   meetings, retro,   │
│                  │  │  via drawio│  │record-c4 │  │   agent-sessions)    │
└────────┬─────────┘  └────┬──────┘  │record-adr│  └─────────────────────┘
         │                 │         └────┬─────┘
         ▼                 ▼              │
┌─────────────────┐  ┌─────────────────┐  │
│record-research  │  │record-tech-radar│  │
│◄── feeds ──────►│  │◄── feeds ──────►│  │
└─────────────────┘  └─────────────────┘  │
                                          ▼
                                 ┌─────────────────┐
                                 │record-compliance │
                                 │◄── req ──────────│
                                 │record-adr, c4,   │
                                 │record-contracts  │
                                 └─────────────────┘

         ┌─────────────────────┐
         │ record-aha-moments   │  ← Lightweight, standalone (feeds into
         │                      │     all others via idea maturation)
         └─────────────────────┘

         ┌─────────────────────┐
         │  record-release      │  ← Release management (SHOULD reference
         │                      │     record-docs, record-adr, record-c4,
         │                      │     record-compliance for major versions)
         └─────────────────────┘

         ┌─────────────────────┐
         │ record-tradeoffs     │  ← Trade-off & debt tracking (SHOULD load
         │                      │     record-adr for promoted path,
         │                      │     record-compliance for domain overrides)
         └─────────────────────┘

         ┌─────────────────────┐
         │    doc-structure     │  ← Infrastructure foundation (all skills
         │                      │     depend on this)
         └─────────────────────┘
```

**Edge descriptions:**
- `record-adr` → `record-c4`: Each ADR must link to affected C4 elements
- `record-adr` ↔ `record-research`: ADRs may cite research; research may recommend ADR creation
- `record-adr` ↔ `record-tech-radar`: Tech adoption decisions are ADRs; ADRs drive radar status
- `record-c4` → `record-compliance`: Compliance rules derive from C4 container boundaries
- `record-contracts` → `record-c4`: Every contract MUST trace source and target to C4 elements
- `record-adr` → `record-contracts`: ADRs may produce contracts as concrete protocol outputs
- `record-contracts` → `record-compliance`: Compliance rules SHOULD trace to contract documents for Contract Compliance and Event Channel rule types
- `record-compliance` → `record-adr`, `record-c4`, `record-contracts`: Every rule must trace to an ADR, C4 element, or contract
- `record-docs` → `drawio`: Architecture diagrams may be exported via drawio skill
- `record-aha-moments` → *: Aha moments may graduate into any record-* document type
- `record-release` → `record-docs`: Release plans SHOULD reference PRD/Spec/RFC when features originate from them
- `record-release` → `record-adr`: Release plans SHOULD reference ADRs when version ships architectural decisions
- `record-release` → `record-c4`: Release plans SHOULD reference C4 elements affected by this version
- `record-release` → `record-compliance`: Major releases (x.0.0) SHOULD trigger compliance check before GA
- `record-tradeoffs` → `record-adr`: Accepted trade-offs may be promoted to formal ADRs when constraints become permanent
- `record-tradeoffs` → `record-docs`: Resolved trade-offs may be absorbed into AGENTS.md, .rules, specs, or PRDs
- `record-tradeoffs` ↔ `record-compliance`: Trade-off arbitration SHOULD consume domain override rules from compliance; trade-off lessons may be absorbed into compliance rules
- `record-aha-moments` → `record-tradeoffs`: Aha moments may graduate into trade-off records for systematic tracking

## Routing Table — Exact Decision Logic

Read the user's request. Match against the **Intent** column. Execute the **Action** column.

| Intent (user says / requests) | SKILL to load | Action |
|------------------------------|--------------|--------|
| "record architecture" without specifying type; "I have an architecture thing to document but don't know what type" | (this skill) | Present routing options; ask clarifying question |
| Architecture decision, technology choice, trade-off evaluation, "this vs that" reasoning; mentions ADR、架构决策、技术选型、方案取舍 | `record-adr` | Load `record-adr` → scan `doc/adr/` → generate ADR from `templates/ADR.md` |
| System/container/component diagram, C4 model, architecture diagram, drift detection; mentions C4、架构图、容器图、组件图、架构漂移 | `record-c4` | Load `record-c4` → read existing C4 models → generate/update from `templates/C4.md` |
| Architecture rule, constraint, guardrail, coding boundary; mentions 合规规则、架构约束、层边界、技术约束 | `record-compliance` | Load `record-compliance` → read relevant ADR/C4 → generate rule from `templates/COMPLIANCE-RULE.md` |
| Component protocol contract, event mapping, API spec, message schema, data contract; mentions 契约、接口协议、事件映射、消息通道、API契约、协议对齐 | `record-contracts` | Load `record-contracts` → read C4 models → generate contract from `templates/CONTRACT.md` |
| Technology recommendation, adoption status, tech evaluation; mentions 技术雷达、技术选型、Adopt/Trial/Assess/Hold | `record-tech-radar` | Load `record-tech-radar` → scan `doc/tech-radar/` → generate/recommend from `templates/TECH-RADAR.md` |
| Technology research, comparison report, proof-of-concept findings; mentions 技术调研、方案对比、调研报告、选型分析 | `record-research` | Load `record-research` → scan `doc/research/` → generate from `templates/RESEARCH.md` |
| Spec, RFC, PRD, design doc, retrospective, meeting notes, agent session record; mentions 规格说明、RFC、PRD、回顾、会议记录、Agent 记录 | `record-docs` | Load `record-docs` → determine sub-type → generate from corresponding template |
| Insight, sudden idea, "aha moment", half-baked thought; mentions 灵感、顿悟、灵光一闪、想法收集 | `record-aha-moments` | Load `record-aha-moments` → create file in `doc/aha-moments/` |
| Release plan, version release, feature checklist, CHANGELOG; mentions 发布计划、版本发布、功能清单、CHANGELOG、版本管理、RC、GA、SNAPSHOT | `record-release` | Load `record-release` → parse version → determine granularity → generate release plan from `templates/RELEASE.md` |
| Temporary compromise, tech debt tracking, trade-off registration, revisit backlog; mentions 取舍、技术债务、临时方案、权宜之计、回归收口、trade-off标记、@tradeoff | `record-tradeoffs` | Load `record-tradeoffs` → determine source type → insert @tradeoff annotation → create record from `templates/TRADEOFF.md` |
| Key decisions summary, project technology overview, decision index; mentions 关键决策、技术决策汇总、决策索引 | `record-adr` | Load `record-adr` → read `doc/key-decisions.md` → update/add entries based on recent ADR/tech-radar changes |
| Glossary, terminology, term definition, abbreviation; mentions 术语表、术语定义、缩写、专用词汇 | `record-docs` | Load `record-docs` → read `doc/glossary.md` → add/update term entries |

## 4-Phase Lifecycle Orchestration

### Phase 1: Preflight (pre-code validation)

**Trigger**: User says "validate plan before coding", "preflight check", or implicitly before any architectural change.

**Exact steps to execute**:

```
STEP 1.1: Load record-compliance skill
STEP 1.2: Run: ls doc/compliance-rules/*.md | head -20
STEP 1.3: Load ALL compliance rule files found (read each .md)
STEP 1.4: Load record-c4 skill
STEP 1.5: Run: ls doc/c4/*.md | head -20
STEP 1.6: Read relevant C4 model files (match by system/container name to planned change)
STEP 1.7: Load record-adr skill
STEP 1.8: Check for existing ADRs in the affected domain: ls doc/adr/<domain>/ 2>/dev/null || ls doc/adr/*.md
STEP 1.9: Report violations found: [PASS/WARN/FAIL] for each compliance rule
STEP 1.10: If no existing ADR covers the decision being made → suggest creating one
```

### Phase 2: Review (code/PR review)

**Trigger**: User says "review this PR", "architecture review", or provides code diff for architecture check.

**Exact steps to execute**:

```
STEP 2.1: Load record-compliance skill
STEP 2.2: Read ALL compliance rules: for f in doc/compliance-rules/*.md; do read $f; done
STEP 2.3: For each rule type, check the diff against the rule condition
STEP 2.4: Load record-c4 skill
STEP 2.5: Read ALL C4 model files: for f in doc/c4/*.md; do read $f; done
STEP 2.6: Compare code imports/calls against documented C4 relationships
STEP 2.7: Detect drift: for each relationship in C4 YAML, check if corresponding code import exists
STEP 2.8: Report: [DRIFT] for mismatches, [VIOLATION] for rule breaks
STEP 2.9: If a new architectural decision was made in code → suggest creating record-adr
```

### Phase 3: Postship (post-deployment update)

**Trigger**: User says "just merged", "deployment done", "after ship", "postship update".

**Exact steps to execute**:

```
STEP 3.1: Identify what changed (read the merged PR description / commit messages)
STEP 3.2: Load record-c4 skill
STEP 3.3: If new containers/components added → update C4 model YAML in doc/c4/
STEP 3.4: If new relationships introduced → add relationship entries in affected C4 files
STEP 3.5: Load record-adr skill
STEP 3.6: If an undocumented architectural decision was made → create ADR
STEP 3.7: Load record-docs skill (sub-type: specs)
STEP 3.8: If API endpoints changed → update doc/api-contracts/ (or specs/)
STEP 3.9: Run drift recalc: compare C4 relationships against code imports; update doc/c4/drift-trend.md
```

### Phase 4: Drift Detection (discrepancy discovery)

**Trigger**: User says "check for drift", "is architecture up to date?", "drift score".

**Exact steps to execute**:

```
STEP 4.1: Load record-c4 skill
STEP 4.2: For each C4 model file in doc/c4/, extract all YAML relationship entries:
         grep -A3 "relationships:" doc/c4/*.md
STEP 4.3: For each relationship (from → to), search codebase for corresponding import/dependency:
         grep -r "<from_module>" --include="*.go" --include="*.py" --include="*.ts" --include="*.java"
STEP 4.4: Calculate per-dimension score:
         - Systems:  count of documented systems with matching repo-names / total documented systems
         - Containers: count of documented containers with matching top-level dirs / total documented containers
         - Components: count of documented components with matching source files / total documented components
         - Code Elements: count of documented file paths that still exist / total documented file paths
         - Relationships: count of documented relationships with matching code dependencies / total documented relationships
STEP 4.5: Calculate weighted aggregate drift score
STEP 4.6: Record score in doc/c4/drift-trend.md with date
STEP 4.7: If score < 70% → recommend immediate correction: flag the 3 worst dimensions
```

## Progressive Indexing

All architecture assets follow the 3-level progressive indexing system defined in `doc-structure`. Anytime a new document is created, update:

1. The category README (`doc/<category>/README.md`) — add row to navigation table
2. The global index (`doc/README.md` or `doc/index.md`) — increment document count

Refer to `doc-structure` skill for exact index update commands.

## Location

All assets are stored under the `doc/` directory. Exact subdirectory paths are defined in each target skill. Refer to `doc-structure` for directory infrastructure rules and the master naming convention table.
