# docs — the source of truth (placeholder)

> Installs as `docs/CLAUDE.md`. Keep it a `CLAUDE.md`, not a README, and keep
> it orientation-only: the map below plus a one-line gloss per entry. Add a
> rule here only if working *in this directory* genuinely needs it — the
> control-system rules already live in the files listed below.

Documentation is the source of truth for this project; code is one
implementation of it. This directory holds that truth and the machinery that
keeps it honest.

```
docs/
|-- CLAUDE.md            # this map
|-- PRINCIPLES.md        # the system's design principles — read when designing/reviewing
|-- SPEC.md              # one-paragraph statement of what this project is
|-- WORKFLOW.md          # the human-AI collaboration contract
|-- design_doc_sync.md   # how docs and code are kept in agreement (the 4 tiers)
|-- changelog/           # what changed — one file per design doc, mirroring versions
|-- decisions/           # ADRs — what was considered and why (accepted/rejected)
|-- in_process/          # active plans not yet stable enough to be a design_*.md
|-- audit/               # semantic-drift audit reports (Tier 4)
`-- skill/               # authoring skills — how to write a design doc, a plan, keep docs synced
...
```

The bare `...` line opts this tree out of the completeness check: `design_*.md`
files and domain subtrees land here as they are written. Optional later slots:
`architecture/mechanism_*.md` (the L2 theory plane, `design_doc_sync.md` §7.1)
and `reference/` (imported foreign docs, outside the control system).

Each subdirectory carries its own `CLAUDE.md` explaining its slot.
