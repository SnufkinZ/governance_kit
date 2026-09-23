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

Layers 1–3 are pure text comparison and run in an **independent Docs
workflow** (`templates/docs.example.yml`). Docs may report failure, but that
result is not a direct dependency of runtime build/deploy workflows. Making
Docs a required PR check can still prevent merging and indirectly delay a
release; choose that branch policy deliberately. They cannot read meaning,
so they cannot catch a doc that
describes the *wrong mechanism* in fluent, internally-consistent prose. That is
layer 4's job, and it needs a model reading code and prose side by side — so it
is a human-triggered audit, not a deployment gate.

The recurring failure shape these target: **the source-of-truth doc is correct;
an aggregation layer or a sibling doc lags.** Layers 2 and 4 aim squarely at that.

---

## 1. What counts as "in sync"

| Truth source | Must agree with | Enforced by |
|---|---|---|
| A directory's actual contents | the file tree in its `CLAUDE.md` | Tier 1 |
| A control directory's existence | a `CLAUDE.md` map inside it (not a README) | Tier 1 |
| A markdown link target | an existing file | Tier 1 |
| An `in_process/` plan | the head-format contract + a Track section | Tier 1 |
| A top-level plan's existence | a row/entry on the priority board | Tier 1 |
| A doc's own `**Status:**` | the priority board's placement of it | Tier 2 |
| A design doc's `**Version:**` | a matching entry in its changelog | Tier 2 |
| A changed code file | a change to its owning design doc | Tier 3 |
| A path-shaped `> **Code:**` token | at least one live file | Tier 3 unit test |
| An L3 page's pinned L2 hash | the live L2 source | Tier 2 (optional; when L3 exists) |
| An L3 page pinning a design doc | the mechanism doc that contract implements, pinned too | Tier 2 (optional; when L3 and a mechanism doc exist) |
| A design doc's prose | the behavior of the code it owns | Tier 4 (audit) |

---

## 2. Tier 1 — Mechanical structure (`tests/docs/test_doc_consistency.py`)

Runs as `pytest tests/docs/` in the Docs workflow; keep it out of the runtime
test job so documentation debt stays visible without failing application CI.
Pure filesystem + text checks, no judgement. Starter implementations of Tiers 1–2 ship with the kit — green in a
fresh install, biting as soon as each convention is first used; extend them as
conventions grow (§7):

- **CLAUDE.md trees match disk** — every listed entry exists; every immediate
  child of the directory is listed (a tree may opt out of the completeness half
  with a bare `...` line). Generated/build directories and imported external
  reference material under `docs/reference/` are pruned. This keeps the
  per-directory maps honest as files come and go.
- **Control directories carry a CLAUDE.md** — the two checks above keep an
  *existing* map accurate but say nothing about a directory that has none. The
  coverage check closes that gap: each directory in `REQUIRED_CLAUDE_DIRS`
  (docs/, its control subtrees, and each ported code root) must contain a
  `CLAUDE.md` — a README does not satisfy it, because `CLAUDE.md` is the file
  the AI auto-loads. Listing a not-yet-created directory is a no-op, so
  coverage grows as directories appear.
- **Links resolve** — every relative markdown link under `docs/` points at a real
  file (frozen `archive/` trees and imported `reference/` material exempt).
- **in_process head format** — every plan/problem/change doc carries the standard
  head (`Type/Status/Priority/Date/Owner`) and a `## Track` section.
- **Board coverage** — every top-level plan is referenced on the priority board,
  so no plan silently falls off the radar.

Adding, renaming, or moving a file fails Tier 1 until the maps are updated. This
is the layer that makes "update the CLAUDE.md" a hard requirement, not a hope.

## 3. Tier 2 — Contradiction (`tests/docs/test_doc_contradictions.py`)

Also in the Docs workflow. Compares two places that state the same fact and
reports failure when they disagree:

- **Status vs. board** — a doc whose head Status is terminal (Implemented /
  Completed / Superseded) may not still own a row in the board's *active* table,
  and vice-versa.
- **Version ↔ changelog** — if a governed `design_*.md` declares `**Version:** X`, a
  changelog file for it must record an entry for `X`. Catches a bumped header with
  no changelog entry, or a stale header left after content moved on.

Tier 2 does **not** read meaning. It only checks that facts written in two places
agree.

### 3.1 L2↔L3 freshness pin (optional — add when L3 exists)

The human-intuition layer (L3) retells an L2 source. It shares the hazard of any
aggregation layer — it silently rots when the source moves — so it gets the same
defense one edge higher: each L3 page **pins the L2 sources it aligned to** in
its frontmatter, by **content hash** (e.g. the first 12 hex of sha256 over the
source's bytes), and a test fails when a source advances past its pin. Do not add
this tier until L3 exists (`BOOTSTRAP.md` R0.2).

```yaml
l3_sources:
  - { doc: docs/design_auth.md, hash: "8f04c1a2b9d3" }
```

**Pin by hash, not by version.** Nothing forces a `**Version:**` bump when a
design doc's prose changes, so a version pin stays green across unbumped content
edits — the exact blindness the pin exists to prevent. The hash always moves
with content. If pages also show a human-facing version label, have the test
require the source's *live* version in it, so "pin bumped, label left stale"
fails too.

**The acknowledgment is the freshness guarantee — and lying to it is cheaper
than telling the truth unless the truth has a cheap path.** A red pin means the
*source moved*, not necessarily that the page is wrong. Exactly one of three
paths must be taken:

1. **Still accurate** → bump the pin. The bump alone is the "I looked, still
   accurate" stamp — a bypass that exists only on the record.
2. **Drifted** → fix the page, then bump.
3. **Cannot afford the re-alignment now** → declare the debt: add a stale marker
   (e.g. `l3_stale: "<what is missing, against which source version>"`) to the
   frontmatter and leave the pin **unbumped**. A stale page is exempt from pin
   checks; the marker — not a rubber-stamped pin — carries the truth until the
   debt is paid. Without this honest cheap exit, pages that mirror a fast-moving
   source go red on nearly every change and the observed failure mode is agents
   bumping pins they never verified.

Either way a human or AI looks once per L2 change — O(1) per change. The prose
drift a hash bump cannot see (a wrong explanation stamped as verified) is Tier
4's job, extended to the L2↔L3 edge.

**Mechanism companions — L3 must reference both L2 planes.** When a design doc
has a mechanism companion (§7.1), a page that retells the contract but not the
mechanism teaches the *what* and silently drops the *why*. So the pin test
requires both: if a page pins a design doc that has a companion, the companion
must be pinned too. The edge is read from the mechanism doc's own header line
(`> **Engineering Contract:** `docs/design_x.md``) — the `> **Code:**` trick one
layer up. The rule is one-way (a page may retell a mechanism doc alone, never a
contract alone) and is **not** waived by the stale marker, which declares that
content lags a source, not permission to omit one.

## 4. Tier 3 — Ownership gate (`scripts/check_docs_sync.py`)

A separate Docs-workflow job (needs the base ref to diff). Each design doc may
declare the code it owns via a header line:

```
> **Code:** `src/module/**`
```

The script builds the `code-glob → owning-doc` map from these lines, diffs the
change range, and for every changed code file that has an owner, requires **at
least one** owner doc to be touched in the same range. The gate is a checklist
prompt, not proof of correctness — touching the doc satisfies it; whether the edit
is *right* is Tier 4's concern. Docs under `docs/skill/` (templates with example
`> **Code:**` lines), `docs/archive/`, and `docs/reference/` (imported foreign
design docs) are excluded from ownership discovery (`DOC_CONTROL_EXCLUDE`). A
foreign doc's globs describe another repository, but overlapping paths such as
`backend/api/**` may exist here too — admitting it would create a satisfiable
co-owner that absorbs violations meant for the local owning doc.

**Glob semantics are directory-aware.** In an ownership glob, `*` and `?` do not
cross `/`; only `**` does. This is stricter than `fnmatch` (where `*` matches `/`
and lets one doc's glob leak into another's territory). Pinned by
`tests/docs/test_ownership_gate.py`.

**A claim that matches nothing is worse than no claim.** A `> **Code:**` token
naming a directory (`src/pkg/`) is not a glob and owns zero files — and because
an unowned file cannot owe a document, the gate reports no violation *because*
the claim is empty. The doc looks like it governs a package while governing
nothing, and the green result is indistinguishable from real coverage. Every
token containing `/` must therefore match at least one live file (tracked, or
untracked but not ignored — so a final doc pass may claim a new file before
staging it); `tests/docs/test_ownership_gate.py` enforces this. Tokens without a
directory component are exempt: a `> **Code:**` line may name bare filenames in
explanatory prose.

**Scope is self-governing.** The script's `CODE_SCOPES` lists the roots that
require an owner; `tests/docs/` and `scripts/` are in scope so the sync system
governs its own implementation. Adjust `CODE_SCOPES`/`CODE_EXEMPT_PREFIXES` per
repo.

**Bypass is explicit, audited, and commit-scoped.** A genuinely doc-neutral
change (refactor, typo, test-only — see the design-impact threshold in
`docs/skill/document_maintenance.md`) adds a `docs-sync: not-needed` trailer to
the commit that carries it. The trailer must be a full line of the message (a
mid-line prose mention does not count), and it waves only files touched
**exclusively** by trailer-carrying commits: a file also touched by a plain
commit stays gated, and staged/working-tree changes belong to no commit, so no
trailer can vouch for them. (A range-global bypass was tried and retired: one
early legitimate trailer silently absorbed every later violation on the
branch.) The trailer *is* the audit trail — it records that someone judged
*that commit's* change to have no design impact. Silent bypass is impossible.

**Merge commits own their additional edits.** The commit manifest uses combined
merge diffs: a path whose result differs from every parent counts as touched
by the merge itself, including conflict resolutions and files introduced while
merging. Without a trailer on that merge, an earlier trailer cannot waive those
edits. A path inherited unchanged from a parent retains its source commits'
obligations and trailers, so a clean merge does not revoke a valid waiver. A
trailer on the merge never waives a plain source commit's changes.

**Work in progress is reported, not blocked.** A violating file whose changes
exist *only* in the working tree is listed under **DOCS OWED** and the run exits
0. Otherwise the gate would fire at the one moment its instruction is wrong: a
design doc is written once, when the change is final
(`document_maintenance.md`), but a dirty tree is by definition unfinished — so
failing there pushes an agent into documenting code that is still moving. The
debt is deferred, never waived: the file re-enters the range as a hard violation
the moment it is committed, and a file that is both committed and further edited
stays a hard violation throughout. This differs from the trailer — the trailer
is a permanent judgement that no doc change is needed; DOCS OWED is a timing
deferral that expires at the next commit.

**Coverage grows monotonically.** A code path with no owner is reported as "no
owner yet" — informational, not blocking. As docs adopt ownership lines, coverage
grows; the gate never forces a doc to exist before its design has landed.

**Boot note:** in Phase 0 the gate runs `--warn-only` (reports, does not fail).
It flips to blocking at Phase 0→1 graduation (`BOOTSTRAP.md` R0.1).

Run locally before pushing: `python scripts/check_docs_sync.py` (`--warn-only` to
report without failing, `--json` for the ownership map; the JSON pairing is
unfiltered and reports owed and bypassed files as violations, since an audit
wants the full set).

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
             ──► Tier 2 (contradiction) ├─ Docs workflow ── visible report, free
             ──► Tier 3 (ownership)     ┘  (warn-only in Phase 0) — no build/deploy dependency

runtime change ──► runtime CI ──► build ──► deploy   (does not wait on Docs)

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
- **New mechanism doc** (`docs/architecture/mechanism_*.md`) → see §7.1. Give it
  a `> **Engineering Contract:**` line naming the design doc it governs, and no
  `> **Code:**` line — theory owns no code by construction.
- **Imported foreign docs** → put them under `docs/reference/` (or another
  subtree listed in `DOC_CONTROL_EXCLUDE`) so their maps, links and ownership
  lines stay outside the local control system.
- **New aggregation doc** → if it restates facts owned elsewhere, add a Tier 2
  contradiction check for it.
- **Tuning** scope roots or the bypass trailer text → change the constant in the
  script/test; keep it single-sourced.

### 7.1 L2 on two planes — which design docs get a mechanism companion

L2 may run on two planes, both full authority, neither outranking the other: a
`design_*.md` owns the **engineering contract** (names, shapes, formulas, phase
order, status, deferred seats); a `docs/architecture/mechanism_*.md` owns the
**durable theory and invariants** that contract implements — what stays true
when the implementation is replaced. They are kept apart so theory does not
bloat the contract and code churn does not drag the theory.

**A mechanism doc is optional, and most design docs will never have one.** A
design doc standing alone is complete, not in debt — it keeps its own reasons,
and a sentence or two of rationale beside each contract is normal and healthy.
Absence of a companion is never a finding. The class is the project's few
**foundational mechanisms** whose theory constrains everything built on them;
platform and adapter contracts are outside it by nature. Within that class, a
split is worth making when the theory:

- **spans several code modules or design docs**, so no single contract is its
  natural home;
- contains **causal structure independent of the current implementation** — it
  would survive a rewrite;
- **judges future designs**, functioning as a standing test of adequacy rather
  than a record;
- has grown large enough that leaving it in place would **drown the contract**;
- has a **clean ownership boundary** — one nameable mechanism, not a theme;
- is **settled**, not this sprint's plan.

The costs a split must be worth: a second doc to keep true, an extra hop for a
reader, and (once L3 exists) a mandatory extra source on every L3 page that
retells the contract (§3.1). Two failure modes to name: theory that stays in the
design doc when it should split (the contract slowly becomes a treatise), and a
mechanism doc created before the theory is settled (a discussion draft wearing
L2 authority).

The split is one-way for code: ownership discovery (§4) reads `design_*.md`
only, so theory generates no Tier 3 pressure and a refactor can never force a
theory edit. **Optional to create; binding once created** — whether a companion
exists is judged here; whether L3 must reference an existing one is enforced
(§3.1).
