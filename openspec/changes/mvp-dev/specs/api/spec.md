## ADDED Requirements

### Requirement: Event submission endpoint
The system SHALL provide POST /v1/events to accept new events with schema validation and idempotency.

#### Scenario: Valid event submitted
- **WHEN** a valid CreateEventRequest JSON is posted
- **THEN** the system returns HTTP 200 with {event_id, status: "accepted", message: "事件已接收"}

#### Scenario: Invalid event schema
- **WHEN** an event with missing required fields or invalid intent is posted
- **THEN** the system returns HTTP 400 with ErrorResponse containing INVALID_EVENT_SCHEMA code and details

#### Scenario: Duplicate event_id
- **WHEN** an event with an existing event_id is posted
- **THEN** the system returns HTTP 200 with {event_id, status, duplicate: true, message: "事件已存在（幂等命中）"} and does not re-execute

#### Scenario: Auto-generated event_id
- **WHEN** an event is posted without an event_id
- **THEN** the system generates one in the format evt_<session>_<seq> and returns it

### Requirement: Event status query endpoint
The system SHALL provide GET /v1/events/{event_id} to query event execution status.

#### Scenario: Event exists with executions
- **WHEN** GET /v1/events/{event_id} is called for an existing event with completed executions
- **THEN** the system returns HTTP 200 with EventStatusResponse containing event_id, status, intent, created_at, updated_at, and executions array

#### Scenario: Event not found
- **WHEN** GET /v1/events/{event_id} is called with a non-existent event_id
- **THEN** the system returns HTTP 404 with ErrorResponse containing EVENT_NOT_FOUND code

### Requirement: Query proxy endpoint
The system SHALL provide POST /v1/query to route read requests to backend adapters.

#### Scenario: Query routed to Grocy adapter
- **WHEN** POST /v1/query with target=grocy and operation=stock_query is submitted
- **THEN** the system routes to Grocy adapter, writes a query event to events table, and returns the result

#### Scenario: Query writes event log
- **WHEN** any query is executed
- **THEN** an entry is written to events table with intent=query but NO execution records are created

#### Scenario: Backend unavailable during query
- **WHEN** the target backend is unreachable
- **THEN** the system returns HTTP 502 with ErrorResponse containing ADAPTER_UNAVAILABLE code, but still writes the query event log

### Requirement: Health check endpoint
The system SHALL provide GET /v1/health to report HomeBus and adapter health.

#### Scenario: All adapters healthy
- **WHEN** GET /v1/health is called and all backends are reachable
- **THEN** the system returns HTTP 200 with {status: "healthy", adapters: {grocy: "ok", beancount: "ok", homebox: "ok"}}

#### Scenario: Some adapters degraded
- **WHEN** GET /v1/health is called and some backends are unreachable
- **THEN** the system returns HTTP 200 with {status: "degraded", adapters: {..., homebox: "error"}}, not an error status code

### Requirement: Unified error response format
The system SHALL return all errors in a consistent ErrorResponse format.

#### Scenario: Any non-200 response
- **WHEN** any endpoint returns an error
- **THEN** the response body contains {error: {code: ErrorCode, message: string, details: {}}}

### Requirement: Background task execution
The system SHALL use FastAPI BackgroundTasks to process events asynchronously after returning the accepted response.

#### Scenario: Event accepted before backend execution
- **WHEN** POST /v1/events is called
- **THEN** the API returns immediately after DB persistence, and backend dispatch/execution runs in a background task
