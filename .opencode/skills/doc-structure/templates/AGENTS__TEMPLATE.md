# AGENTS.md: [Directory Name] Writing Guide

This document guides AI agents on how to write and handle [directory description, e.g., technology research and validation reports].

## When to Create Documents

**CREATE a new document when:**
- [Trigger condition 1]
- [Trigger condition 2]
- [Trigger condition 3]

**DO NOT CREATE when:**
- [Exclusion condition 1]
- [Exclusion condition 2]

## Regression Checks (MANDATORY before creating)

Before creating a new document, the agent MUST:

1. **Read category README**: Check for similar existing topics
   ```bash
   read doc/<category>/README.md
   ```
2. **Check numbering continuity**: Read directory contents, find max number +1
   ```bash
   ls doc/<category>/ | sort -V | tail -1
   ```
3. **Check global index**: If `doc/README.md` or `doc/index.md` exists, read it and prepare to update
4. **Avoid duplicates**: If a same-topic document already exists → UPDATE it, do NOT create a new one
   ```bash
   grep -rli "<topic keywords>" doc/<category>/ 2>/dev/null
   ```

## Core Principles

### DO

| Principle | Description | Example |
|-----------|-------------|---------|
| [Principle 1] | [description] | [example] |
| [Principle 2] | [description] | [example] |

### DON'T

| Error Type | Description | Bad Example |
|------------|-------------|------------|
| [Error 1] | [description] | [example] |
| [Error 2] | [description] | [example] |

## Template Structure

```markdown
# [Document Title]

## Context
<!-- Brief description -->

## Actions Taken
<!-- What was done -->

## Findings / Results
<!-- What was discovered -->

## Decisions Made
<!-- Decisions and rationale -->

## Next Steps
<!-- What should happen next -->
```

## Writing Checklist

After creating a document, verify:

- [ ] File naming follows convention
- [ ] Metadata is complete (date, author, status)
- [ ] Content structure is clear
- [ ] Language is concise and accurate
- [ ] Links and references are correct

## Common Errors

### Error 1: [Description]

```diff
- Wrong: incorrect approach
+ Right: correct approach
```

### Error 2: [Description]

```diff
- Wrong: incorrect approach
+ Right: correct approach
```

## Updating Documents

### Status Changes

When a document status changes:
```diff
- **Status**: Draft
+ **Status**: Published
+ **Date**: YYYY-MM-DD (updated date)
```

### Adding Cross-References

When a new document relates to existing documents:
1. Add links to existing documents in the new document
2. Back-link the new document in existing documents

## Directory Structure

[Describe directory organization, e.g., organized by topic with independent numbering per subcategory]

```
[directory-name]/
├── [subdirectory 1]/    # [description]
│   ├── 001-xxx.md
│   └── 002-xxx.md
├── [subdirectory 2]/    # [description]
│   └── 001-xxx.md
└── README.md
```

When creating a new subdirectory, create it and restart numbering from 001 within it.

## File Naming Convention

- [Naming rule 1]
- [Naming rule 2]
- Format: `[format description]`

Examples:
- `001-example-title.md`
- `002-another-title.md`
