## ADDED Requirements

### Requirement: Publish command
The system SHALL provide `homebus publish` to submit events via --body JSON or --file path.

#### Scenario: Submit via --body
- **WHEN** `homebus publish --body '{"intent":"purchase",...}'` is executed
- **THEN** the CLI POSTs to /v1/events, prints JSON response to stdout, and exits 0 on success

#### Scenario: Submit via --file
- **WHEN** `homebus publish --file ./event.json` is executed
- **THEN** the CLI reads the file, POSTs its content, and produces the same output as --body

#### Scenario: API error
- **WHEN** the API returns 4xx or 5xx
- **THEN** the CLI prints error details to stderr and exits with code 1

### Requirement: Status command
The system SHALL provide `homebus status` to query event execution status.

#### Scenario: Query event status
- **WHEN** `homebus status --event-id evt_xxx` is executed
- **THEN** the CLI GETs from /v1/events/{event_id}, prints EventStatusResponse JSON to stdout

#### Scenario: Watch mode polls until terminal state
- **WHEN** `homebus status --event-id evt_xxx --watch` is executed
- **THEN** the CLI polls /v1/events/{event_id} until status is success/compensated/failed, then prints the final response

#### Scenario: Watch timeout
- **WHEN** `homebus status --event-id evt_xxx --watch --timeout 10` is executed and event does not reach terminal state within 10s
- **THEN** the CLI prints timeout error to stderr and exits with code 1

### Requirement: Query command
The system SHALL provide `homebus query` to route read requests to backends.

#### Scenario: Query Grocy stock
- **WHEN** `homebus query --target grocy --operation stock_query --params '{"product_name":"牛奶"}'` is executed
- **THEN** the CLI POSTs to /v1/query and prints the data response

### Requirement: Health command
The system SHALL provide `homebus health` to check HomeBus and adapter availability.

#### Scenario: Health check succeeds
- **WHEN** `homebus health` is executed
- **THEN** the CLI GETs /v1/health and prints the HealthResponse JSON

### Requirement: Init command
The system SHALL provide `homebus init` to generate configuration files.

#### Scenario: First-time init
- **WHEN** `homebus init` is executed and no config files exist
- **THEN** the CLI creates ~/.config/homebus/ with config.toml template, registry.toml template, and .env.example template

#### Scenario: Init with existing files
- **WHEN** `homebus init` is executed and config files already exist
- **THEN** the CLI skips existing files with a notification, unless --force is specified

### Requirement: API URL configuration discovery
The system SHALL resolve the API URL with the priority: --api-url > HOMEBUS_CLI_URL env > config.toml cli.api_url > http://localhost:8080.

#### Scenario: Explicit --api-url takes priority
- **WHEN** `homebus health --api-url http://remote:8080` is executed
- **THEN** the CLI uses http://remote:8080 regardless of env vars or config files

### Requirement: JSON output to stdout, errors to stderr
The system SHALL write all success output as JSON to stdout and all error messages to stderr.

#### Scenario: Success writes JSON to stdout only
- **WHEN** any CLI command succeeds
- **THEN** only valid JSON is written to stdout, nothing to stderr

#### Scenario: Failure writes to stderr only
- **WHEN** any CLI command fails
- **THEN** the error message is written to stderr, and nothing or empty is written to stdout
