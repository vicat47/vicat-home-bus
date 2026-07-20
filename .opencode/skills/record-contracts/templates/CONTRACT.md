---
status: draft              # draft | in-review | complete | superseded | archived
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: ""
tags: ["contract"]
contract_type: ""           # interface-mapping | api-spec | message-schema | data-contract | callback-contract
source: ""                  # MANDATORY — C4 element name (e.g., "AgentEventHandler")
target: ""                  # MANDATORY — C4 element name (e.g., "ACPSession Controller")
protocol: ""                # ACP | REST | gRPC | Kafka | AMQP | WebSocket | Webhook | MySQL | PostgreSQL
related:
  adr: ""                  # ADR that justified this contract's protocol choice
  c4: ""                   # C4 model file containing source/target relationship
  research: ""
  radar: ""
---

# CONTRACT: [Source] ↔ [Target] — [Brief Description]

## Overview

[1-2 paragraphs: what interaction does this contract govern? Why does it exist? What decisions drove the protocol choice?]

---

## Source & Target (C4 Traceability)

| Role | C4 Element | C4 File | Responsibility |
|------|-----------|---------|---------------|
| **Source** | [C4 element name] | `doc/c4/[file].md` | [what this component does, and its role in the interaction] |
| **Target** | [C4 element name] | `doc/c4/[file].md` | [what this component does, and its role in the interaction] |

### Interaction Diagram
```
[Source Component] ──([Protocol]: [Direction])──> [Target Component]
```

---

## Interface Mapping
> Fill this section ONLY when contract_type = interface-mapping

### Mapping Table

| Source Event | Trigger Condition | Target Protocol Type | Conversion Rule | Notes |
|-------------|-------------------|---------------------|----------------|-------|
| [internal event name] | [when this event fires] | [target message type] | [transformation logic, field mapping] | [edge cases] |
| [internal event name] | [when this event fires] | [target message type] | [transformation logic, field mapping] | [edge cases] |

### Field-Level Mapping

```yaml
# Source → Target field mapping (for key event types)
mappings:
  - source_event: "[internal event name]"
    target_type: "[external protocol message type]"
    fields:
      - source_path: "[internal.field.path]"
        target_path: "[external.field.path]"
        transform: "[pass-through | rename | format | enrich | conditional]"
        required: true/false
        notes: "[transformation notes]"
```

### Conversion Conditions (Non-1:1 Mappings)

| Condition | Source Field Value | Target Protocol Type | Rationale |
|-----------|-------------------|---------------------|-----------|
| [condition name] | [specific value or range] | [which target type is chosen] | [why this branching exists] |

---

## API Specification
> Fill this section ONLY when contract_type = api-spec

### Base Configuration
- **Base URL**: `[base path]`
- **Auth Method**: [None | Bearer Token | API Key | OAuth2]
- **Content Type**: `application/json` (default)
- **Rate Limit**: [requests/sec or requests/min]

### Endpoints

#### `[METHOD] [path]`
- **Purpose**: [what this endpoint does]
- **Auth Required**: Yes/No

**Request**:
```json
{
  "field_name": "type // description // required/optional // constraints"
}
```

**Response (Success — [status code])**:
```json
{
  "field_name": "type // description"
}
```

**Response (Error)**:
```json
{
  "error_code": "[ERROR_CODE]",
  "message": "human-readable message"
}
```

### Error Codes

| Code | HTTP Status | Meaning | When Returned |
|------|------------|---------|---------------|
| `[ERROR_CODE]` | [4xx/5xx] | [description] | [trigger condition] |

---

## Message Schema
> Fill this section ONLY when contract_type = message-schema

### Channel Configuration
- **Topic/Queue Name**: `[topic.queue.name]`
- **Broker**: [Kafka / RabbitMQ / Pulsar]
- **Partitions**: [N] (if Kafka)
- **Replication Factor**: [N] (if Kafka)
- **Retention**: [time or size-based]

### Producer
- **Component**: [C4 element name]
- **Group/Client ID**: `[producer-group-id]`
- **Partition Key**: [field used for partitioning]
- **Serialization**: [Avro / JSON / Protobuf]

### Consumer(s)
| Consumer Component | Group ID | Delivery Semantic | Dead Letter |
|-------------------|----------|------------------|-------------|
| [C4 element] | `[consumer-group]` | at-least-once / exactly-once | [DLQ topic name or none] |

### Message Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "[Message Type Name]",
  "type": "object",
  "properties": {
    "[field_name]": {
      "type": "[string | number | boolean | object | array]",
      "description": "[field description]",
      "nullable": false
    }
  },
  "required": ["[field_1]", "[field_2]"]
}
```

### Compatibility Strategy
- **Schema Registry**: [Yes/No, with URL]
- **Compatibility Mode**: [BACKWARD | FORWARD | FULL | NONE]
- **Deprecation Policy**: [how old fields are removed, notice period]

---

## Data Contract
> Fill this section ONLY when contract_type = data-contract

### Shared Resource
- **Database**: [database name or connection string reference]
- **Database Type**: [MySQL / PostgreSQL / MongoDB / etc.]
- **Connection Pool**: [per-service config]

### Table Ownership Matrix

| Table / Collection | Owner (Read+Write) | Reader (Read-Only) | No Access | Migration Owner |
|-------------------|--------------------|--------------------|-----------|----------------|
| `[table_name]` | [component A] | [component B] | [component C] | [component name] |
| `[table_name]` | [component B] | — | [component A] | [component name] |

### Cross-Component Query Restrictions

| Restriction | Scope | Rationale |
|------------|-------|-----------|
| [e.g., "Component B MUST NOT JOIN table_X owned by Component A"] | [affected queries or code paths] | [why — coupling risk, performance, etc.] |
| [e.g., "Component A can only SELECT from table_Y; INSERT/UPDATE/DELETE forbidden"] | [affected queries or code paths] | [why] |

### Migration Coordination
- **When tables owned by Component A change**: [who must be notified, notification lead time]
- **Breaking change policy**: [how breaking schema changes are coordinated]

---

## Callback / Webhook Contract
> Fill this section ONLY when contract_type = callback-contract

### Callback Registration
- **Registrar Component**: [who accepts callback registrations]
- **Registration Method**: [how callbacks are registered — API, config, runtime]
- **Callback URL / Channel**: [where callbacks are delivered]

### Trigger Conditions

| Trigger | Condition | Payload Type | Notes |
|---------|----------|-------------|-------|
| [trigger name] | [when this callback fires] | [payload schema reference] | [any special notes] |

### Callback Payload

```json
{
  "event_type": "[trigger_name]",
  "timestamp": "ISO-8601",
  "data": {
    "[field]": "type // description"
  }
}
```

### Reliability Guarantees
- **Timeout**: [seconds before callback is considered failed]
- **Retry Policy**: [max retries, backoff strategy]
- **Delivery Guarantee**: [at-most-once / at-least-once / exactly-once]
- **Failure Handling**: [what happens when callback fails — dead letter, alerting]

---

## Anti-Patterns

> ACTIVE: This section is the contract's most defensive value. List every KNOWN WRONG WAY to use this contract. Engineers and AI agents should read this BEFORE writing code.

| # | Anti-Pattern | Why It's Wrong | Detection Rule |
|---|-------------|---------------|----------------|
| 1 | [describe the wrong approach] | [why it breaks the contract — data corruption, protocol violation, silent failure] | [how to detect this in code review] |
| 2 | [describe the wrong approach] | [why it breaks the contract] | [how to detect this in code review] |

---

## Evolution Log

| Date | Version | Change | Changed By | Status Impact |
|------|---------|--------|------------|--------------|
| YYYY-MM-DD | v1.0 | Initial creation | [author] | draft → in-review |
| YYYY-MM-DD | v1.1 | [description of change] | [author] | [status change if any] |
