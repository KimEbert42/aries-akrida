# AI review records

This folder stores the full text of reviews of this repository (for example the Indicio team review run by
`indicio-team-skill`), so a review keeps a home after the PR that discussed it is merged.

## Convention

- One folder per review, named `yyyymmdd-short-name` (the date the review ran), e.g. `20261030-team-review/`.
- Each review folder has a `README.md` (scope, method, roles, **the commit SHA reviewed**), a `summary.md`
  (synthesis and prioritised action items) and one file per role or reviewer with their output verbatim.
- A review is a snapshot of one commit and is expected to go stale. Do not edit it to track fixes.
- Findings the owner accepts become plans in `ai/plans/future/` (see `ai/plans/README.md`), which link back to the
  finding here.
- No secrets, licence strings, claim values, QR contents or real credential/PII data in review files.
- The plan that produced a review lives in `ai/plans/`; the PR for the review is the place for discussion.
