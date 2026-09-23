# BOOTSTRAP — the temporary boot file for a doc-driven, AI-controlled project

> **Read this every session until it is deleted.** While this file exists, it
> overrides nothing in the permanent rules — it *adds* new-project relaxations on
> top of them and tells you when to remove each relaxation.
>
> **Status:** ACTIVE — the project is still standing up its control system.
> **Current phase:** 0 — Design skeleton (each tightening action in §3 updates
> this line; the remaining R-clauses below are the ground truth it summarizes)
> **Deletes itself when:** Phase 2 graduation completes (see §0 and §4).

---

## 0. What this file is, and how it ends

This project runs on a permanent control system — documentation is the source of
truth, code is one implementation of it, mechanical checks catch drift. That
system (`WORKFLOW.md`, `PRINCIPLES.md`, `design_doc_sync.md`, the gate, the doc
tests) is a **permanent immune system**. It never retires.

**This boot file is the only temporary part.** Its job is to hold the
*relaxations* that make sense only while the project is small — and to convert
each one into a permanent rule as the project matures. Boot does **not** "build
the system then get thrown away." Boot **graduates**:

> Each phase names what is temporarily relaxed, the condition that ends the
> relaxation, and the permanent file the rule moves into when it is tightened.
> When no relaxation is left, this file equals `WORKFLOW.md` in spirit and is
> **deleted** — its mission complete.

So "deprecating boot" = every temporary clause has been promoted to permanent
and the steady-state docs now carry the whole load. Not before.

---

## 1. The axioms — true from line one, never relaxed by any phase

These are **not** phased. They hold on the project's first day and forever. If a
phase below ever seems to contradict one of these, the axiom wins.

**A1 — Design before code.** No production code is written before the design doc
that specifies it exists and is approved. The doc is the source of truth; the
code is its implementation. This is the whole premise; relaxing it in "phase 0
to move fast" would teach the AI the wrong habit at the moment it is cheapest to
teach the right one. Two clarifications, not exceptions: a bug fix *inside* an
already-approved design needs no new doc (`WORKFLOW.md` §4.2 — unless the fix
touches the design, which sends it back through design first); throwaway
spikes/experiments may explore ahead of a doc, but nothing they produce is
promoted into production code until its design doc exists.

**A2 — The control loop's *shape* is visible from day one.** Even when a
directory is empty, it exists with a placeholder that states what it is for. The
AI must be able to see the *whole* loop — changelog, decisions (ADR), in-process
plans, skills — from the first session, so it never makes a decision the loop was
meant to capture (e.g. an architectural choice with no ADR) simply because the
slot "didn't exist yet."

**A3 — No island mechanisms, no silent doc skips.** A change that touches a
documented contract updates that contract in the same change, or records on the
commit line why it did not. (This is enforceable by the gate the moment Tier 3
is switched to blocking; until then it is a discipline you still follow.)

**A4 — Verify on signal, not on schedule.** The human drops into code only when a
signal fires (anomaly, audit finding, contradictory AI explanations, a new
principle, a cross-cutting change). Routine "let me check what the AI did" is
discouraged even during boot.

---

## 2. Day-zero setup (do this once, before any feature code)

> **Skip check:** if `docs/WORKFLOW.md` already exists in this repo, day-zero
> was done (the installer ran) — go straight to §3. Only revisit step 2 if any
> file still carries unedited `<angle-bracket>` or EDIT-ME placeholders.

This realizes A2: stand up the skeleton so the loop is visible even when empty.

1. **Install the permanent core** — one command copies everything to its
   MIGRATION.md path (never overwriting):
   ```
   python governance-kit/scripts/install.py <new-repo-root>
   ```
   This lands the contract docs (`WORKFLOW.md`, `PRINCIPLES.md`,
   `design_doc_sync.md`), the gate + phase checker (`scripts/`), the doc tests
   (`tests/docs/`, green out of the box), the authoring skills (`docs/skill/`),
   the Tier 4 audit skill (`.claude/skills/doc-audit/`), a starter root
   `CLAUDE.md`, and the skeleton below:
   ```
   docs/
   |-- CLAUDE.md              # placeholder map of docs/
   |-- PRINCIPLES.md          # EDIT: replace the second principle for your domain
   |-- SPEC.md                # EDIT: 1 paragraph — what this project is
   |-- WORKFLOW.md
   |-- design_doc_sync.md
   |-- changelog/CLAUDE.md    # placeholder map — "change history lives here"
   |-- decisions/CLAUDE.md    # placeholder map + ADR template — "rejected/major choices"
   |-- in_process/CLAUDE.md   # placeholder map + priority.md
   |-- audit/CLAUDE.md        # placeholder map — "semantic-drift audit reports"
   `-- skill/CLAUDE.md        # placeholder map + the authoring templates
   ```
   Empty is fine. The **placeholder text is the point** — it teaches the AI the
   slot's purpose before there is content. Every directory's map is a
   `CLAUDE.md` (the file the AI auto-loads), never a README — a Tier 1 test
   pins that each control directory carries one.

2. **Edit the placeholders** the installer names: root `CLAUDE.md` (project
   context + repo tree), `docs/SPEC.md`, `PRINCIPLES.md` §2, and the two PORT
   constants in `scripts/check_docs_sync.py`. Add a per-directory `CLAUDE.md`
   to each code directory as it appears: an annotated file tree (one line per
   entry saying what it is) plus point-of-use rules *only if that directory
   needs them* — most maps are orientation-only. Add each new code root to
   `REQUIRED_CLAUDE_DIRS` in `tests/docs/test_doc_consistency.py` so the
   coverage test guards it.

3. **Author the first design doc** for the first module *before its code*, using
   `docs/skill/design_template.md`. Add its `> **Code:**` line.

4. **Wire the Docs workflow** (`--with-ci` at install time, or copy
   `templates/docs.example.yml` by hand): an independent workflow that runs
   `pytest tests/docs/` (Tiers 1–2) and `python scripts/check_docs_sync.py
   --warn-only` (Tier 3 in report-only mode — see Phase 0). It stays separate
   from runtime CI: build/deploy workflows do not depend on the Docs result.

---

## 3. The maturity ladder

Each phase = a set of relaxations + a graduation condition + the tightening action.

### Phase 0 — Design skeleton (you are here at project start)

- **Axioms in force:** A1–A4 (design-first is absolute; skeleton is placeheld).
- **Relaxations active now:**
  - **R0.1 — Tier 3 gate runs `--warn-only`.** It reports "code changed without
    its owning doc" but does not fail the build. *Why:* early churn is heavy and
    the doc set is tiny; a blocking gate now costs more than it catches.
    **First would-have-blocked event:** none yet — the first time the warn-only
    gate reports a real violation, record it here as `YYYY-MM-DD — <one line>`;
    `check_bootstrap_phase.py` reads this line for graduation signal (c).
  - **R0.2 — L3 human-intuition layer (docs website) is not built and not
    placeheld.** *Why:* with few design docs, a human still reads L2 directly;
    the website/bilingual/pin machinery is pure cost with no reader yet. This is
    the one part of the loop that is legitimately deferred, not just relaxed.
  - **R0.3 — Tier 4 semantic audit is ad hoc**, run only if something smells
    wrong, not on a cadence.
- **Still fully on:** A1 (design before code), A2 (skeleton visible), Tier 1
  (structure tests), Tier 2 (contradiction tests) for the docs that exist.
- **Graduation → Phase 1 when:** `python scripts/check_bootstrap_phase.py`
  passes: (a) ≥ 3 design docs carry a `> **Code:**` line, (b) the doc tests and
  the gate are wired (`tests/docs/` + `scripts/check_docs_sync.py` present, and
  green in CI), (c) the R0.1 clause above records at least one
  would-have-blocked event (proof the gate is wired to real ownership).
- **Tightening action (write it into the record):**
  - Flip Tier 3 to **blocking** (drop `--warn-only` in the Docs workflow, so
    a violation turns it red; optionally make it a required PR check). It
    is not a direct build/deploy dependency; a required PR check can still
    prevent merging and indirectly delay a release. → removes R0.1.
  - Delete the R0.1 clause from this file.
  - Set the header's **Current phase** to `1 — Skeleton in place`.

### Phase 1 — Skeleton in place

- **Relaxations active now:** R0.2 (no L3 yet), R0.3 (audit ad hoc).
- **Now on:** blocking Tier 3 gate; Tiers 1–2; A1–A4.
- **Graduation → Phase 2 when:** *a human judgment, not a script* — "I am
  starting to find L2 design docs hard to hold in my head; I want a patient,
  human-facing retelling." That subjective signal is the honest trigger for L3;
  do not fake a metric for it.
- **Tightening action:**
  - Stand up the L3 layer (a docs website) **and** its freshness pin test
    (`design_doc_sync.md` §3.1). → removes R0.2.
  - Put Tier 4 (the `/doc-audit` skill, installed at
    `.claude/skills/doc-audit/`) on a real cadence (e.g. per milestone). →
    removes R0.3.
  - Set the header's **Current phase** to `2 — Mature`.

### Phase 2 — Mature (all relaxations gone)

- **Relaxations active now:** none.
- The steady-state system is fully on: Tiers 1–4, L3 layer with pins, the trust
  model, the ADR/changelog/in-process separation.
- **Final action — retire boot:**
  1. Confirm every relaxation clause above has been removed.
  2. Verify `WORKFLOW.md` now describes the full running system with nothing
     deferred to "boot."
  3. **Delete the boot artifacts — and only them:** `BOOTSTRAP.md`,
     `scripts/check_bootstrap_phase.py`, the "Boot first" rule in the root
     `CLAUDE.md`, and a vendored `governance-kit/` folder if one was copied
     into this repo. Record the deletion in `docs/changelog/`.
  4. **Everything else the kit installed is a permanent organ — do not "clean
     it up" as scaffolding:** the `docs/skill/` templates (used for every new
     design doc and plan), the `/doc-audit` skill (Tier 4 runs for the life of
     the project), `docs/decisions/ADR-template.md`, the placeholder READMEs
     (they graduate into real content as their directory fills — signage, not
     scaffolding), `priority.md` (a live working file), the gate, and
     `tests/docs/`. The immune system remains; its
     training wheels are gone.

---

## 4. Graduation is machine-checkable where it can be

Phase 0→1 rests on countable signals, so it is a script, not a vibe —
`scripts/check_bootstrap_phase.py` (shipped in `governance-kit/scripts/`). This
keeps phase transitions *isomorphic to the rest of the system*: mechanically
determined, "verify on signal."

Phase 1→2 is the one honest exception: "can a human still read L2 comfortably" is
subjective. Do not invent a fake metric for it — record the human's call in an
ADR instead ("adopting L3 because L2 exceeded comfortable reading load").

---

## 5. Boot-phase working rules (supersede nothing permanent; add to it)

- When you (the AI) start a session, **read this file first**, take the phase
  from the **Current phase** header, and state it back: "We are in Phase N; the
  active relaxations are …". Then work within that phase. If the header and the
  remaining R-clauses disagree, the clauses are the truth and the header is
  stale — fix the header and tell the human.
- Never silently skip a design doc, even in warn-only Phase 0. A1/A3 hold now;
  the gate is just not yet the thing that stops you.
- Never build L3 before Phase 1→2 (R0.2) — it is the classic over-early tax.
- Run `python scripts/check_bootstrap_phase.py` at milestones, or whenever the
  phase is in doubt.
- When a graduation condition is met, **do the tightening action and edit this
  file** in the same change. Boot maintaining itself is the whole design.
