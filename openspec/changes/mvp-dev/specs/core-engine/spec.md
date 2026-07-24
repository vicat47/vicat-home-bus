## ADDED Requirements

### Requirement: Event lifecycle pipeline
The system SHALL process events through a validated pipeline: schema validation → idempotency check → persistence → dispatch → execution → aggregation.

#### Scenario: Purchase event flows through pipeline
- **WHEN** a valid purchase event is submitted to POST /v1/events
- **THEN** the system validates the schema, writes to events table with status=accepted, returns {event_id, status: "accepted"}, then asynchronously dispatches subtasks, executes them, and updates the final status

#### Scenario: Consume event flows through pipeline
- **WHEN** a valid consume event is submitted
- **THEN** the system dispatches a single grocy consume_stock subtask and executes it

### Requirement: Sub-task derivation from event intent
The system SHALL derive backend subtasks from the event intent and item categories using the routing registry.

#### Scenario: Purchase with consumable items
- **WHEN** a purchase event contains items with category=consumable
- **THEN** the dispatch engine generates Grocy add_stock (L0, depends_on=[]) and Beancount record_expense (L1, depends_on=[0]) subtasks

#### Scenario: Purchase with durable items
- **WHEN** a purchase event contains items with category=durable
- **THEN** the dispatch engine generates Grocy add_stock (L0), Beancount record_expense (L1), and Homebox create_asset (L1) subtasks

#### Scenario: Purchase with mixed category items
- **WHEN** a purchase event contains both consumable and durable items
- **THEN** Beancount record_expense handles all items with appropriate posting types (consumable→expense, durable→asset), and Homebox only processes durable items

### Requirement: DAG-based parallel execution
The system SHALL execute subtasks respecting their dependency graph, with concurrent execution within each layer.

#### Scenario: Layer execution succeeds
- **WHEN** a DAG has L0=[seq=0] and L1=[seq=1, seq=2]
- **THEN** seq=0 executes first; when it succeeds, seq=1 and seq=2 execute concurrently

#### Scenario: Layer execution fails
- **WHEN** a subtask fails at any layer
- **THEN** the executor cancels all in-flight subtasks in that layer, does not proceed to the next layer, and triggers Saga compensation

### Requirement: Execution timeout and retry
The system SHALL enforce a timeout per subtask and retry failed subtasks up to a configured maximum.

#### Scenario: Subtask times out
- **WHEN** a subtask exceeds its timeout (default 30s)
- **THEN** the subtask is marked as failed and the executor handles it as a failure

#### Scenario: Subtask retries on failure
- **WHEN** a subtask fails and retry_count < max_retries (default 3)
- **THEN** the executor retries the subtask, incrementing retry_count

### Requirement: Result aggregation to final status
The system SHALL aggregate all execution results to determine the event's final status.

#### Scenario: All subtasks succeed
- **WHEN** all subtasks for an event complete successfully
- **THEN** the aggregator sets event status to "success"

#### Scenario: Partial failure with successful compensation
- **WHEN** some subtasks fail and Saga compensation completes successfully
- **THEN** the aggregator sets event status to "compensated"

#### Scenario: Compensation also fails
- **WHEN** both a subtask and its compensation fail
- **THEN** the aggregator sets event status to "failed"
