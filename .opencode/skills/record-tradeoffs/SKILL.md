---
name: record-tradeoffs
description: >-
  Activate when the agent makes a temporary compromise, encounters a tool error forcing a fallback,
  is uncertain about implementation correctness, or discovers post-hoc deviations from intended design.
  Use for recording trade-offs, tech debt, tactical compromises, and implementation divergences.
  Also activate on regression review (回归收口) to scan sessions and collect unmarked trade-offs.
  当 agent 产生临时取舍、遭遇错误被迫降级、对实现方案不确定、或回归审查需要收口时使用。
category: documentation
tags: ["tradeoff", "trade-off", "debt", "compromise", "divergence", "uncertain", "agent-swarm"]
---

# Record Trade-Offs — Temporary Compromise & Tech Debt Tracking

Records temporary trade-offs, tactical compromises, and implementation divergences that arise during LLM long-running tasks. Provides a shared state mechanism for cross-model agent swarm review and human arbitration.

**Dependencies**: Load `doc-structure` (MUST — directory infrastructure, naming conventions, triage loading). Load `record-adr` (SHOULD — promoted path). Load `record-compliance` (SHOULD — arbitration domain override rules).

**Cross-reference**: Trade-offs may graduate into any record-* document type. After creation, periodic regression review checks for stale entries and promotes eligible trade-offs.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

---

## 1. When to Capture — 4 Source Types

### 1.1 `deliberate` — Conscious Tactical Compromise

Agent knowingly accepts a suboptimal approach due to a temporary constraint.

**CAPTURE when**:
- Context window is near limit, skipping non-critical implementation details
- Token budget exhausted, deferring edge case handling
- Time pressure, deferring optimization to a later session
- Agent articulates: "I know X would be better, but I'll use Y for now because Z"

**Key characteristic**: Agent is AWARE of the compromise at creation time.

### 1.2 `uncertain` — Implementation Correctness Uncertain

Agent implements something but is not confident the approach is correct.

**CAPTURE when**:
- API docs are incomplete or potentially outdated in training data
- Multiple plausible implementations exist and agent chose one without certainty
- Agent thinks: "This might work, but I'm not sure"

**Key characteristic**: Agent is EXPLICITLY uncertain, not confident.

### 1.3 `divergence` — Forced Deviation from Intended Approach

A tool invocation fails (non-zero exit, exception, dependency missing), forcing agent to adopt a different approach than originally planned.

**CAPTURE when**:
- Tool returns error → agent changes implementation strategy
- Dependency unavailable → agent downgrades to simpler alternative
- Permission denied → agent uses workaround

**Key characteristic**: Triggered by an EXTERNAL error event. Original intent was clear; obstacle forced change. This is the most dangerous type — user sees final code and assumes it was the intended design.

### 1.4 `discovered` — Post-Hoc Detection

Noticed after the fact: by a review bot, during regression scan, or by another agent examining the codebase.

**CAPTURE when**:
- Review bot detects code pattern suggesting a compromise (no @tradeoff annotation present)
- Heuristic scan finds: long parameter lists, missing error handling, simplified algorithms
- Another agent cross-checking session transcripts finds unmarked divergences

**Key characteristic**: Detected EXTERNALLY, not by the original creator agent.

### Source Decision Tree

```
Agent encounters a compromise / deviation from ideal:

  Q1: Am I knowingly compromising because of a constraint I can name?
      → YES: deliberate

  Q2: Am I implementing something but uncertain if it's correct?
      → YES: uncertain

  Q3: Did a tool error force me to change my implementation approach?
      → YES: divergence

For review bots / regression scans:

  Q4: Did I detect a compromise that was NOT marked by the original agent?
      → YES: discovered
```

---

## 2. @tradeoff Annotation Protocol (Cross-Model Standard)

All models MUST use this exact format. Deviation from this syntax will be flagged as "format non-compliant" by review bots.

### Single-Line Format

```
@tradeoff(<source>, <severity>, revisit=<YYYY-MM-DD>): <one-line description>
```

### Multi-Line Format

```
/**
 * @tradeoff(<source>):
 * severity: <critical|high|medium|low>
 * intended: <what should have been done>
 * obstacle: <what prevented the intended approach>
 * obstacle_type: <dependency-missing|api-unsupported|permission-denied|env-incompatible|context-window|token-budget|time-pressure|missing-info|model-limitation|other>
 * revisit_trigger: <condition that should trigger revisit>
 * revisit_by: <YYYY-MM-DD>
 */
```

### Annotation Placement

- Place directly ABOVE the affected code block, class, or method
- Language-native comment syntax (// for Java/JS/Go/C#, # for Python/Ruby, -- for SQL/Lua)
- The `@tradeoff(` prefix is the machine-parseable marker regardless of comment style

### Examples

**deliberate (Java)**:
```java
// @tradeoff(deliberate, medium, revisit=2026-08-01):
// Context window near limit, skipping comprehensive error handling.
// Should add retry logic with exponential backoff when revisiting.
public Result process(Input input) {
    return service.call(input); // simplified
}
```

**divergence (Java)**:
```java
/**
 * @tradeoff(divergence):
 * severity: high
 * intended: ReentrantLock with tryLock(timeout)
 * obstacle: java.util.concurrent.locks unavailable (Maven unreachable)
 * obstacle_type: dependency-missing
 * revisit_trigger: Maven dependency resolution restored in CI
 * revisit_by: 2026-07-24
 */
synchronized (this) {
    if (condition) {
        // critical section
    }
}
```

**uncertain (Python)**:
```python
# @tradeoff(uncertain, medium, revisit=2026-08-01):
# Unsure if this API accepts milliseconds or seconds.
# Training data may be outdated. Verify against live docs.
def schedule_task(delay):
    scheduler.add(delay * 1000)
```

---

## 3. Multi-Agent Role Model

Trade-off lifecycle is driven by 5 roles — NOT by a single agent session. The same physical agent may play different roles in different sessions.

| Role | Responsibility | Permissions |
|------|---------------|-------------|
| **Creator** | Produces trade-off, inserts @tradeoff annotation, writes initial record | May dismiss own captured trade-off within the SAME session |
| **Detector** | Scans code/sessions for unmarked trade-offs (heuristic or review bot) | Creates `source: discovered` records |
| **Reviewer** | Validates obstacle reality, severity accuracy, intended approach correctness | captured → verified OR dismissed |
| **Arbiter** | Decides evolution direction: accept / reject / promote | verified → accepted / rejected / promoted |
| **Resolver** | Fixes code, removes annotation, closes record | accepted → resolved |

**Human position**: Human is an OVERLORD role — can intervene at any stage, override any agent decision, and has exclusive authority over security/data-integrity/compliance domains.

---

## 4. State Machine

```
                    [Creator]                    [Reviewer]           [Arbiter]
                    produces                    verifies              decides
                       │                           │                    │
                       ▼                           ▼                    ▼
                 ┌──────────┐               ┌──────────┐        ┌──────────┐
                 │ captured │──────────────▶│ verified │───────▶│ accepted │
                 └────┬─────┘               └────┬─────┘        └────┬─────┘
                      │                          │                   │
          (Creator    │                          │                   │
           dismiss    │              (Reviewer   │      (Arbiter     │
           only in    ▼              dismiss)    ▼      reject)     ▼
           same    ┌──────────┐               ┌──────────┐        ┌──────────┐
           session)│dismissed │               │dismissed │        │ rejected │
                   └──────────┘               └──────────┘        └──────────┘
                                                                      │
                    [Resolver / Arbiter]                               │
                    resolves / promotes / absorbs                      │
                       │                                               │
        ┌──────────────┼──────────────┐                                │
        ▼              ▼              ▼                                │
  ┌──────────┐  ┌──────────┐  ┌──────────┐                             │
  │ resolved │  │ promoted │  │ absorbed │                             │
  │(代码修复) │  │  → ADR   │  │→ AGENTS  │                             │
  └──────────┘  └──────────┘  │  /.rules  │                             │
                              └──────────┘                             │
        │              │              │                                │
        ▼              ▼              ▼                                ▼
  ┌──────────────────────────────────────────────────────────────────────┐
  │                         stale                                        │
  │  trigger: revisit_by expired AND status != resolved/promoted/absorbed │
  │  action: auto-escalate to Arbiter for re-evaluation                  │
  └──────────────────────────────────────────────────────────────────────┘
```

### State Transition Rules

| From | To | Triggered By | Trigger |
|------|-----|-------------|---------|
| (none) | `captured` | Creator | @tradeoff annotation inserted + record file written |
| (none) | `captured` | Detector | Heuristic scan or review bot discovers unmarked trade-off |
| `captured` | `dismissed` | Creator | Creator realizes annotation was wrong (same session only) |
| `captured` | `verified` | Reviewer | Obstacle confirmed real, severity accurate, intended approach valid |
| `captured` | `dismissed` | Reviewer | Reviewer determines: not a real trade-off |
| `verified` | `accepted` | Arbiter | Human or swarm vote approves: trade-off acknowledged, revisit_by set |
| `verified` | `rejected` | Arbiter | Human or swarm vote rejects: must fix immediately, cannot defer |
| `accepted` | `resolved` | Resolver | Code fixed, @tradeoff annotation removed, commit references trade-off |
| `accepted` | `promoted` | Arbiter | Trade-off becomes permanent → formal ADR created |
| `accepted` | `absorbed` | Arbiter | Lesson embedded into AGENTS.md / .rules / spec / PRD |
| `accepted` | `expired` | Arbiter or time | Trade-off no longer relevant (module removed, constraint gone) |
| `accepted` | `stale` | System check | `revisit_by` date passed without resolution |
| `stale` | `accepted` | Arbiter | Revisit_by extended, trade-off still relevant |
| `stale` | `resolved` | Resolver | Code finally fixed |
| `stale` | `expired` | Arbiter | Confirmed no longer relevant |

### End State Semantics

| End State | Meaning | Record preserved? |
|-----------|---------|-------------------|
| `resolved` | Code fixed, debt cleared | Yes (for audit trail) |
| `promoted` | Upgraded to formal ADR | Yes (points to ADR) |
| `absorbed` | Lesson integrated into AGENTS.md / .rules / spec | Yes (points to target) |
| `expired` | No longer relevant | Yes (with expiration reason) |
| `dismissed` | Determined not to be a trade-off | Yes (with dismissal reason, prevents re-creation) |
| `rejected` | Arbiter refused to defer — must fix now | Yes (with rejection reason) |

---

## 5. Loading Strategy — Role-Based Triage

Prevents context window explosion as trade-off count grows. Overrides `doc-structure` defaults for this category.

| Session Type | Load Content | Do NOT Load |
|-------------|-------------|-------------|
| **Creator** (implementation) | Only active trade-offs matching current module (≤5) | Full list, stale, other modules, dismissed |
| **Reviewer** (review bot) | @tradeoff annotations in PR diff + corresponding formal records | Other modules, unrelated trade-offs |
| **Arbiter** (decision) | All verified but not yet accepted | resolved, promoted, absorbed, expired, dismissed |
| **Resolver** (fix) | Target trade-off record + affected code location | All other trade-offs |

### Triage Rules (override doc-structure)

```
Creator session:
  L.1: Only load severity: critical + high + last 5 medium
  L.2: severity: low — never proactively load
  L.3: captured but not verified within 7 days — skip
  L.4: dismissed / rejected / expired / resolved — skip
  L.5: If active count > 20 — warn user and request category filter

Reviewer session:
  L.1: Scan PR diff for @tradeoff annotations
  L.2: For each annotation found → load corresponding formal record
  L.3: Run heuristic scan for unmarked potential trade-offs
  L.4: Present findings grouped by confidence (certain / probable / possible)

Arbiter session:
  L.1: Load all verified records (exclude captured — not yet reviewed)
  L.2: Group by severity — process critical/high first
  L.3: Check for stale records (revisit_by expired → auto-escalate)

Resolver session:
  L.1: Load ONLY the target trade-off
  L.2: Read affected code location
  L.3: After resolution, update record; unload from context
```

---

## 6. Arbitration Rules

### 6.1 Human Authority Hierarchy

| Condition | Authority | Mechanism |
|-----------|-----------|-----------|
| severity: low + unanimous vote | Agent swarm auto-execute | No human needed |
| severity: low + divided vote | Agent swarm execute + notify | Human can override post-hoc |
| severity: medium | Swarm vote, human silent-window override | 24h no objection = accepted |
| severity: high | Swarm recommends, human MUST confirm | Review bot blocks merge until human confirms |
| severity: critical | Human directly, swarm not involved | Immediate escalation |
| Security / Data Integrity / Compliance domain | Human directly | Swarm vote bypassed regardless of severity |

### 6.2 Swarm Voting Mechanism

| Vote Result | Action |
|-------------|--------|
| Unanimous accept | → accepted, record vote details |
| Simple majority accept | → accepted with minority dissent recorded |
| Tie (2:2 or 1:1) | → escalate to human Arbiter |
| Simple majority reject | → rejected with minority support recorded |
| Unanimous reject | → rejected, immediately convert to blocking issue |

### 6.3 Domain Override Rules

Defined in `record-compliance`. When `record-tradeoffs` performs arbitration, it SHOULD query `record-compliance` for active domain override rules. If the trade-off falls into an override domain:

1. Skip swarm voting entirely
2. Escalate to human Arbiter with: trade-off summary + matched domain + override reason
3. Human MUST explicitly confirm before status changes to accepted

**Minimum override domains** (these should be formalized in `record-compliance`):
- **Security**: Any trade-off tagged with security concerns → human decision mandatory
- **Data Integrity**: Any trade-off affecting data correctness → human decision mandatory
- **Compliance / Regulatory**: Any trade-off touching regulatory constraints → human decision mandatory

---

## 7. Core Workflows

### Workflow A: Creator (Implementation Session)

```
STEP A.1: Agent encounters trade-off during implementation
  → Determine source type using decision tree (§1)

STEP A.2: Insert @tradeoff annotation
  → Use standardized format (§2)
  → Place DIRECTLY above affected code

STEP A.3: Write formal record
  → Read: skills/record-tradeoffs/templates/TRADEOFF.md
  → Fill in all Creator sections:
    - source, severity, intended_approach, obstacle, obstacle_type,
      actual_approach, gap_assessment, revisit_by, revisit_trigger
  → Save to: doc/tradeoffs/YYYYMMDD__<short-slug>.md

STEP A.4: Reference in commit message
  → Include: "Trade-off: <SHORT-SLUG> (see doc/tradeoffs/YYYYMMDD__<short-slug>.md)"

STEP A.5: Update indices
  → Update doc/tradeoffs/README.md (add row)
```

### Workflow B: Reviewer (PR Review / Cross-Model Check)

```
STEP B.1: Scan PR diff for @tradeoff annotations
  → Parse each annotation, validate format (§2)
  → Flag "format non-compliant" if syntax deviates

STEP B.2: Run heuristic scan for UNMARKED trade-offs
  → Search patterns:
    - Overly long methods / parameter lists
    - Missing error handling after external calls
    - Commented-out code blocks
    - Simplified algorithms where complexity expected
  → Create source: discovered records with confidence:
    - certain: has explicit code evidence + matching session error log
    - probable: has code pattern match
    - possible: heuristic flag only

STEP B.3: For each trade-off (annotated + discovered):
  ✓ Verify obstacle is real (check session logs / tool error traces)
  ✓ Verify intended_approach is correct (cross-model validation)
  ✓ Verify severity is appropriate
  → Update: captured → verified (add reviewed_by, review_notes, confidence)
  → Or: captured → dismissed (if not a real trade-off)

STEP B.4: Output PR review summary table
  | Trade-off | Source | Severity | Status | Action Required |
  |-----------|--------|----------|--------|-----------------|
```

### Workflow C: Arbiter (Decision Session)

```
STEP C.1: Load all verified trade-offs
  → Group by severity
  → Check for domain overrides (§6.3)

STEP C.2: For each trade-off:
  → If domain override applies → escalate to human (§6.1)
  → If severity: critical → escalate to human
  → If severity: high → swarm recommend, human must confirm
  → If severity: medium → swarm vote + 24h human override window
  → If severity: low → swarm auto-process

STEP C.3: Execute decision:
  → accepted: set revisit_by, record arbitration details
  → rejected: document reason, convert to blocking issue if severity high+
  → promoted: trigger record-adr workflow
  → absorbed: specify target (AGENTS.md / .rules / spec / etc.)

STEP C.4: Update indices and notify Creator (if agent) of decision
```

### Workflow D: Resolver (Fix Session)

```
STEP D.1: Agent re-enters project
  → Triage loading (§5) returns active trade-offs for current module

STEP D.2: Agent: "I need to resolve <trade-off>"
  → Read full trade-off record
  → Locate affected code via @tradeoff annotation

STEP D.3: Implement fix
  → Apply intended_approach
  → Remove @tradeoff annotation
  → Commit: "Resolve trade-off <SHORT-SLUG>"

STEP D.4: Update trade-off record
  → status: accepted → resolved
  → resolution: { type: resolved }
  → resolved_by, resolved_in (commit hash)

STEP D.5: Update indices
```

### Workflow E: Regression Review (Session End or Scheduled)

```
STEP E.1: User triggers: "回归收口" / "regression review" / "collect trade-offs"

STEP E.2: Scan git diff for @tradeoff annotations
  → Collect all annotations → cross-reference with doc/tradeoffs/
  → Create formal records for annotations missing formal files

STEP E.3: Scan session transcript for tool errors
  → Find all non-zero exit codes / exceptions
  → Cross-reference: did each error cause an implementation change?
  → If yes AND no @tradeoff annotation → flag as potential divergence

STEP E.4: Scan code for degradation patterns
  → See Reviewer heuristic scan (Workflow B, STEP B.2)
  → Create source: discovered records for high-confidence findings

STEP E.5: Stale check
  → Find all accepted trade-offs where revisit_by < today
  → Update status: accepted → stale
  → Present stale list to user: "These trade-offs are past their revisit date"

STEP E.6: Graduation check
  → For long-lived trade-offs (> 3 months active):
    "This has been open for 3 months. Consider: resolve / promote to ADR / expire?"
```

---

## 8. Consumer Directory Structure

```
doc/tradeoffs/
├── README.md                      # Navigation: status / severity / source / revisit_by
├── AGENTS.md                      # Agent behavior guide (when to create, how to review)
└── YYYYMMDD__<short-slug>.md      # Trade-off record file
```

---

## 9. Skill Directory Structure

```
skills/record-tradeoffs/
├── SKILL.md                       # This file
├── templates/
│   └── TRADEOFF.md                # Trade-off record template
└── references/
    └── examples.md                # 6 complete examples (4 sources × various resolutions)
```
