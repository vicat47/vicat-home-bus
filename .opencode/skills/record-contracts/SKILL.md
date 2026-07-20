---
name: record-contracts
description: >-
  Activate when the user asks to document component-to-component protocol contracts,
  event type mappings, API specifications between services, message channel schemas,
  or mentions 契约、接口协议、事件映射、消息通道、API契约、协议对齐、message mapping、schema contract.
category: documentation
tags: ["contracts", "api", "event", "protocol", "message", "interface", "mapping", "schema"]
---

# Record Contracts — Component Protocol Contracts

Document precise protocol contracts between C4 components — field-level mappings, event type conversions, API schemas, and message formats. Contracts bridge the gap between C4 topology ("where are the components?") and compliance rules ("what must be true about their interactions?").

**Dependencies**: Load `record-c4` (every contract's `source` and `target` MUST be existing C4 elements). Load `doc-structure` for directory infrastructure. Optionally load `record-adr` (protocol choices are often ADR results — the contract is the concrete output).

**Cross-reference**: `record-compliance` — "Contract Compliance" and "Event Channel" rule types SHOULD trace to contract documents. See `record-architecture` for the full skill dependency graph.

**OUTPUT LANGUAGE**: All model output to the user MUST be in **Simplified Chinese (简体中文)** unless the surrounding conversation context unambiguously requires English or another language. Contract document content itself follows the same rule.

## What a Contract Is (and Is Not)

- **IS**: A precise record of HOW two components communicate — field names, types, conversion rules, error handling, anti-patterns
- **IS NOT**: An architecture diagram (that's `record-c4` — it records THAT they communicate, not HOW)
- **IS NOT**: A decision record (that's `record-adr` — it explains WHY this protocol was chosen)
- **IS NOT**: A compliance rule (that's `record-compliance` — it ENFORCES what the contract requires)
- **IS NOT**: A general spec or RFC (that's `record-docs` — contracts are narrower, focused exclusively on component boundary protocols)

## When to Create a Contract

**CREATE when**:
- Two components communicate via a non-trivial protocol (event bus, message queue, bidirectional stream, structured callback)
- The mapping between internal events/fields and external protocol messages is **not 1:1** (requires conversion logic, conditional routing, or enrichment)
- The protocol enforces versioning constraints (backward/forward compatibility rules)
- Multiple teams own different sides of the contract interface
- There are explicit **anti-patterns** (forbidden mappings, disallowed conversions) that engineers need to know before writing code

**DO NOT CREATE when**:
- Simple pass-through from one layer to another with no transformation
- Purely private internal method calls within the same C4 container
- Standard REST CRUD with auto-generated OpenAPI (use `record-docs` spec instead)
- 1:1 field copy with no conversion logic

## 5 Contract Types

| contract_type | 说明 | 典型场景 |
|---|---|---|
| `interface-mapping` | 源语义域到目标语义域的字段级映射——含转换规则、条件分支、反模式 | 组件 A 的领域模型 → 组件 B 的协议/API 字段如何转换（非 1:1 时最需要此类型） |
| `api-spec` | 服务间 API 契约 — endpoint、请求/响应 schema、错误码枚举 | Connector Service 暴露 REST API，前端需要精确的 JSON 字段、状态码含义 |
| `message-schema` | 消息通道契约 — Kafka/Topic/Queue 的 schema、topic、生产/消费组 | Order Service 发 OrderCreated 到 Kafka，Payment Service 消费——约定 Avro schema、分区键 |
| `data-contract` | 共享数据契约 — 数据库表归属矩阵、读写权限、跨组件查询限制 | 两个服务共享同一 MySQL，但各自只读写特定表，禁止跨表 JOIN |
| `callback-contract` | 回调/Webhook 契约 — 触发条件、payload schema、超时、重试策略 | WebSocket Manager 通知 Event Forwarder 连接状态变更 |

## Init Workflow — Initialize Contracts Directory

When the user asks to "初始化契约目录" or "init contracts directory":

```
STEP 1: DELEGATE DIRECTORY SETUP TO doc-structure
  - Load doc-structure skill
  - Run doc-structure creation workflow:
      mkdir -p doc/contracts/
      cp skills/doc-structure/templates/README__TEMPLATE.md doc/contracts/README.md
      cp skills/doc-structure/templates/AGENTS__TEMPLATE.md doc/contracts/AGENTS.md
  - Copy the contract template:
      cp skills/record-contracts/templates/CONTRACT.md doc/contracts/_TEMPLATE.md

STEP 2: COLLECT CONTRACT-SPECIFIC CONTEXT
  - List available C4 elements: ls doc/c4/*.md 2>/dev/null
  - List available ADRs: ls doc/adr/*.md 2>/dev/null && ls doc/adr/*/*.md 2>/dev/null
  - Identify existing cross-component relationships from C4 YAML blocks:
      grep -E "(from:|to:)" doc/c4/*.md | sort -u

STEP 3: CUSTOMIZE README.md FOR CONTRACT CONTEXT
  Edit doc/contracts/README.md:
  - Replace placeholder description with contracts-specific scope
  - Add "Related Architecture Documents" section:
    - Link to available C4 models (from STEP 2)
    - Link to relevant ADRs (from STEP 2)
  - Add contract_type column to navigation table
  - Add link to _TEMPLATE.md

STEP 4: CUSTOMIZE AGENTS.md FOR CONTRACT CONTEXT
  Edit doc/contracts/AGENTS.md:
  - Update "When to Create Documents":
    - Add triggers from "When to Create a Contract" section above
    - Add exclusions: 1:1 pass-through, auto-generated OpenAPI, private method calls
  - Update "Regression Checks":
    - C4 traceability check: grep -E "(source:|target:)" doc/contracts/ && verify each in ls doc/c4/
    - ADR cross-reference check: grep "related.adr" doc/contracts/ | grep -v '""'
    - Anti-pattern freshness check: flag contracts with anti-patterns > 90 days old
  - Replace Core Principles table with contract-specific DO/DON'T
  - Replace Template Structure with CONTRACT.md skeleton
  - Add 5 contract types reference table
  - Update File Naming Convention to: YYYYMMDD[-NN]__kebab-name.md

STEP 5: UPDATE PARENT INDICES
  - If doc/README.md exists → add contracts entry
  - Run doc-structure index update if available

STEP 6: VERIFY
  - Confirm doc/contracts/ contains: README.md, AGENTS.md, _TEMPLATE.md
  - Confirm README.md lists available C4 elements for traceability
  - Confirm AGENTS.md includes contract-specific regression checks
```

## Contract Lifecycle State Machine

```
                  ┌─────────┐
                  │  draft  │  ← Contract being authored
                  └────┬────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
        ┌──────────┐ ┌──────┐ ┌───────────┐
        │in-review │ │draft │ │ cancelled │  ← Abandoned
        └────┬─────┘ └──────┘ └───────────┘
             │       (revision)
        ┌────┼────┐
        ▼         ▼
  ┌──────────┐ ┌───────────┐
  │ complete │ │ cancelled │  ← Rejected by review
  └────┬─────┘ └───────────┘
       │
  ┌────┼────┐
  ▼         ▼
┌──────────┐ ┌──────────┐
│superseded│ │ archived │  ← Contract no longer relevant
└──────────┘ └──────────┘
```

### State Transition Rules

| From | To | Trigger |
|------|-----|---------|
| `draft` | `in-review` | Author submits contract for review |
| `draft` | `cancelled` | Contract no longer needed or user abandons |
| `in-review` | `complete` | Review approved |
| `in-review` | `cancelled` | Rejected during review |
| `in-review` | `draft` | Revision requested by reviewer |
| `complete` | `superseded` | Newer contract replaces this one (e.g., protocol upgrade) |
| `complete` | `archived` | Source or target C4 element removed/deprecated |
| `complete` | `draft` | Major revision needed (protocol change) |

**NEVER delete a contract.** Superseded/archived contracts form the protocol evolution timeline — they explain why past mappings existed and when they changed.

## Smart Loading Strategy

Use triage-first loading instead of loading all contracts:

```
STEP L.1: Read doc/contracts/README.md first
STEP L.2: Scan the status column — identify active contracts
STEP L.3: Load ONLY:
          - Contracts with status: in-review (always — pending decisions)
          - Contracts with status: complete that match the current task's C4 elements
STEP L.4: Skip: draft, cancelled, superseded, archived unless explicitly referenced
STEP L.5: If > 10 active contracts, load only the 5 most recently updated
```

## Human Review Gate

After generating a contract, a mandatory human review phase MUST be completed:

```
REVIEW.1: Present the contract to the user with:
          - Contract type, source C4 element, target C4 element
          - Key mapping rules or schema highlights
          - Anti-patterns (what NOT to do)
          - Related ADR (protocol justification)

REVIEW.2: Ask user:
          1. 契约内容是否准确？(Confirm / Revise / Reject)
          2. 反模式列表是否完整？
          3. 是否需要补充边界情况？

REVIEW.3: On user confirmation → set status to in-review → then complete after final validation
REVIEW.4: On user revision request → update contract, re-present
REVIEW.5: On user rejection → set status to cancelled, document reason
```

## Exact Creation Workflow

```
STEP 1: IDENTIFY SOURCE & TARGET C4 ELEMENTS (MANDATORY)
  - Every contract MUST trace to two C4 elements (source ↔ target)
  - Run: ls doc/c4/*.md | head -20
  - If C4 elements don't exist yet → STOP, suggest creating C4 first (load record-c4)
  - Identify the relationship between them (sync/async, protocol, data direction)

STEP 2: DETERMINE CONTRACT TYPE
  - Match the interaction pattern to one of the 5 contract types
  - interface-mapping: 源语义域 → 目标语义域字段转换（事件映射、DTO 裁剪、协议转换、版本迁移）
  - api-spec: service → service via REST/gRPC
  - message-schema: service → topic/queue → service
  - data-contract: service → shared database
  - callback-contract: component → callback/notification to component

STEP 3: FIND RELATED ADRs (OPTIONAL BUT RECOMMENDED)
  - Run: grep -rl "<protocol-name>\|<source>\|<target>" doc/adr/ 2>/dev/null
  - If an ADR justifies the protocol choice → link it in related.adr

STEP 4: CHECK FOR EXISTING CONTRACTS (AVOID DUPLICATES)
  - Run: ls doc/contracts/ 2>/dev/null
  - Search for existing contracts involving same source/target:
      grep -l -E "(source:|target:)" doc/contracts/*.md 2>/dev/null | xargs grep -l "<source>\|<target>"
  - If similar contract exists → suggest updating existing, don't create duplicate

STEP 5: GENERATE CONTRACT DOCUMENT
  - Read template: skills/record-contracts/templates/CONTRACT.md
  - Fill in ALL sections:
    - YAML frontmatter (status: draft initially)
    - Source & Target (C4 element links, MANDATORY)
    - Contract-type-specific section (fill ONLY the section matching contract_type)
    - Anti-Patterns (list forbidden mappings/conversions)
    - Cross-References (links to ADR, C4)
  - For interface-mapping: fill in the mapping table with field-level precision
  - For api-spec: fill in endpoint table + request/response schema
  - For message-schema: fill in topic + message schema
  - For data-contract: fill in table ownership matrix
  - For callback-contract: fill in trigger conditions + payload schema

STEP 5.5: HUMAN REVIEW GATE (MANDATORY)
  - Execute the Human Review Gate procedure documented above
  - Contract status remains draft until user explicitly confirms

STEP 6: NAME AND SAVE
  - Get today's date: date +%Y%m%d  →  (e.g., 20260616)
  - Check for existing contracts with same date:
      ls doc/contracts/$(date +%Y%m%d)*.md 2>/dev/null
  - Assign suffix:
      If no match → YYYYMMDD__kebab-name.md
      If matches exist → count them, increment by 1, pad to 2 digits:
        YYYYMMDD_NN__kebab-name.md  (e.g., 20260616_02__another-contract.md)
  - Generate kebab-name from source-target-protocol (e.g., agent-eventhandler-acp-mapping)
  - Save to: doc/contracts/<filename>

STEP 7: UPDATE INDICES
  - Update doc/contracts/README.md (add row to navigation table)
  - Update doc/README.md or doc/index.md (increment contract count)

STEP 8: CROSS-LINK TO ADR AND C4
  - If the contract's source/target C4 file has a "Relationships" section → add a link back to this contract
  - If the contract references an ADR → update ADR's "Consequences" section with a link to the contract
```

## Naming Convention

```
YYYYMMDD[-NN]__kebab-name.md
```

- `YYYYMMDD` — creation date, always present
- `-NN` — 2-digit sequence number (01-99), ONLY added when multiple contracts created on the same date
- `__` — double underscore separator between date prefix and descriptive name
- `kebab-name` — short, descriptive name, typically source-target-protocol

Examples:
```
20260616__agent-eventhandler-acp-mapping.md
20260616_02__connector-service-custom-filter-api.md
20260618__order-service-kafka-payment-events.md
```

```bash
# Find existing contracts for today
ls doc/contracts/$(date +%Y%m%d)*.md 2>/dev/null

# Assign next sequence number if needed
# Count existing: ls doc/contracts/$(date +%Y%m%d)*.md | wc -l
# If count == 0 → no suffix, filename = YYYYMMDD__name.md
# If count >= 1 → suffix = count+1 (padded), filename = YYYYMMDD_NN__name.md
```

## Directory Structure

```
skills/record-contracts/
├── SKILL.md                     # This file
└── templates/
    └── CONTRACT.md              # Contract template (5 type-conditional sections)
```

## Connection to record-compliance

Contracts are the primary traceability source for two compliance rule types:

| Rule Type | Contract Traceability | Example Rule |
|-----------|----------------------|--------------|
| **Contract Compliance** | Rule's `related.adr` / `related.c4` MUST include contract reference | "AgentEventHandler MUST emit correct ACP SessionUpdate type per agent-eventhandler-acp-mapping" |
| **Event Channel** | Rule references contract's `message-schema` / `interface-mapping` | "Order events MUST publish to `order.events` topic per the order-service-kafka contract" |

When creating a compliance rule from a contract:
1. Read the contract's Anti-Patterns section
2. Convert each anti-pattern into a rule condition
3. Set severity based on impact: Blocker (data corruption) / Critical (protocol violation) / Warning (forbidden convenience shortcut)

```bash
# After creating a contract, scan for related compliance rules that need updating:
grep -rl "<contract-filename>" doc/compliance-rules/ 2>/dev/null
```
