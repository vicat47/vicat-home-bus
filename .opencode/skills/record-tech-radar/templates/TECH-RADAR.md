# TECH-RADAR-[NNN]: [Technology Name]

- **Status**: Adopt / Trial / Assess / Hold
- **Date**: YYYY-MM-DD
- **Evaluator**: [person]
- **Associated ADR**: [ADR-XXX](link)
- **Technology Category**: [Language / Framework / Database / Tool / Platform / Library]

## Overview
[Brief description of this technology and its positioning within the organization]

---

## Tech Radar Status Reference

### Four Status Definitions

| Status | Meaning | Usage Guidance |
|--------|---------|---------------|
| **Adopt** | Proven, recommended for wide use | "Default choice for new projects. Teams should actively adopt." |
| **Trial** | Promising, needs real-project validation | "Suitable for non-critical projects. Collect feedback." |
| **Assess** | Worth exploring, needs further research | "Schedule time to investigate. Evaluate fit for our context." |
| **Hold** | Not recommended or deprecated | "Avoid in new projects. Plan migration for existing usage." |

### Current Status: [Adopt / Trial / Assess / Hold]

**Status Change History**
| Date | Status | Change Reason | Decided By |
|------|--------|--------------|------------|
| YYYY-MM-DD | [status] | [reason] | [person] |

---

## Technology Details

### Basic Information
- **Name**: [name]
- **Version**: [currently evaluated version]
- **License**: [MIT/Apache-2.0/GPL/Commercial]
- **Maintainer**: [organization/person]
- **GitHub/Website**: [url]
- **Last Updated**: [date]

### Technology Assessment

#### Pros
- [Pro 1]
- [Pro 2]
- [Pro 3]

#### Cons
- [Con 1]
- [Con 2]
- [Con 3]

#### Suitable Scenarios
- [Scenario 1]: [why suitable]
- [Scenario 2]: [why suitable]

#### Unsuitable Scenarios
- [Scenario 1]: [why unsuitable]
- [Scenario 2]: [why unsuitable]

### Comparison with Existing Technologies
| Dimension | This Technology | Alternative A | Alternative B |
|-----------|----------------|---------------|---------------|
| [Performance] | [...] | [...] | [...] |
| [Learning Curve] | [...] | [...] | [...] |
| [Community] | [...] | [...] | [...] |
| [Ecosystem Maturity] | [...] | [...] | [...] |
| [Ops Cost] | [...] | [...] | [...] |

### Validation Results
- **PoC Completed**: Yes/No
- **PoC Report**: [link]
- **Performance Test**: [summary of results]
- **Security Review**: [Passed/Failed/Pending]

---

## Tech Radar Definition (YAML)
```yaml
tech_radar:
  id: TECH-RADAR-[NNN]
  name: [Technology Name]
  category: [Language/Framework/Database/Tool/Platform/Library]
  status: adopt/trial/assess/hold
  date: YYYY-MM-DD

  info:
    version: [version]
    license: [license]
    maintainer: [maintainer]
    url: [url]
    last_updated: YYYY-MM-DD

  assessment:
    pros:
      - [Pro 1]
      - [Pro 2]
    cons:
      - [Con 1]
      - [Con 2]

    use_cases:
      - scenario: [Scenario 1]
        reason: [why suitable]
    avoid_cases:
      - scenario: [Scenario 1]
        reason: [why unsuitable]

    comparisons:
      - dimension: [Dimension]
        this_tech: [...]
        alternative_a: [...]
        alternative_b: [...]

    validation:
      poc_completed: true/false
      poc_report: [link]
      security_review: passed/failed/pending

  status_history:
    - date: YYYY-MM-DD
      status: [status]
      reason: [change reason]
```

---

## Usage Guide

### Getting Started
[Brief getting-started steps or link to internal guide]

### Known Issues
- [Issue 1]: [description and workaround]
- [Issue 2]: [description and workaround]

### Internal Resources
- **Example Projects**: [link]
- **Best Practices Doc**: [link]
- **Point of Contact**: [person/team]

## Change Log
| Date | Version | Change Description | Changed By |
|------|---------|-------------------|------------|
| YYYY-MM-DD | v1.0 | Initial assessment | [person] |
| YYYY-MM-DD | v1.1 | [status change/updated assessment] | [person] |
