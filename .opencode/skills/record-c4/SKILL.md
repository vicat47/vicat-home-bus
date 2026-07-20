---
name: record-c4
description: >-
  Activate when the user asks to draw system architecture, record C4 model, create architecture diagrams,
  detect architectural drift, or mentions C4、系统架构、架构图、容器图、组件图、架构漂移.
category: documentation
tags: ["c4", "architecture", "diagram", "drift-detection", "yaml", "model"]
---

# Record C4 — Architecture Models & Drift Detection

Document architecture using the C4 model — Context, Containers, Components, and Code. Each diagram shows exactly ONE zoom level. Relationships matter more than boxes.

**Dependencies**: Load `doc-structure` for directory infrastructure, progressive indexing, and naming conventions. Load `drawio` when the user requests visual diagrams from C4 models.

**Cross-reference**: `record-adr` — every ADR must link to affected C4 elements. `record-compliance` — compliance rules derive from C4 container boundaries. See `record-architecture` for the full skill dependency graph.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language.

## C4 Four-Level Model

| Level | Shows | Audience |
|-------|-------|----------|
| **Context (Level 1)** | How the system fits in its external environment | PMs, stakeholders |
| **Containers (Level 2)** | Independently deployable technology blocks | Architects, platform engineers |
| **Components (Level 3)** | Logical groupings within a container | Service owners |
| **Code (Level 4)** | Class and interface relationships (prefer auto-generation) | Developers |

### Key Principles

1. Each diagram shows ONE zoom level — never mix levels
2. Relationships are more valuable than boxes — always annotate protocol and data flow direction
3. Don't try to show everything at once
4. C4 and UML are not mutually exclusive — use UML at Code level

## Architecture as Code — YAML Format

C4 models are expressed in YAML for machine-readable architecture. YAML blocks are embedded inside the markdown C4 document.

```yaml
systems:
  - name: E-Commerce Platform
    type: software_system
    containers:
      - name: API Service
        type: api
        technologies: [Go, gRPC]
      - name: Product Database
        type: database
        technologies: [PostgreSQL]

relationships:
  - from: API Service
    to: Product Database
    label: "Reads/writes product data"
    protocol: "TCP/SQL"
    direction: outbound
```

## Relationship Annotation Rules

Every relationship MUST specify:

| Field | Required? | Example |
|-------|-----------|---------|
| `from` | YES | Source element name |
| `to` | YES | Target element name |
| `label` | YES | Human-readable description of data flow |
| `protocol` | YES for sync | `HTTPS/JSON`, `gRPC/Protobuf` |
| `direction` | YES | `inbound` / `outbound` |
| `middleware` | YES for async | `Kafka/OrderCreated`, `RabbitMQ/payment.events` |

For **asynchronous** relationships, use `middleware` + `topic` instead of `protocol`:

```yaml
relationships:
  - from: Order Service
    to: Payment Service
    label: "Sends order confirmation"
    middleware: Kafka
    topic: order.confirmed
    direction: outbound
```

## C4 Model Lifecycle State Machine

```
                  ┌─────────┐
                  │  draft  │  ← Model being authored
                  └────┬────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
        ┌───────────┐ ┌──────┐ ┌───────────┐
        │ confirmed │ │ draft│ │ cancelled │  ← Abandoned
        └─────┬─────┘ └──────┘ └───────────┘
              │       (revision)
              │         ▲
              ▼         │
        ┌───────────┐   │
        │  updated  │───┘   ← Code changes → model must update
        └───────────┘
```

### State Transition Rules

| From | To | Trigger |
|------|-----|---------|
| `draft` | `confirmed` | Human review approves the model |
| `draft` | `cancelled` | Model no longer needed |
| `confirmed` | `updated` | Code changes require model update |
| `updated` | `confirmed` | Update verified (drift check passes) |
| `confirmed` | `draft` | Major revision needed |

## Smart Loading Strategy

C4 models accumulate. Use level-aware loading:

```
STEP L.1: Read doc/c4/README.md first
STEP L.2: Identify the target level (from user request or task context):
          - System Context → load system-*.md files
          - Container → load container-*.md files + parent system
          - Component → load component-*.md files + parent container
STEP L.3: Load ONLY models at the target or parent level
          - Skip models at unrelated levels (e.g., Component models when working on System Context)
STEP L.4: Skip stale models:
          - Status: draft with created date > 90 days ago
STEP L.5: If > 10 models at a level, load only the 5 most recently updated
```

## Human Review Gate

After generating a C4 model (STEP 3), a mandatory review MUST be completed:

```
REVIEW.1: Present the C4 model to the user with:
          - Level (System/Container/Component) and name
          - Key relationships and dependencies
          - Any identified gaps or architectural decisions

REVIEW.2: Ask user:
          1. C4 模型是否正确反映了当前架构？
          2. 关系标注是否完整（协议/数据流方向）？
          3. 是否需要导出为可视化图表（drawio）？

REVIEW.3: On user confirmation → set status to confirmed
REVIEW.4: On user revision request → update model, re-present
REVIEW.5: On user rejection → set status to cancelled
```

## Exact Creation Workflow

```
STEP 1: DETERMINE C4 LEVEL
  - Ask user: "Which level? System Context / Container / Component / Code?"
  - If user doesn't know: ask about the target audience to infer level

STEP 2: READ EXISTING C4 MODELS
  - Run: ls doc/c4/*.md
  - Read relevant files to avoid duplication
  - Check if a parent element already exists (e.g., system must exist before container)

STEP 3: GENERATE FROM TEMPLATE
  - Read: skills/record-c4/templates/C4.md
  - Fill in the level-specific section:
    - System Context → "System Context" section
    - Container → "Containers" section
    - Component → "Components" section

STEP 3.5: HUMAN REVIEW GATE (MANDATORY)
  - Execute the Human Review Gate procedure documented above
  - C4 model status remains draft until user explicitly confirms
  - On confirmation → update status to confirmed

STEP 5: ADD YAML BLOCK
  - Copy from template and fill in ALL required fields
  - Ensure every relationship has from/to/label/protocol+middleware/direction

STEP 6: NAME AND SAVE
  - Format: [level-]kebab-name.md
  - Level values: system, container, component
  - Example: system-ecommerce-platform.md, container-payment-service.md
  - Save to: doc/c4/<filename>

STEP 7: UPDATE INDICES
  - Update doc/c4/README.md
  - Update doc/README.md or doc/index.md

STEP 8: CROSS-LINK ADRs
  - Run: grep -l "<container-name>" doc/adr/**/*.md
  - If ADRs reference this C4 element, update them with the correct file link
```

## Architecture Drift Detection

Architectural drift = the gap between what documentation says and what code actually does.

### Drift Score Interpretation

| Score | Meaning |
|-------|---------|
| 90-100% | Excellent — docs match code closely |
| 70-89% | Good — mostly accurate, some gaps |
| 50-69% | Fair — significant drift, time to update |
| < 50% | Documents are fictional — immediate action required |

### Five Validation Dimensions

| Dimension | What to Check | Command |
|-----------|--------------|---------|
| **Systems** | Do repo names match documented system names? | Compare `doc/c4/system-*.md` titles against project directory name |
| **Containers** | Do top-level directories correspond to documented containers? | `ls -d */` vs grep for `name:` in `doc/c4/container-*.md` |
| **Components** | Are components valid given their parent container exists? | grep `parent_container` in C4 YAML, verify container file exists |
| **Code Elements** | Do file paths referenced in docs still exist on disk? | Extract paths from C4 docs; `test -f <path>` for each |
| **Relationships** | Are both ends of every relationship valid? | For each `from`/`to` in YAML, grep for matching import/dependency in code |

### Exact Drift Detection Commands

Execute these commands to perform drift detection:

```bash
# STEP 1: Extract all C4 relationships
grep -A1 "from:" doc/c4/*.md | paste - - | sed 's/.*from: //;s/to: / → /'

# STEP 2: For each relationship, search code for corresponding import/dependency
# Example: if doc says "API Service → Product Database"
grep -r "product.*database\|productdb\|product_db" --include="*.go" --include="*.py" --include="*.ts" --include="*.java" -l

# STEP 3: Calculate per-dimension percentages
# (count_matches / count_total) * 100

# STEP 4: Record in drift trend file
echo "| $(date +%Y-%m-%d) | {systems}% | {containers}% | {components}% | {code}% | {relationships}% | {aggregate}% |" >> doc/c4/drift-trend.md
```

### Trend Tracking (Not Snapshots)

1. Record drift score after each significant change
2. Store scores in `doc/c4/drift-trend.md` as a markdown table
3. Alert if aggregate score drops below 70%
4. Investigate root cause of ANY decline

## Connection to drawio Skill

When the user wants a **visual diagram** of the C4 model:

```
1. Read the corresponding C4 YAML/model file from doc/c4/
2. Load the drawio skill
3. Use drawio to generate a .drawio diagram from the YAML structure
4. Export to PNG/SVG as needed
5. Save the .drawio file in doc/c4/ (or doc/assets/) alongside the markdown model
```

Do NOT create a .drawio diagram unless the user explicitly requests a visual diagram. The markdown+YAML is the authoritative source.

## Naming Convention

```
[level-]kebab-name.md
```

- `system-` — System Context diagrams
- `container-` — Container diagrams
- `component-` — Component diagrams

Examples: `system-ecommerce-platform.md`, `container-payment-service.md`, `component-order-validator.md`

## Directory Structure

```
skills/record-c4/
├── SKILL.md          # This file
└── templates/
    └── C4.md         # C4 model template (all four levels)
```
