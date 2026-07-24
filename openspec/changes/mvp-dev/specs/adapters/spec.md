## ADDED Requirements

### Requirement: Unified adapter interface
The system SHALL require all backend adapters to implement the AdapterBase abstract interface.

#### Scenario: Adapter implements required methods
- **WHEN** a new adapter class is created
- **THEN** it must implement execute(action, params) → dict, health_check() → dict, and list_actions() → list[ActionMeta]

#### Scenario: Adapter returns success response
- **WHEN** an adapter action completes successfully
- **THEN** the return value is {success: true, data: {…}}

#### Scenario: Adapter returns failure response
- **WHEN** an adapter action fails
- **THEN** the return value is {success: false, error: "description"}

### Requirement: Grocy stock operations
The system SHALL support add_stock, consume_stock, and stock_query operations on Grocy.

#### Scenario: Add stock resolves product name
- **WHEN** add_stock is called with item name "牛奶"
- **THEN** the adapter resolves the name to a Grocy product_id by checking cache first, then API, then updates cache

#### Scenario: Add stock fails on unknown product
- **WHEN** a product name cannot be resolved to a Grocy product_id
- **THEN** the adapter returns {success: false, error: "产品'xxx'在 Grocy 中不存在"} (fail-fast, no silent skip)

#### Scenario: Consume stock succeeds
- **WHEN** consume_stock is called with valid items
- **THEN** the adapter decrements stock quantities in Grocy

#### Scenario: Stock query returns product info
- **WHEN** stock_query is called with a product name
- **THEN** the adapter returns {product_name, product_id, stock, unit}

### Requirement: Beancount entry generation and file I/O
The system SHALL generate Beancount entries with #homebus tag and homebus_event:/homebus_time: meta fields.

#### Scenario: Generate purchase entry
- **WHEN** record_expense is called with event details
- **THEN** the generated .bean entry includes #homebus tag, homebus_event: meta for idempotency, and homebus_time: meta for timestamp

#### Scenario: Write entry to correct file
- **WHEN** a Beancount entry is written
- **THEN** it is appended to {ledger_path}/{YYYY}/0-default/homebus-{MM}.bean

#### Scenario: IDempotent entry check
- **WHEN** record_expense is called with an already-processed event_id
- **THEN** the adapter detects the existing homebus_event: meta and returns {success: true, already_exists: true}

#### Scenario: Delete entry by event_id
- **WHEN** delete_entry is called (Saga compensation)
- **THEN** the adapter scans .bean files for homebus_event: meta, removes the matching entry lines

#### Scenario: Post-write validation
- **WHEN** a .bean file is modified
- **THEN** the system runs bean-check to validate and git commit to persist the change

### Requirement: Homebox asset operations
The system SHALL support create_asset and delete_asset operations on Homebox.

#### Scenario: Create asset succeeds
- **WHEN** create_asset is called with name, category, location, and price
- **THEN** the adapter POSTs to Homebox API and returns {asset_id, name}

#### Scenario: Delete asset handles 404 idempotently
- **WHEN** delete_asset is called and Homebox returns 404 (asset already deleted)
- **THEN** the adapter returns {success: true, data: {deleted: false, note: "asset already deleted"}}

### Requirement: Adapter health checks
The system SHALL provide health checks for each backend with independent failure handling.

#### Scenario: Grocy health check
- **WHEN** Grocy API /api/system/info is reachable within 5s
- **THEN** health_check returns {healthy: true}

#### Scenario: Beancount health check
- **WHEN** ledger_path directory exists, .bean files are readable, and bean-check is available
- **THEN** health_check returns {healthy: true, detail: "bean-check v2.3.6"}

#### Scenario: Homebox health check
- **WHEN** Homebox API /api/v1/status is reachable within 5s
- **THEN** health_check returns {healthy: true}
