## ADDED Requirements

### Requirement: Compensation action derivation
The system SHALL derive compensation operations from the original subtask's service and action using a COMPENSATION_MAP.

#### Scenario: Compensate Grocy add_stock
- **WHEN** a grocy add_stock subtask needs compensation
- **THEN** the system generates a grocy consume_stock compensation with reversed (negative) quantities

#### Scenario: Compensate Beancount record_expense
- **WHEN** a beancount record_expense subtask needs compensation
- **THEN** the system generates a beancount delete_entry compensation using the original event_id

#### Scenario: Compensate Homebox create_asset
- **WHEN** a homebox create_asset subtask needs compensation
- **THEN** the system generates a homebox delete_asset compensation using the asset_id from the original result

#### Scenario: Unknown action has no compensation
- **WHEN** a subtask's (service, action) is not in COMPENSATION_MAP
- **THEN** the system raises UncompensatableError

### Requirement: Sequential compensation execution
The system SHALL execute compensation operations sequentially (not DAG-based), recording each as a new execution record.

#### Scenario: Compensation creates new execution records
- **WHEN** Saga compensation is triggered for a failed event
- **THEN** each compensation operation creates a new execution record with is_compensation=1

#### Scenario: Original executions marked as compensated
- **WHEN** compensation completes successfully
- **THEN** the original successful execution records have their status updated from "success" to "compensated"

### Requirement: Compensation failure handling
The system SHALL handle cases where compensation itself fails.

#### Scenario: Compensation operation fails
- **WHEN** a compensation operation itself fails
- **THEN** the event's final status is set to "failed" (not "compensated")

### Requirement: Beancount compensation uses physical deletion
The system SHALL compensate Beancount entries by physically deleting the entry lines (undo), not by creating offsetting entries.

#### Scenario: Delete removes entry from .bean file
- **WHEN** beancount delete_entry is called for compensation
- **THEN** the matching entry lines are physically removed from the .bean file

### Requirement: Grocy compensation uses reverse operation
The system SHALL compensate Grocy stock changes by creating reverse stock records, not by deleting the original add_stock record.

#### Scenario: Reverse stock adds negative consumption
- **WHEN** grocy add_stock is compensated
- **THEN** a new consume_stock record is created with negative quantity (which effectively increases stock in Grocy's operation log model)

### Requirement: Homebox compensation handles 404 idempotently
The system SHALL treat a 404 response from Homebox delete_asset as success during compensation.

#### Scenario: Asset already deleted
- **WHEN** delete_asset is called for compensation and Homebox returns 404
- **THEN** the compensation is considered successful (goal: "asset should not exist" is already achieved)
