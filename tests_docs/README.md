# tests_docs — the mechanical checks (Tiers 1–3 unit tests)

These files install as `tests/docs/` in the target repo (the installer also
creates the required empty `__init__.py`). Together with
`scripts/check_docs_sync.py` they are the *mechanical* half of the control
system — see `design_doc_sync.md` for what each tier means.

| File | Tier | What it pins |
|---|---|---|
| `test_doc_consistency.py` | 1 | CLAUDE.md file trees match disk; relative links under `docs/` resolve; in_process docs carry the standard head + Track section; every plan is on the priority board. |
| `test_change_log_draft.py` | 1 | The draft log obeys its inbox contract (dated batches, `Docs:` lines, consume = delete, size cap). |
| `test_doc_contradictions.py` | 2 | A doc's own Status vs the board; board snapshot freshness; `**Version:**` header vs changelog entry. |
| `test_ownership_gate.py` | 3 | The gate's pure functions: glob semantics (`*` does not cross `/`, `**` does), scope rules, bypass-trailer matching. |

## Portability

- **Run these after install, not in place.** Each file resolves the repo root
  as `parents[2]` of its own path, i.e. it assumes it lives at
  `<repo>/tests/docs/`. Inside the kit folder that resolution is wrong by
  design.
- All checks are **vacuously green in a fresh install** and start biting as
  soon as the convention they guard is first used (first plan doc, first
  versioned design doc, first draft-log batch).
- The only fixtures tied to porting constants are marked `PORT` in
  `test_ownership_gate.py` — if you edit `CODE_SCOPES` /
  `CODE_EXEMPT_PREFIXES` in `scripts/check_docs_sync.py`, mirror the edit
  there. Everything else is layout-neutral.

## Extending (this is expected, not exceptional)

These are *starters*. The origin project grew several more checks on top of
them (L2↔L3 freshness pins, CLI-skill lockstep, design-token rules). The
pattern for every new mechanical invariant:

1. State the invariant as "X must agree with Y".
2. Add a test to `tests/docs/` that fails with a message naming the exact
   file and the exact fix.
3. If the invariant guards new code, keep that code inside `CODE_SCOPES` so
   the gate governs it too.
