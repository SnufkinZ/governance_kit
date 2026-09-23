# Governance Kit — a portable doc-driven control system for AI-assisted development

Copy this folder next to a new repo, run one installer command, and the new
project gets the documentation-code control system that runs the
Roseal/Evolvra project — from its first line of code.

## What problem it solves

When an AI writes both code *and* documentation faster than a human can read
either, the traditional brake — *the human reviews everything* — fails. This
kit restores a cheaper form of trust with a **layered control loop**:

- **Documentation is the source of truth**; code is one valid implementation of it.
- The human stays at the **design layer**; the AI reads code on the human's behalf.
- **Mechanical checks** detect drift before it compounds, so the human verifies
  *on signal, not on schedule*.

Concretely: every design doc declares the code it owns; a gate in an
independent Docs workflow flags any committed change that touches owned code
without touching its doc; pytest checks keep
file trees, links, statuses, and versions from contradicting each other; and a
model-run audit periodically reads code and prose side by side to catch what
regex cannot.

## Quick start

```bash
# 1. Install the kit into your new repo (never overwrites existing files):
python governance-kit/scripts/install.py /path/to/new-repo
cd /path/to/new-repo

# 2. Edit the four placeholder spots the installer names:
#      CLAUDE.md, docs/SPEC.md, docs/PRINCIPLES.md section 2,
#      and CODE_SCOPES / CODE_EXEMPT_PREFIXES in scripts/check_docs_sync.py.

# 3. Commit, then sanity-check (all three should run clean):
git add -A && git commit -m "install governance kit"
python scripts/check_docs_sync.py --warn-only   # Tier 3 gate (report mode)
python scripts/check_bootstrap_phase.py         # tells you what Phase 0 needs
pytest tests/docs/                              # Tiers 1-2 + gate unit tests, green out of the box
```

Prefer manual installation, or want to know exactly what lands where? Read
`MIGRATION.md` — the installer is just that file automated.
For an existing installation, follow `MIGRATION.md` §6: re-running the
installer fills missing files but does not upgrade existing rules or scripts.

## How you then build (the day-to-day loop)

1. **Every AI session starts with `BOOTSTRAP.md`** (the AI states the current
   boot phase, then works within it). The root `CLAUDE.md` carries the
   condensed working rules.
2. **First feature = first design doc.** Human and AI align on intent; the AI
   drafts the L2 contract from `docs/skill/design_template.md`, including its
   `> **Code:**` ownership line; the human approves. *Only then* is code
   written — design before code is axiom A1, never relaxed.
3. **While coding, the docs stay untouched** — the uncommitted diff is the
   record, and the gate lists owed docs as **DOCS OWED** without failing.
   Only the *why* and deliberate open questions go into the owning
   `docs/in_process/` plan (or an ADR). When the change is final and the
   human gives the command, the AI updates the design docs + one
   `docs/changelog/` entry in a single pass
   (`docs/skill/document_maintenance.md`). Changes that neither add, remove,
   nor change a documented contract (API behavior, state semantics,
   persistence compatibility, or architecture) skip L2/L3
   and carry a `docs-sync: not-needed` trailer instead.
4. **Before pushing:** `python scripts/check_docs_sync.py` — if owned code
   changed without its doc, the gate names the doc to update (or you record a
   `docs-sync: not-needed` trailer on that commit explaining why — it covers
   that commit's files only).
5. **At milestones:** run the `/doc-audit` skill (installed at
   `.claude/skills/doc-audit/`) for the semantic drift machines can't see, and
   `python scripts/check_bootstrap_phase.py` to see whether the project is
   ready to graduate to the next boot phase.

The full contract is `WORKFLOW.md`; the machinery spec is `design_doc_sync.md`.

## What is in this folder

| Path | What it is | Domain-neutral? |
|---|---|---|
| `BOOTSTRAP.md` | The temporary boot file: a maturity ladder the AI obeys while standing the system up. Graduates into `WORKFLOW.md`, then is deleted. | Yes |
| `WORKFLOW.md` | The steady-state collaboration contract (The Inversion, the three doc layers, the trust model, the audit mechanisms). | Yes |
| `PRINCIPLES.md` | The two core design principles (Decoupling + a placeholder for a domain principle). | Decoupling: yes. Second principle: replace. |
| `design_doc_sync.md` | The design of the four-tier sync system itself — what is checked, by what, and where. | Yes |
| `scripts/install.py` | One-command installer: copies everything below to its target path, never overwrites. | Yes |
| `scripts/check_docs_sync.py` | **Tier 3 gate.** Builds a `code → owning-doc` map from `> **Code:**` lines and fails a diff whose owned code changed without its doc. | Yes — edit two PORT constants |
| `scripts/check_bootstrap_phase.py` | Scores the machine-checkable Phase 0 → 1 graduation signals. | Yes |
| `tests_docs/` | **Tiers 1–2 starter tests + Tier 3 unit tests.** Green in a fresh install; start biting as conventions are used. See `tests_docs/README.md`. | Yes — one PORT-marked fixture block |
| `templates/` | Authoring skills (design contract, in-process plan, document maintenance), the Tier 4 `/doc-audit` skill, root `CLAUDE.md` + `AGENTS.md` starters (the latter points non-Claude agents at the former), the Docs workflow example, and the placeholder files the boot phase drops in. | Yes |
| `modules/workboard/` | **Optional** (`install.py --with-workboard`): the parallel-workboard protocol for several agents/windows/vendors sharing one repo — activation levels L0–L3, a temporary Integrator, task cards, receipts, notices, and explicit dispatch/commit authority. Skip it if you never run agents in parallel. | Yes |
| `tests/` | Kit-author installation regressions: fresh installs with/without workboard, template instances, repeat installs, existing-map preservation, and initial-push CI handling. Run `python -m pytest governance-kit/tests/` from the host repo (or `python -m pytest tests/` from the standalone kit). Requires pytest, PyYAML, Git, and Bash; these tests are not installed into target projects. | No |
| `MIGRATION.md` | The full file-by-file install map: what goes where, what to edit, in what order. | Yes |

## The one idea to keep straight

The control system is a **permanent immune system**, not scaffolding — it runs
for the life of the project. What is *temporary* is `BOOTSTRAP.md`: it holds
the **new-project relaxations** (rules loosened only because the project is
still small). Boot does not "build the system and get discarded." Boot
**graduates**: one by one it converts its relaxations into the permanent rules
in `WORKFLOW.md`, and when nothing temporary remains, the boot file is deleted.
See `BOOTSTRAP.md` §0.
