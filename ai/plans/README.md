# AI plan documents

This folder holds plan documents written by AI agents (or humans, working with an agent) for
non-trivial pieces of work — the kind of thing that would otherwise live in a chat log or a
scratch file scattered somewhere on one person's machine.

## Convention

- `future/` — plans for work that hasn't started yet (proposed/queued).
- `current/` — plans for work that's actively in progress.
- `completed/` — move a plan here once the feature/bug it covers ships. This preserves the
  reasoning and context behind the change even after the work is done, in case it's useful later
  (e.g. work gets revisited, or someone needs to understand why a decision was made).
- `abandoned/` — plans that were started and then explicitly dropped. Keeping these visible lets
  us see what wasn't worth pursuing, instead of silently deleting the record.

When a plan's status changes, move the file to the matching folder (`git mv`) rather than copying
or deleting it — e.g. `future/` → `current/` when work starts, then `current/` → `completed/` or
`abandoned/`.

### File naming

Name each plan `yyyymmdd-short-name.md`, where the date is when the plan was written (not when
work started or finished) — e.g. `20260924-wallet-rekey-flow.md`. Keep `short-name` a few
hyphenated words, no need to restate the folder it's in.

These documents are expected to go stale — code and reality move faster than plans. That's fine;
they're a reference for "what was the thinking at the time," not living documentation.

This complements issue tracking (ClickUp/JIRA), it doesn't replace it.
