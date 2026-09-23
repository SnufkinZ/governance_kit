# In-Process Docs (placeholder)

> Installs as `docs/in_process/CLAUDE.md`. Keep it a `CLAUDE.md`, not a README.
> One companion file installs alongside this one (shipped in this folder as
> `in_process__priority.md`): `priority.md` — the priority board.

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
- **While coding, no doc journal:** the uncommitted diff is the record of *what*
  changed. Only the *why* and what was deliberately left open go into the
  owning plan doc (or an ADR); design docs are written once, at the end, on
  command (`../skill/document_maintenance.md`).

Empty for now — present from day one so the AI separates *plans* from
*contracts* from *history* from the start (BOOTSTRAP.md axiom A2).
