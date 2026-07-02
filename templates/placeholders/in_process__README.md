# In-Process Docs (placeholder)

> Rename to `docs/in_process/CLAUDE.md` (or keep a README) in the target repo.
> Two companion files install alongside this one (shipped in this folder as
> `in_process__priority.md` and `in_process__change_log_draft.md`):
> `priority.md` — the priority board — and `change_log_draft.md` — the
> draft-log inbox.

This directory holds **active planning documents** — things being decided,
designed, or implemented but not yet stable enough to live in a `design_*.md`.
Once a plan is implemented and its design docs are synced, the plan moves to
`docs/changelog/` or is deleted. **A plan is temporary scaffolding, not a
permanent record** — never leave a plan and a design doc both describing the same
contract (the design doc is authoritative).

- **What to do next:** `priority.md` — single source of truth for active
  prioritization. Every top-level `plan_*`/`problem_*` doc must be referenced
  there (Tier 1 enforces this).
- **How to write a plan doc:** `../skill/in_process_plan_format.md` — standard
  head (`Type/Status/Priority/Date/Owner`) + append-only `## Track` section
  (Tier 1 enforces this).
- **Raw facts while coding:** `change_log_draft.md` — an inbox, not a journal;
  its header comment carries the contract (Tier 1 enforces this).

Empty for now — present from day one so the AI separates *plans* from
*contracts* from *history* from the start (BOOTSTRAP.md axiom A2).
