# AGENTS.md — vicat-home-bus

## What this repo is

A centralized configuration hub ("homebus") for managing OpenCode skills and workflows via APM (Atmosphere Package Manager). Despite the `python/` parent directory name, this is **not** a Python project — it contains no application code, no `requirements.txt`, no `pyproject.toml`, and no build system.

## Key directories

| Path | Purpose | Managed by |
|------|---------|------------|
| `apm.yml` / `apm.lock.yaml` | APM dependency manifest and lockfile | APM CLI |
| `.opencode/skills/` | Installed OpenCode skills | APM (do not edit files owned by lockfile entries) |
| `.opencode/command/` | Custom `/opsx-*` commands (propose, apply, archive, explore) | repo-local |
| `openspec/` | OpenSpec workflow (schema: `spec-driven`, config at `openspec/config.yaml`) | `openspec-cn` CLI |
| `apm_modules/` | APM dependency cache | APM (gitignored) |
| `tmp/` | Temporary workspace | manual |

## Commands

```bash
apm install          # sync skills from apm.yml
openspec-cn list     # list active OpenSpec changes
openspec-cn status --change "<name>" --json
```

## OpenSpec workflow

This repo uses OpenSpec with schema `spec-driven` (configured in `openspec/config.yaml`). Custom slash commands invoke the workflow:

- `/opsx-propose <name>` — create a new change with proposal, design, and tasks
- `/opsx-apply <name>` — implement tasks from a change
- `/opsx-archive <name>` — finalize a completed change

The `openspec-cn` CLI is the Chinese-localized variant. All output to users should be in **Simplified Chinese**.

## Skill ownership

Skills listed in `apm.lock.yaml` with `active_owner` fields are managed by APM and deployed from the `home-vicat-skills` repo. Do not manually edit these files — they will be overwritten on the next `apm install`. Local-only skills (e.g., `openspec-*`) under `.opencode/skills/` can be edited freely.

## Record-* skill conventions

All documentation created by `record-*` skills uses YAML frontmatter with required fields: `status`, `created`, `updated`, `author`, `tags`, `related`. Each document type has its own status values (e.g., ADR uses `proposed → accepted → implemented`, research uses the full `draft → in-progress → in-review → complete` lifecycle). See `doc-structure/SKILL.md` for the authoritative spec and dependency graph.

## No build/test/lint

There is no code to build, test, or lint in this repo.
