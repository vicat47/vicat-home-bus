---
status: draft              # draft | active | deprecated
created: YYYY-MM-DD
updated: YYYY-MM-DD
author: ""
tags: ["compliance"]
rule_type: ""              # required-pattern | naming-convention | technology-constraint | layer-boundary | contract-compliance | dependency-rule | event-channel
severity: ""               # blocker | critical | warning | info
related:
  adr: ""                  # MANDATORY — link to ADR that justifies this rule
  c4: ""                   # MANDATORY — link to C4 element whose boundary this rule protects
  research: ""
  radar: ""
---

# COMPLIANCE-RULE-[NNN]: [Rule Name]

## Overview
[Brief description of this compliance rule's purpose and scope]

---

## 7 Rule Types Reference

| Type | Description | Example |
|------|-------------|---------|
| **Required Pattern** | Patterns that must or must not exist in code | "All database queries must use parameterized queries" |
| **Naming Convention** | File, type, function naming standards | "API endpoints must use kebab-case" |
| **Technology Constraint** | Lock technology stack by container | "Order service can only use PostgreSQL" |
| **Layer Boundary** | Import relationships between layers | "UI layer must not import Repository layer directly" |
| **Contract Compliance** | Code endpoints match API contracts | "All /api/v2/* endpoints must have OpenAPI docs" |
| **Dependency Rule** | Every import must have a C4 relationship | "No unapproved external dependencies" |
| **Event Channel** | Producers/consumers match declared channels | "Order events must publish to `orders` topic" |

---

## Rule Definition

### Rule Type: [Select from above]

### Rule Description
[Detailed description of what this rule enforces]

### Scope
- **Applicable Containers**: [container list]
- **Applicable Languages**: [Go/Java/TypeScript/All]
- **Excluded Paths**: `[glob patterns, e.g., **/test/**, **/vendor/**]`

### Rule Condition
```
[Natural language or pseudo-code describing the check condition]

Example:
IF import_path CONTAINS "github.com/unapproved/library"
THEN FAIL with message "Unapproved external dependency"
```

### Violation Example
```[language]
// ❌ VIOLATION — breaks this rule
[show violating code]
```

### Compliance Example
```[language]
// ✅ COMPLIANT — follows this rule
[show compliant code]
```

### Auto-Fix (if available)
[Describe the auto-fix method if one exists]

---

## Rule Definition (YAML)
```yaml
compliance_rule:
  id: COMPLIANCE-RULE-[NNN]
  name: [Rule Name]
  type: [Required Pattern / Naming Convention / Technology Constraint / Layer Boundary / Contract Compliance / Dependency Rule / Event Channel]
  status: active/deprecated/draft
  severity: blocker/critical/warning/info

  description: [Rule Description]

  scope:
    containers:
      - [Container 1]
      - [Container 2]
    languages:
      - [Go]
      - [TypeScript]
    exclude_paths:
      - "**/test/**"
      - "**/vendor/**"

  condition: |
    [Rule check condition]

  examples:
    violation: |
      // ❌ Violation
      [code example]
    compliant: |
      // ✅ Compliant
      [code example]

  auto_fix:
    available: true/false
    description: [auto-fix description]
```

---

## Enforcement
- **Check Timing**: [PR Review / CI Pipeline / Local Pre-commit / Preflight]
- **Check Tool**: [ESLint / Custom Script / Archyl Agent / Other]
- **Failure Behavior**: [Block Merge / Warning / Requires Approval]

## Exceptions
- **Exceptions Allowed**: Yes/No
- **Approval Process**: [describe how to request an exception]
- **Known Exceptions**:
  | Path/Module | Reason | Approver | Expiration |
  |------------|--------|---------|------------|
  | [path] | [reason] | [person] | YYYY-MM-DD |

## Change Log
| Date | Version | Change Description | Changed By |
|------|---------|-------------------|------------|
| YYYY-MM-DD | v1.0 | Initial creation | [person] |
| YYYY-MM-DD | v1.1 | [change description] | [person] |
