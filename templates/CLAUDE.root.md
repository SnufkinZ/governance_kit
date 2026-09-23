# Project Context

> **EDIT ME:** replace every `<angle-bracket>` placeholder, then delete this
> line. Keep this file short — it loads into *every* AI session; per-directory
> rules belong in that directory's own `CLAUDE.md`.

<2–4 sentences: what this project is, who it is for, product name vs internal
codename if they differ.>

# Repository Layout

```
<repo>/
|-- BOOTSTRAP.md    # boot ladder — READ EVERY SESSION while it exists
|-- docs/           # source of truth: design docs, changelog, ADRs, in-process plans
|-- scripts/        # docs-code sync gate + bootstrap phase checker
|-- tests/          # test suite; tests/docs/ enforces the documentation contract
|-- CLAUDE.md       # this file
|-- AGENTS.md       # pointer here, for tools that read AGENTS.md instead
...
```

# Working Rules (the control system, condensed)

1. **Boot first.** While `BOOTSTRAP.md` exists at the repo root, read it at the
   start of every session, state the current phase and active relaxations, and
   work within them.
2. **Design before code.** No production code before its design doc exists and
   is approved (`docs/skill/design_template.md`). The doc is the source of
   truth; code implements it.
3. **Ask before deviating.** If a bug or a design flaw makes you want to depart
   from a documented design, surface it and ask the human before changing
   either the code direction or the doc.
4. **Check for existing logic before adding new.** Search the codebase for
   similar functions/mechanisms first; do not add new logic unless necessary.
5. **Docs stay in sync with code — written once, at the end, on command.**
   Read `docs/skill/document_maintenance.md` before coding. While work is in
   progress do not edit design docs, changelogs, or version headers, whatever
   the gate reports (it lists uncommitted debt as DOCS OWED). A change that
   neither adds, removes, nor changes a documented contract (API behavior,
   state semantics, persistence compatibility, or architecture) must not touch
   L2/L3 docs; give its commit a `docs-sync: not-needed` trailer instead. The gate
   (`python scripts/check_docs_sync.py`) enforces the rest.
6. **Evaluate every design proposal against `docs/PRINCIPLES.md`.** If a
   proposal violates a principle, redesign before implementing.
7. **Keep every `CLAUDE.md` lean.** It loads into every session. When editing
   one, add only what changes AI behavior; prefer cutting words over adding
   them, never pad for completeness.

# Documentation References

- Collaboration contract: `docs/WORKFLOW.md`
- Core principles: `docs/PRINCIPLES.md`
- Project spec: `docs/SPEC.md`
- Doc-code sync machinery: `docs/design_doc_sync.md`
- Authoring skills: `docs/skill/`
