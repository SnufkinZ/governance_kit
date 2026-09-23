#!/usr/bin/env python3
"""
Governance-kit installer — copies the kit into a target repo per MIGRATION.md.

Usage:
    python governance-kit/scripts/install.py <target-repo-root>
    python governance-kit/scripts/install.py <target-repo-root> --with-ci
    python governance-kit/scripts/install.py <target-repo-root> --with-workboard

Behavior:
- Copies every kit file to its MIGRATION.md target path.
- NEVER overwrites an existing file (idempotent; re-running reports skips).
- Creates the docs/ skeleton, tests/docs/__init__.py, and a stub docs/SPEC.md.
- Stamps today's date into docs/in_process/priority.md's snapshot line.
- With --with-ci, also installs templates/docs.example.yml as
  .github/workflows/docs.yml — the independent Docs workflow (skipped if one
  already exists). Runtime CI stays yours; it should not run tests/docs/.
- With --with-workboard, also installs the optional parallel-workboard module
  (modules/workboard/): the coordination protocol, an idle global board, the
  task/receipt/notice mailboxes and their templates. Only for projects where
  several agents, windows or vendors work in one repo at once.

After installing you still have to EDIT (the installer reminds you):
- CLAUDE.md and docs/SPEC.md (replace every <placeholder>),
- CODE_SCOPES / CODE_EXEMPT_PREFIXES in scripts/check_docs_sync.py,
- the second principle in docs/PRINCIPLES.md.

Exit codes: 0 ok; 2 setup error.
"""

from __future__ import annotations

import argparse
import datetime
import shutil
import sys
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[1]

# (kit-relative source, target-repo-relative destination)
FILE_MAP: list[tuple[str, str]] = [
    ("BOOTSTRAP.md", "BOOTSTRAP.md"),
    ("PRINCIPLES.md", "docs/PRINCIPLES.md"),
    ("WORKFLOW.md", "docs/WORKFLOW.md"),
    ("design_doc_sync.md", "docs/design_doc_sync.md"),
    ("scripts/check_docs_sync.py", "scripts/check_docs_sync.py"),
    ("scripts/check_bootstrap_phase.py", "scripts/check_bootstrap_phase.py"),
    ("tests_docs/test_ownership_gate.py", "tests/docs/test_ownership_gate.py"),
    ("tests_docs/test_doc_consistency.py", "tests/docs/test_doc_consistency.py"),
    ("tests_docs/test_doc_contradictions.py", "tests/docs/test_doc_contradictions.py"),
    ("tests_docs/README.md", "tests/docs/README.md"),
    ("templates/placeholders/docs__CLAUDE.md", "docs/CLAUDE.md"),
    ("templates/placeholders/skill__CLAUDE.md", "docs/skill/CLAUDE.md"),
    ("templates/design_template.md", "docs/skill/design_template.md"),
    ("templates/in_process_plan_format.md", "docs/skill/in_process_plan_format.md"),
    ("templates/document_maintenance.md", "docs/skill/document_maintenance.md"),
    ("templates/doc-audit-SKILL.md", ".claude/skills/doc-audit/SKILL.md"),
    ("templates/CLAUDE.root.md", "CLAUDE.md"),
    ("templates/AGENTS.root.md", "AGENTS.md"),
    ("templates/placeholders/changelog__CLAUDE.md", "docs/changelog/CLAUDE.md"),
    ("templates/placeholders/decisions__CLAUDE.md", "docs/decisions/CLAUDE.md"),
    ("templates/placeholders/ADR-template.md", "docs/decisions/ADR-template.md"),
    ("templates/placeholders/in_process__CLAUDE.md", "docs/in_process/CLAUDE.md"),
    ("templates/placeholders/in_process__priority.md", "docs/in_process/priority.md"),
    ("templates/placeholders/audit__CLAUDE.md", "docs/audit/CLAUDE.md"),
]

CI_MAP = ("templates/docs.example.yml", ".github/workflows/docs.yml")

# Optional module: parallel workboard (see modules/workboard/parallel_workboard.md).
WORKBOARD_MAP: list[tuple[str, str]] = [
    ("modules/workboard/parallel_workboard.md", "docs/skill/parallel_workboard.md"),
    ("modules/workboard/WORKBOARD.md", "docs/in_process/WORKBOARD.md"),
    ("modules/workboard/workboard__CLAUDE.md", "docs/in_process/workboard/CLAUDE.md"),
    ("modules/workboard/tasks__CLAUDE.md", "docs/in_process/workboard/tasks/CLAUDE.md"),
    ("modules/workboard/receipts__CLAUDE.md", "docs/in_process/workboard/receipts/CLAUDE.md"),
    ("modules/workboard/notices__CLAUDE.md", "docs/in_process/workboard/notices/CLAUDE.md"),
    ("modules/workboard/templates/task_card.md",
     "docs/in_process/workboard/templates/task_card.md"),
    ("modules/workboard/templates/task_receipt.md",
     "docs/in_process/workboard/templates/task_receipt.md"),
    ("modules/workboard/templates/coordination_notice.md",
     "docs/in_process/workboard/templates/coordination_notice.md"),
]

# Pointer lines the module adds to maps the core install just created. A map the
# target already had is never edited; the installer prints the line instead.
WORKBOARD_POINTERS: list[tuple[str, str, str]] = [
    # (map file, line to insert after, line to insert)
    ("docs/skill/CLAUDE.md",
     "|-- in_process_plan_format.md  # the plan-doc head + Track format the board expects",
     "|-- parallel_workboard.md      # optional: protocol for coordinated multi-agent work"),
    ("docs/in_process/CLAUDE.md",
     "  (Tier 1 enforces this).",
     "- **Coordinated multi-agent work:** `WORKBOARD.md` (runtime state) and\n"
     "  `workboard/` (cards, receipts, notices); protocol in\n"
     "  `../skill/parallel_workboard.md`. Opt-in; most work never registers."),
]

SPEC_STUB = """# SPEC

<One paragraph: what this project is, for whom, and what "done" looks like.
Refine as the project takes shape — but never leave the placeholder in.>
"""


def install_file(src: Path, dest: Path) -> str:
    """Copy src to dest unless dest exists. Returns 'copied' or 'skipped'."""
    if dest.exists():
        return "skipped"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    return "copied"


def insert_pointer(path: Path, anchor: str, line: str) -> bool:
    """Insert `line` after the first line ending with `anchor`. False if absent."""
    text = path.read_text(encoding="utf-8")
    lines = text.split("\n")
    for i, existing in enumerate(lines):
        if existing.endswith(anchor):
            lines.insert(i + 1, line)
            path.write_text("\n".join(lines), encoding="utf-8")
            return True
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="root of the repo to install into")
    parser.add_argument("--with-ci", action="store_true",
                        help="also install the Docs workflow "
                             "(.github/workflows/docs.yml)")
    parser.add_argument("--with-workboard", action="store_true",
                        help="also install the optional parallel-workboard module")
    parser.add_argument("--force", action="store_true",
                        help="allow installing into the repo that hosts the kit")
    args = parser.parse_args()

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"target is not a directory: {target}", file=sys.stderr)
        return 2
    if target == KIT_ROOT.parent and not args.force:
        print("Refusing to install into the repo that hosts the kit itself "
              "(this is almost never intended). Pass --force to override.",
              file=sys.stderr)
        return 2

    copied, skipped = [], []
    mappings = (list(FILE_MAP) + ([CI_MAP] if args.with_ci else [])
                + (WORKBOARD_MAP if args.with_workboard else []))
    for src_rel, dest_rel in mappings:
        src = KIT_ROOT / src_rel
        if not src.is_file():
            print(f"kit file missing: {src_rel} (kit copy is incomplete?)",
                  file=sys.stderr)
            return 2
        dest = target / dest_rel
        (copied if install_file(src, dest) == "copied" else skipped).append(dest_rel)

    # Generated files (not copies of kit files).
    init_py = target / "tests" / "docs" / "__init__.py"
    if not init_py.exists():
        init_py.parent.mkdir(parents=True, exist_ok=True)
        init_py.write_text("", encoding="utf-8")
        copied.append("tests/docs/__init__.py")
    else:
        skipped.append("tests/docs/__init__.py")

    spec = target / "docs" / "SPEC.md"
    if not spec.exists():
        spec.parent.mkdir(parents=True, exist_ok=True)
        spec.write_text(SPEC_STUB, encoding="utf-8")
        copied.append("docs/SPEC.md")
    else:
        skipped.append("docs/SPEC.md")

    # Stamp today's date into the freshly installed priority board so the
    # snapshot line is parseable from day one.
    priority = target / "docs" / "in_process" / "priority.md"
    if "docs/in_process/priority.md" in copied:
        text = priority.read_text(encoding="utf-8")
        today = datetime.date.today().isoformat()
        priority.write_text(text.replace("YYYY-MM-DD", today, 1), encoding="utf-8")

    # The workboard module lands files that the core maps must list (Tier 1
    # checks tree completeness). Patch only maps created by this very run.
    manual_pointers: list[tuple[str, str]] = []
    if args.with_workboard:
        for map_rel, anchor, line in WORKBOARD_POINTERS:
            if map_rel in copied and insert_pointer(target / map_rel, anchor, line):
                continue
            if line not in (target / map_rel).read_text(encoding="utf-8"):
                manual_pointers.append((map_rel, line))

    print(f"governance-kit install into: {target}")
    print(f"  copied : {len(copied)}")
    for f in copied:
        print(f"    + {f}")
    if skipped:
        print(f"  skipped (already exist): {len(skipped)}")
        for f in skipped:
            print(f"    = {f}")
        print("  Existing files were preserved, not upgraded. Follow the kit's "
              "MIGRATION.md section 6 to merge updates and retire obsolete files; "
              "preserve your current bootstrap phase.")
    if args.with_ci and (target / ".github/workflows/ci.yml").exists():
        print("  Review existing .github/workflows/ci.yml: remove only docs "
              "jobs migrated to docs.yml; preserve runtime CI (MIGRATION.md section 6).")
    if manual_pointers:
        print("  ACTION: these maps already existed and were not edited; add by hand:")
        for map_rel, line in manual_pointers:
            print(f"    {map_rel}:")
            for part in line.split("\n"):
                print(f"      {part}")
    if not args.with_ci:
        print("  (Docs workflow not installed; re-run with --with-ci, or wire "
              "templates/docs.example.yml by hand)")

    print("""
Next steps (BOOTSTRAP.md section 2):
  1. EDIT the placeholders: CLAUDE.md, docs/SPEC.md, and the second
     principle in docs/PRINCIPLES.md.
  2. EDIT the PORT constants in scripts/check_docs_sync.py
     (CODE_SCOPES / CODE_EXEMPT_PREFIXES) to match your repo layout.
  3. Commit the install (the sync gate diffs against your main branch).
  4. Sanity check:
       python scripts/check_docs_sync.py --warn-only
       python scripts/check_bootstrap_phase.py
       pytest tests/docs/
  5. Read BOOTSTRAP.md and start at Phase 0: write the first design doc
     BEFORE its code.""")
    return 0


if __name__ == "__main__":
    sys.exit(main())
