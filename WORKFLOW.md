# Human-AI Collaboration Workflow

> **Scope:** How humans and AI agents collaborate on this project — the
> steady-state contract the whole control system serves.
> **Relation to other files:**
> - This document describes the *process* of building the project.
> - `PRINCIPLES.md` describes the *system being built*.
> - `design_doc_sync.md` describes the *machinery* that keeps docs and code in agreement.
> - `CLAUDE.md` files in each directory carry *point-of-use rules* for that scope.
> - `BOOTSTRAP.md`, while it exists, adds temporary new-project relaxations on top of this file.

---

## 0. One-sentence summary

> **Human owns design and supervision. AI owns implementation and reading.
> Documentation is the contract between them.**

The human stays at the highest-leverage layer (intent, principles, architecture).
The AI handles what benefits from speed and exhaustive recall (writing code,
reading the codebase, keeping docs in sync). Documentation lets the two sides
operate without re-synchronizing through the code itself.

---

## 1. The Inversion

Traditional software:
- Code is the source of truth.
- Documentation is a (often stale) reference.
- Humans read code; documentation is a courtesy.

This project:
- **Documentation is the source of truth.**
- **Code is one valid implementation of the documented intent.**
- **AI reads code on the human's behalf; humans read documentation by default.**

This inversion is only viable because AI can read code far faster and more
exhaustively than a human. It collapses if the AI cannot be trusted to keep code
aligned with documentation — which is why the audit mechanisms in §6 exist.

### 1.1 The Three Documentation Layers

Documentation is not one thing. As AI writes both code *and* design docs at
machine speed, the design docs themselves can outgrow human reading speed. The
collaboration therefore runs on **three layers**:

| Layer | Artifact | Primary reader | Purpose |
|---|---|---|---|
| **L1 — Code** | `src/`, `backend/`, … | AI | Executable truth. Guarded by types, tests, and decoupling so local error cannot spread. |
| **L2 — Design docs** | `docs/**/design_*.md`, ADRs | AI + rigor | The architecture **contract**. Every code region traces to it; it governs AI development, semantic audit, change control. Precise, not easy. |
| **L3 — Human-intuition layer** | a docs site (optional) | **Human** | Translates L2 into human **intuition** — a patient retelling where the human builds understanding and forms the next instruction. |

L3 is a **faithful retelling, never a second source of truth.** On any conflict,
the L2 doc wins and the L3 page is the defect. L3's risk is the same drift
problem moved up one edge — an L3 page can silently rot as its L2 doc moves — so
the L2↔L3 edge is pinned mechanically (each L3 page records the L2 version/hash
it aligned to; a test fails when the source advances past the pin). **L3 is
deferred until a human actually needs it** — see `BOOTSTRAP.md` R0.2; building it
too early is pure cost with no reader.

---

## 2. Roles

### 2.1 Human

| Layer | Activity |
|---|---|
| Design | Author/own SPEC, PRINCIPLES, and design docs. Decide what the system *should* do. |
| Supervision | Review documentation diffs. Make judgment calls on trade-offs the AI flags. Approve principle changes. |
| Spot-check | Drop to code only when a signal warrants it (§7). |

The human does **not**, by default, write/edit code line-by-line or review every
code diff. The human **does** keep the global view: how the code runs, its
structure, and the goals.

### 2.2 AI

| Layer | Activity |
|---|---|
| Implementation | Write and modify code per the documented design. |
| Maintenance | Keep `docs/` and `docs/changelog/` synchronized with code reality after every structural change. |
| Mediation | Answer "where is X implemented? why does it work this way?" by reading code and docs in real time. |
| Audit | Run scheduled drift checks (§6.1) in fresh-context sessions. |

The AI does **not**, by default: deviate from a documented design without
surfacing the conflict; modify `PRINCIPLES.md`/`SPEC.md` unilaterally; add island
mechanisms, hardcoded caps, or wide interfaces "for safety" without
justification; or refactor opportunistically while doing other work.

---

## 3. Trust Model

**(1) Documentation is the source of truth.** When code and docs disagree, the
default question is "did the AI drift?" — not "is the doc outdated?" Outdated
documentation is a defect that should have been caught earlier.

**(2) Default trust the code layer.** The human does not pre-audit AI-written
code. Code is assumed to honor the design until a signal suggests otherwise.

**(3) Verify on signal, not on schedule.** The human drops into code when a §7
signal fires. Routine "let me just check what the AI did" is discouraged — it is
low-leverage and trains a dependency the workflow is designed to eliminate.

---

## 4. Workflow by activity type

### 4.1 New feature
```
1. Discussion       — human and AI align on intent
2. Design doc       — AI drafts the L2 contract using docs/skill/design_template.md
3. Review           — human reviews, iterates, approves
4. Implementation   — AI writes code and tests
5. Doc sync         — AI updates docs/ + docs/changelog/ + local CLAUDE.md + decisions/ if needed
6. Doc review       — human reviews the doc diff, briefly scans the code diff for alignment
7. Testing          — human runs the new behavior and verifies it
```
(A1 in `BOOTSTRAP.md`: steps 1–3 precede step 4 always. Design before code.)

### 4.2 Bug fix
```
1. Symptom          — human describes the observable problem
2. Locate           — AI finds the root cause and explains
3. Propose          — AI proposes a fix
4. Classify         — does the fix touch design?  No -> 5;  Yes -> fall back to 4.1
5. Implement + sync — AI fixes and updates any affected docs
```

### 4.3 Refactor
```
1. Scope            — identify which design docs the refactor touches
2. Principle check  — evaluate against PRINCIPLES.md
3. Branch           — if a principle would be violated: revise the principle (with ADR),
                      or abandon the refactor. Never silently violate.
4. Implement + sync — proceed only after principle alignment
```

### 4.4 Documentation-only update
```
1. Propose          — human or AI proposes a doc change
2. Downstream check — identify documents that depend on this one
3. Update           — apply the change + mirror to docs/changelog/
4. Review           — human approves
```

---

## 5. Document layering and loading strategy

**Each layer loads under different conditions — intentionally.** Centralizing all
rules into this file would force every AI session to load the entire ruleset
regardless of task, wasting tokens and diluting attention. This defeats the
just-in-time property that makes the structure work.

| Layer | File(s) | When loaded |
|---|---|---|
| Project entry | Root `CLAUDE.md` | Every AI session in this repo |
| Local rules | `*/CLAUDE.md` per directory | When AI works in that directory |
| System principles | `PRINCIPLES.md` | When designing or reviewing architecture |
| System spec | `SPEC.md` | When intent or scope is in question |
| Module designs (L2) | `docs/**/design_*.md` | When working on that module |
| Human-intuition (L3) | docs site | When a human needs to understand/test a system |
| Process meta | `WORKFLOW.md` (this file) | Onboarding; designing the workflow itself |
| Boot ladder | `BOOTSTRAP.md` | Every session until the project reaches maturity |

**Local rules stay local.** This document describes the *shape* of the
collaboration, not its rulebook.

---

## 6. Audit mechanisms

The trust model only works if drift is detected before it compounds. The full
design is `design_doc_sync.md`; four mechanisms:

### 6.1 Drift audit (independent-context AI)
A periodic task where a fresh-context AI session reads a design doc and the
corresponding code and reports inconsistencies. Output is a **list, not a fix** —
the human decides whether the doc lags or the code drifted. Must be a fresh
session. Reports go to `docs/audit/`. (Deferred to a real cadence at Phase 1→2;
see `BOOTSTRAP.md` R0.3.)

### 6.2 Decision log (ADR)
`docs/decisions/` holds Architecture Decision Records — one per significant
decision, capturing what was considered and why each alternative was accepted or
rejected. ADRs prevent rejected proposals from being silently re-adopted.
`docs/changelog/` records *what changed*; ADRs record *what was considered and why*.

### 6.3 Periodic doc consolidation
Every so often, an AI run produces a *proposal list* (not direct edits): content
duplicated across documents, rules absorbed into a higher-level principle that can
be removed downstream, and long-stale draft documents to archive. The human
reviews and approves before any consolidation.

### 6.4 Changelog mirror
`docs/changelog/` mirrors design docs and preserves history — the audit trail of
record. Append-only in spirit: old entries are superseded, not rewritten.

---

## 7. When humans drop to code

Signals that justify leaving the documentation layer to inspect code directly:

1. **An audit report flags a specific inconsistency** — verify and decide direction.
2. **Behavior is anomalous** — the system does something nobody expected.
3. **AI explanations contradict each other** across sessions — its mental model is unstable; get ground truth.
4. **Introducing a new principle** — verify the codebase actually has the property the principle assumes.
5. **Cross-cutting decisions spanning multiple design docs** — keep the human anchored to actual structure.
6. **Low decoupling raises supervision needs** — where code is highly decoupled you can tolerate local error; where it is not, learn more of the code and give the AI more detail.

---

## 8. Anti-patterns

| Anti-pattern | Why it breaks the workflow |
|---|---|
| "Skip the doc update this once" | Documentation is the contract. Skipping erodes the trust model everything else depends on. |
| AI refactors opportunistically while fixing a bug | Refactor is its own activity (§4.3) with its own gate. Mixing bypasses principle review. |
| Human approves a doc diff without reading | Removes the only checkpoint between AI design changes and committed reality. |
| A rejected ADR proposal is silently re-adopted | ADRs are not being consulted; past decisions stop accumulating into wisdom. |
| Centralizing local CLAUDE.md rules into this file | Defeats JIT loading; dilutes AI attention across irrelevant rules. |
| Building L3 before a human needs it | The classic over-early tax (see BOOTSTRAP.md R0.2). |
