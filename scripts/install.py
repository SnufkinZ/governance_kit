#!/usr/bin/env python3
"""
Governance-kit installer — copies the kit into a target repo per MIGRATION.md.

Usage:
    python governance-kit/scripts/install.py <target-repo-root>
    python governance-kit/scripts/install.py <target-repo-root> --with-ci

Behavior:
- Copies every kit file to its MIGRATION.md target path.
- NEVER overwrites an existing file (idempotent; re-running reports skips).
- Creates the docs/ skeleton, tests/docs/__init__.py, and a stub docs/SPEC.md.
- Stamps today's date into docs/in_process/priority.md's snapshot line.
- With --with-ci, also installs templates/ci.example.yml as
  .github/workflows/ci.yml (skipped if one already exists).

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
    ("tests_docs/test_change_log_draft.py", "tests/docs/test_change_log_draft.py"),
    ("tests_docs/README.md", "tests/docs/README.md"),
    ("templates/design_template.md", "docs/skill/design_template.md"),
    ("templates/in_process_plan_format.md", "docs/skill/in_process_plan_format.md"),
    ("templates/document_maintenance.md", "docs/skill/document_maintenance.md"),
    ("templates/doc-audit-SKILL.md", ".claude/skills/doc-audit/SKILL.md"),
    ("templates/CLAUDE.root.md", "CLAUDE.md"),
    ("templates/AGENTS.root.md", "AGENTS.md"),
    ("templates/placeholders/changelog__README.md", "docs/changelog/README.md"),
    ("templates/placeholders/decisions__README.md", "docs/decisions/README.md"),
    ("templates/placeholders/ADR-template.md", "docs/decisions/ADR-template.md"),
    ("templates/placeholders/in_process__README.md", "docs/in_process/README.md"),
    ("templates/placeholders/in_process__priority.md", "docs/in_process/priority.md"),
    ("templates/placeholders/in_process__change_log_draft.md",
     "docs/in_process/change_log_draft.md"),
    ("templates/placeholders/audit__README.md", "docs/audit/README.md"),
]

CI_MAP = ("templates/ci.example.yml", ".github/workflows/ci.yml")

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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="root of the repo to install into")
    parser.add_argument("--with-ci", action="store_true",
                        help="also install .github/workflows/ci.yml")
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
    mappings = list(FILE_MAP) + ([CI_MAP] if args.with_ci else [])
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

    print(f"governance-kit install into: {target}")
    print(f"  copied : {len(copied)}")
    for f in copied:
        print(f"    + {f}")
    if skipped:
        print(f"  skipped (already exist): {len(skipped)}")
        for f in skipped:
            print(f"    = {f}")
    if not args.with_ci:
        print("  (CI workflow not installed; re-run with --with-ci, or wire "
              "templates/ci.example.yml by hand)")

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
