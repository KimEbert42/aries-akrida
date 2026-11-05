# Add the `ai/` folder, AGENTS.md and CLAUDE.md

Branch: `feature/ai`
Status: **Completed** (2026-11-05), implemented in commit `3732aff`, pushed to the `kim` remote.

## Goal

Give AI agents (and humans working with them) a consistent home for plans and reviews, and a single
source of truth about how to work in this repo, modelled on `proven-docker`'s `ai/` folder.

## Scope

1. `ai/plans/{future,current,completed,abandoned}/` + `ai/plans/README.md` (convention copied from
   proven-docker: `yyyymmdd-short-name.md`, move with `git mv` as status changes).
2. `ai/review/README.md` (one folder per review, pinned to a commit SHA, never edited afterwards).
3. `AGENTS.md` at the repo root: tool-agnostic instructions (layout, commands, conventions, boundaries).
4. `CLAUDE.md` at the repo root containing only `@AGENTS.md`, so Claude Code loads the same content and
   there is one file to maintain.

## Decisions

- **Branched from `feature/holders`**, not `main`, because `AGENTS.md` documents the holder-agent code
  (`agents/holder/`, `HOLDER_TYPE`) that only exists on that branch. If this should ship independently,
  rebase onto `main` and adjust the holder sections.
- **`CLAUDE.md` uses an `@AGENTS.md` import** rather than a symlink, so it works on any checkout/OS.
- **SOC 2**: `AGENTS.md` carries explicit rules for secrets, change management (signed-off conventional
  commits, PR + CI), authorization to load test, and no real PII/credentials in `ai/` records.

## Out of scope

- Rewriting README/DEVREADME/docs.
- Adding skills, hooks or `.claude/settings.json`.

## Outcome

Delivered as planned: `ai/plans/` (four status folders + README), `ai/review/README.md`, root
`AGENTS.md`, and `CLAUDE.md` (`@AGENTS.md` import). Commit is signed off (DCO) per project rules, and
`AGENTS.md` records that rule.

## Verification

- `AGENTS.md` commands were written from `.github/workflows/ci.yml` and `pyproject.toml`; they were
  not executed as part of this change.
- Paths and loader names referenced in `AGENTS.md` were checked to exist.
- Docs-only change; ruff/tests unaffected and not run.

## Follow-ups

- Fill in the `Debugging` TODO in `DEVREADME.md`.
- Consider a first `ai/review/` of the holder work.
