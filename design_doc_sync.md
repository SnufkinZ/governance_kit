# Documentation-Code Synchronization — Design Document

> **Scope:** The machinery that keeps `docs/` and the code it describes in
> agreement: what is checked, by what mechanism, and where each check lives.
> **Status:** Current
> **Prerequisite:** `WORKFLOW.md`, the document-maintenance skill (`docs/skill/document_maintenance.md`)
> **Code:** `tests/docs/**`, `scripts/check_docs_sync.py`

---

## 0. What this system does, in plain words

This project's core risk is not bad code — it is **documentation that quietly
stops matching the code**. Because design docs are treated as authoritative (the
code is almost their build product), a *wrong* authoritative doc is more dangerous
than no doc: a future contributor, human or AI, trusts it and builds on a false
premise.

The defense is four layers, ordered by how mechanical they are. The cheaper, more
mechanical layers run on every change and catch the common failure; the expensive,
judgement-heavy layer runs periodically and catches what machines cannot:

1. **Structure** — do the maps match the territory? (file trees, links, doc headers)
2. **Contradiction** — does the project contradict its own recorded truth? (a doc says "done" while the board says "to do")
3. **Ownership** — when code changes, did its owning design doc change too?
4. **Semantics** — does the prose still describe what the code actually does?

Layers 1–3 are pure text comparison and live in CI. They cannot read meaning, so
they cannot catch a doc that describes the *wrong mechanism* in fluent,
internally-consistent prose. That is layer 4's job, and it needs a model reading
code and prose side by side — so it is a human-triggered audit, not a blocking
gate.

The recurring failure shape these target: **the source-of-truth doc is correct;
an aggregation layer or a sibling doc lags.** Layers 2 and 4 aim squarely at that.

---

## 1. What counts as "in sync"

| Truth source | Must agree with | Enforced by |
|---|---|---|
| A directory's actual contents | the file tree in its `CLAUDE.md` | Tier 1 |
| A markdown link target | an existing file | Tier 1 |
| An `in_process/` plan | the head-format contract + a Track section | Tier 1 |
| A top-level plan's existence | a row/entry on the priority board | Tier 1 |
| The draft log's structure | the inbox contract in its header | Tier 1 |
| A doc's own `**Status:**` | the priority board's placement of it | Tier 2 |
| A design doc's `**Version:**` | a matching entry in its changelog | Tier 2 |
| A changed code file | a change to its owning design doc | Tier 3 |
| An L3 page's pinned L2 version/hash | the live L2 design doc | Tier 2 (optional; when L3 exists) |
| A design doc's prose | the behavior of the code it owns | Tier 4 (audit) |

---

## 2. Tier 1 — Mechanical structure (`tests/docs/test_doc_consistency.py`, `tests/docs/test_change_log_draft.py`)

Runs in the normal `pytest tests/` suite. Pure filesystem + text checks, no
judgement. Starter implementations of Tiers 1–2 ship with the kit — green in a
fresh install, biting as soon as each convention is first used; extend them as
conventions grow (§7):

- **CLAUDE.md trees match disk** — every listed entry exists; every immediate
  child of the directory is listed (a tree may opt out of the completeness half
  with a bare `...` line). Generated/build directories are pruned. This keeps the
  per-directory maps honest as files come and go.
- **Links resolve** — every relative markdown link under `docs/` points at a real
  file (frozen `archive/` trees exempt).
- **in_process head format** — every plan/problem/change doc carries the standard
  head (`Type/Status/Priority/Date/Owner`) and a `## Track` section.
- **Board coverage** — every top-level plan is referenced on the priority board,
  so no plan silently falls off the radar.
- **Draft-log inbox contract** — the change-log draft is an inbox, not a journal:
  dated batches only, each leading with a `Docs:` line, consumed batches deleted,
  a size cap that forces an overdue docs pass.

Adding, renaming, or moving a file fails Tier 1 until the maps are updated. This
is the layer that makes "update the CLAUDE.md" a hard requirement, not a hope.

## 3. Tier 2 — Contradiction (`tests/docs/test_doc_contradictions.py`)

Compares two places that state the same fact and fails when they disagree:

- **Status vs. board** — a doc whose head Status is terminal (Implemented /
  Completed / Superseded) may not still own a row in the board's *active* table,
  and vice-versa.
- **Version ↔ changelog** — if a `design_*.md` declares `**Version:** X`, a
  changelog file for it must record an entry for `X`. Catches a bumped header with
  no changelog entry, or a stale header left after content moved on.

Tier 2 does **not** read meaning. It only checks that facts written in two places
agree.

### 3.1 L2↔L3 freshness pin (optional — add when L3 exists)

The human-intuition layer (L3) retells an L2 design doc. It shares the hazard of
any aggregation layer — it silently rots when the source moves — so it gets the
same defense one edge higher: each L3 page **pins the L2 source version/hash it
aligned to** in its frontmatter, and a test fails when the source advances past
the pin. **The acknowledgment is the freshness guarantee:** a red pin means the
source moved; the fix is to re-read the diff and bump the pin (the "I looked,
still accurate" stamp) or fix the page first. Either way a human/AI looks once per
L2 change — O(1) per change. Do not add this tier until L3 exists (`BOOTSTRAP.md`
R0.2).

## 4. Tier 3 — Ownership gate (`scripts/check_docs_sync.py`)

A CI job (needs the base ref to diff). Each design doc may declare the code it
owns via a header line:

```
> **Code:** `src/module/**`
```

The script builds the `code-glob → owning-doc` map from these lines, diffs the
change range, and for every changed code file that has an owner, requires **at
least one** owner doc to be touched in the same range. The gate is a checklist
prompt, not proof of correctness — touching the doc satisfies it; whether the edit
is *right* is Tier 4's concern.

**Glob semantics are directory-aware.** In an ownership glob, `*` and `?` do not
cross `/`; only `**` does. This is stricter than `fnmatch` (where `*` matches `/`
and lets one doc's glob leak into another's territory). Pinned by
`tests/docs/test_ownership_gate.py`.

**Scope is self-governing.** The script's `CODE_SCOPES` lists the roots that
require an owner; `tests/docs/` and `scripts/` are in scope so the sync system
governs its own implementation. Adjust `CODE_SCOPES`/`CODE_EXEMPT_PREFIXES` per
repo.

**Bypass is explicit and audited.** A genuinely doc-neutral change (refactor,
typo, test-only) adds a `docs-sync: not-needed` trailer line to a commit message
in the range. The trailer *is* the audit trail — silent bypass is impossible.

**Coverage grows monotonically.** A code path with no owner is reported as "no
owner yet" — informational, not blocking. As docs adopt ownership lines, coverage
grows; the gate never forces a doc to exist before its design has landed.

**Boot note:** in Phase 0 the gate runs `--warn-only` (reports, does not fail).
It flips to blocking at Phase 0→1 graduation (`BOOTSTRAP.md` R0.1).

Run locally before pushing: `python scripts/check_docs_sync.py` (`--warn-only` to
report without failing, `--json` for the ownership map).

## 5. Tier 4 — Semantic audit (a model-run audit)

The first three tiers cannot detect a doc that is structurally perfect and
factually self-consistent but **describes the wrong mechanism**. Catching that
requires reading code and prose together and judging whether they agree — model
work, not regex work. Run it at milestones (it costs model time and reads diffs).

A ready-to-run runbook ships with the kit and installs as a Claude Code skill
at `.claude/skills/doc-audit/SKILL.md` (kit source:
`templates/doc-audit-SKILL.md`); on another agent harness, use it as a plain
audit prompt. The method it encodes:

1. Resolve the audit range (default: since the last audit entry in `docs/audit/`).
2. Use `scripts/check_docs_sync.py --json` to get the `code ↔ owning-doc` pairs
   touched in range.
3. For each pair, read the changed code and the doc's relevant sections; look for
   **semantic drift**: a mechanism, field, default, signature, or invariant the
   code no longer implements.
4. Cross-check aggregation layers the mechanical tiers can't judge.
5. Write findings to `docs/audit/<date>.md` — location, the drift, the evidence
   (code vs. doc), a suggested reconciliation. The audit **reports**; it does not
   silently rewrite design docs.

Findings become doc edits (or in-process items) by a human — keeping authoritative
docs under human control while the model does the expensive cross-reading.

---

## 6. How the tiers fit together

```
every change ──► Tier 1 (structure)     ┐
             ──► Tier 2 (contradiction) ├─ pytest tests/  ── blocking, free
             ──► Tier 3 (ownership)     ┘  + CI gate job (warn-only in Phase 0)

milestone   ──► Tier 4 (semantics)      ── model-run audit ── human-triggered
```

Mechanical layers run constantly and catch the cheap, common failures so the
expensive layer is not wasted on them. Each tier's failure message names the fix,
turning "keep docs in sync" from a discipline that erodes under deadline pressure
into a checklist with a backstop.

The principle alignment: this whole system is **narrow interfaces + rich state
reading** (`PRINCIPLES.md`) applied to documentation — the checks read rich
existing state (file trees, Status fields, Version headers, git diffs) through
narrow, stable contracts (the head format, the `> **Code:**` line), rather than
imposing new authoring ceremony.

---

## 7. Extending the system

- **New mechanical invariant** → add a test to `tests/docs/`. Fail with a message
  that names the exact file and fix.
- **New design doc** → add a `> **Code:**` line if it owns code, so Tier 3 covers
  it. Omit the line for pure contract/index docs.
- **New aggregation doc** → if it restates facts owned elsewhere, add a Tier 2
  contradiction check for it.
- **Tuning** scope roots or the bypass trailer text → change the constant in the
  script/test; keep it single-sourced.
