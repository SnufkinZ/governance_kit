# Governance Kit

A documentation-driven control system for software that AI agents write most of.
Design docs declare the code they own, mechanical checks catch drift between the
two, and humans work at the design layer instead of reviewing every diff.

It is extracted from [Roseal](https://roseal.dev), where it has governed a
codebase built largely by AI agents since June 2026.

## The problem

When an AI writes both code *and* documentation faster than a human can read
either, the traditional brake — *a human reviews everything* — stops working.
This kit replaces it with a cheaper form of trust:

- **Documentation is the source of truth**; code is one valid implementation of it.
- **Humans stay at the design layer**; the AI reads code on their behalf.
- **Mechanical checks catch drift early**, so humans look at code when a signal
  says so, not on a schedule.

## What you get

- **Ownership lines.** Each design doc declares the code it owns
  (``> **Code:** `src/auth/**` ``).
- **A doc-sync check.** A script that fails when owned code changes without its
  design doc, unless the commit records why the doc did not need to change.
- **Consistency tests.** pytest checks that keep directory maps, links, statuses
  and versions in your docs from contradicting each other.
- **A semantic audit.** An agent skill (`/doc-audit`) that periodically reads code
  and docs side by side to find drift no script can see.
- **A staged start.** `BOOTSTRAP.md` relaxes the rules while a project is small
  and tightens them as it grows, so the process never costs more than the
  project can carry.
- **Templates** for design docs, plans, ADRs, and the root `CLAUDE.md` /
  `AGENTS.md` that tell agents how to work in the repo.

Two optional modules:

- **L3 freshness pin** (`--with-l3`). For projects that also keep plain-language
  docs for humans: each page records a hash of the design doc it explains, and
  a test fails when that design doc changes until someone re-checks the page.
- **Parallel workboard** (`--with-workboard`). A coordination protocol for
  several agents or windows working in one repo at once.

## Requirements

Python 3.10+, Git, and `pip install pytest pyyaml`. The agent skill and root
instructions are written for Claude Code; `AGENTS.md` points other agents at
the same rules.

## Quick start

```bash
# 1. Get the kit (the folder name matters: the commands below use it)
git clone https://github.com/SnufkinZ/governance_kit.git governance-kit

# 2. Install into your repo (never overwrites existing files)
python governance-kit/scripts/install.py /path/to/your-repo --with-ci
cd /path/to/your-repo

# 3. Edit what the installer lists: CLAUDE.md, docs/SPEC.md,
#    section 2 of docs/PRINCIPLES.md, and CODE_SCOPES in scripts/check_docs_sync.py

# 4. Commit, then check that everything runs clean
git add -A && git commit -m "install governance kit"
python scripts/check_docs_sync.py --warn-only
python scripts/check_bootstrap_phase.py
pytest tests/docs/
```

`--with-ci` also installs a GitHub Actions workflow for the docs checks. For a
file-by-file account of what lands where, or to upgrade an existing
installation, read `MIGRATION.md`.

## Day-to-day use

1. **Each agent session starts from `BOOTSTRAP.md`** while it exists, and from
   the root `CLAUDE.md` always.
2. **Design before code.** A feature starts as a design doc, written with the
   agent from `docs/skill/design_template.md` and approved by a human. Code
   comes after.
3. **Docs are updated once, at the end.** While a change is still uncommitted,
   the check reports missing doc updates as *owed* instead of failing. When the
   change is done, the agent updates the design docs and changelog in one pass.
   Changes that don't alter a documented contract carry a
   `docs-sync: not-needed` commit trailer instead.
4. **Before pushing,** run `python scripts/check_docs_sync.py`. It names any
   design doc that must change.
5. **At milestones,** run `/doc-audit` for semantic drift, and
   `check_bootstrap_phase.py` to see whether the project is ready for stricter
   rules.

The full collaboration contract is `WORKFLOW.md`; the design of the checks
themselves is `design_doc_sync.md`.

## What's in this repository

| Path | What it is |
|---|---|
| `README.md` | This file. |
| `BOOTSTRAP.md` | The staged-start ladder agents follow while the project is young. It hands its rules over to `WORKFLOW.md` one by one, then is deleted. |
| `WORKFLOW.md` | The long-term human–AI collaboration contract: documentation layers, roles, trust model, audits. |
| `PRINCIPLES.md` | Design principles every proposal is judged against. **Edit:** section 2 is a placeholder for your own domain principle. |
| `design_doc_sync.md` | How the checks work: what each one verifies, and where. |
| `MIGRATION.md` | The install map, what to edit afterwards, and how to upgrade. |
| `scripts/install.py` | The installer. Copies files into place and never overwrites. |
| `scripts/check_docs_sync.py` | The doc-sync check. **Edit:** `CODE_SCOPES` / `CODE_EXEMPT_PREFIXES` for your layout. |
| `scripts/check_bootstrap_phase.py` | Reports whether the project is ready for the next stage. |
| `tests_docs/` | The consistency tests. Installed as `tests/docs/`, green on a fresh install. |
| `templates/` | Design-doc, plan and ADR templates, the `/doc-audit` skill, root `CLAUDE.md` / `AGENTS.md`, and the example docs workflow. |
| `modules/l3/` | Optional L3 freshness-pin test (`--with-l3`). **Edit:** `L3_ROOTS` for where your pages live. |
| `modules/workboard/` | Optional parallel-workboard protocol (`--with-workboard`). |
| `tests/` | The kit's own installer tests. Not installed into your repo. |
| `LICENSE` | MIT. |

## The one idea to keep straight

The checks are permanent; only the relaxations are temporary. `BOOTSTRAP.md`
holds rules loosened because the project is still small. As the project grows,
each relaxation graduates into a permanent rule in `WORKFLOW.md`, and when none
remain, the bootstrap file is deleted. See `BOOTSTRAP.md` §0.

## Status

Early. The kit comes from one project and a small team, and the process is
still changing. Issues and suggestions are welcome.

## License

MIT — see `LICENSE`.
