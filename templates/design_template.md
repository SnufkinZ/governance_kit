# L2 Design Contract Writing Skill

L2 design documents are architecture contracts. They are written for AI agents
and rigorous review, not for first-pass human intuition. Patient, illustrated,
human-readable explanation belongs to the L3 human-intuition layer (a docs
site — see `WORKFLOW.md` §1.1), which is stood up only when a human needs it
(`BOOTSTRAP.md` R0.2).

## Role

A design document answers:

- what system or boundary is being specified;
- what code owns or implements it;
- what invariants downstream code may rely on;
- what interfaces, data shapes, defaults, and lifecycle rules are locked;
- what is deliberately out of scope.

It must not become:

- an implementation diary;
- a step-by-step work plan;
- a changelog;
- a tutorial or textbook chapter;
- an L3 intuition page in disguise.

## Timing

Design docs can be written in two modes:

1. **Pre-implementation contract** - the approved target design before coding.
   It may describe the intended contract, but not a task checklist. Use a
   non-terminal status such as `In Review` or `Approved for implementation`.
2. **Post-implementation contract** - the current system after coding. Before a
   feature is considered done, rewrite the doc so it reads as current reference
   material, not as the plan that produced it.

Implementation history goes to `docs/changelog/`. Active sequencing and open
work go to `docs/in_process/`. Human intuition, diagrams, worked examples, and
long explanations go to the L3 layer once it exists.

## Required Header

Use this header for every code-owning L2 design doc:

```md
> **Scope:** <one precise sentence naming the system and boundary>
> **Version:** <semver-like version>
> **Status:** <Current | In Review | Approved for implementation | Partially built | Superseded>
> **Prerequisite:** <upstream docs/ADRs, or None>
> **Location:** `docs/.../design_*.md`
> **Code:** `path/or/glob/**`, `path/file.py`
```

`> **Code:**` is machine-readable. It may contain only backticked code paths or
globs. Do not put explanatory prose, markdown doc paths, bare terms, or
non-code tokens on that line. Put ownership notes in a normal paragraph below
the header. Claim a package with a glob (`src/pkg/**`), never a bare directory
(`src/pkg/`): a directory token owns zero files, so the gate reads green while
governing nothing — `tests/docs/test_ownership_gate.py` fails on any
path-shaped token that matches no live file.

Pure cross-cutting rulebooks may omit `> **Code:**` when they do not own a code
region directly.

## The Other L2 Plane — Where Theory Goes

A design doc owns the **contract**: names, shapes, formulas, phase order,
status, deferred seats. Keep the reasons with it — a sentence or two beside a
contract explaining why it is shaped that way is part of a good contract.

**Most design docs stop there, and that is correct.** For a small class of
foundational mechanisms, the *why* is not a few sentences but a body of theory
that outlives any implementation and judges every future design touching it.
That theory lives in a **mechanism architecture doc**
(`docs/architecture/mechanism_*.md`), full L2 authority alongside this doc, not
beneath it. Platform and adapter contracts are outside the class by nature.
Writing one is optional and rare; your doc having none is not a gap. Rule:
`docs/design_doc_sync.md` §7.1.

When a companion exists (e.g. `mechanism_scheduling.md` ↔
`design_scheduler.md`):

- cite it in `> **Prerequisite:**` and link it near the top;
- **do not restate its theory** — link instead; two copies drift, and the
  mechanism doc wins on theory by definition;
- the companion carries `> **Engineering Contract:**` pointing back here. Once
  L3 exists, that line is machine-read to force every L3 page retelling this
  contract to retell the theory too (`design_doc_sync.md` §3.1) — so the
  back-link is not decoration.

The split is one-way for code: a mechanism doc never carries `> **Code:**`, so
refactors never drag the theory, and theory edits never trip the Tier 3 gate.

## Recommended Shape

Adapt the section names to the system, but keep the contract function:

```md
## 0. Design Intent
## 1. Overview
## 2. Goals and Non-Goals
## 3. Boundary and Ownership
## 4. Interfaces and Data Shapes
## 5. Runtime / Lifecycle Semantics
## 6. Invariants
## 7. Failure Modes and Validation
## 8. Deferred Scope
## 9. Changelog
```

`## 0. Design Intent` should be brief. It can preserve the human's original
design insight, but only enough to orient the contract. If it grows into
teaching prose, move that material to the L3 layer.

Use code snippets only for public shapes, signatures, schema examples, or
algorithms where prose would be ambiguous. Do not paste large implementation
blocks.

## Current vs. Deferred

Keep current behavior and deferred behavior visibly separate.

- Current contract: what code may rely on now, or what the approved
  pre-implementation contract requires.
- Deferred scope: future-compatible boundaries that must not be blocked.

Avoid broad "Future Extensions" essays. If deferred work needs sequencing,
trade-off analysis, or multiple work units, create or update an `in_process/`
plan and link to it.

## Changelog

The design doc may end with a short pointer:

```md
## Changelog

Full history: [Name Changelog](../changelog/<file>.md).
```

The actual history belongs in `docs/changelog/`, not inline.

## Authoring Checklist

Before writing:

1. Read `docs/WORKFLOW.md` and the affected local `CLAUDE.md` files.
2. Read upstream design docs and ADRs listed as prerequisites.
3. Read existing code if the doc describes an implemented system.
4. Decide whether this is a pre-implementation target contract or a
   post-implementation current contract.

Before finishing:

1. Ensure every current-tense mechanism matches code or the approved target.
2. Ensure all implementation history has moved to changelog or in-process docs.
3. Ensure every deferred item is clearly outside the current contract.
4. Ensure `> **Code:**` is machine-readable and contains only code paths/globs.
5. If the doc has a `> **Version:**`, update its changelog entry.
6. If an L3 page pins this doc (once the L3 layer exists), update or re-check
   that page after the version changes.
