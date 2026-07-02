#!/usr/bin/env python3
"""
Bootstrap phase checker (BOOTSTRAP.md §4).

Reports whether the project has met the *machine-checkable* graduation signals
for the current boot phase. Phase 0 -> 1 is countable and lives here. Phase
1 -> 2 is a human judgment (can a human still read L2 comfortably) and is
deliberately NOT scored here — record that call in an ADR instead.

This keeps phase transitions isomorphic to the rest of the control system:
verify on signal, not on schedule.

Exit codes: 0 = Phase 0 graduation signals met; 1 = not yet; 2 = setup error.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"
BOOT = REPO_ROOT / "BOOTSTRAP.md"

CODE_LINE = re.compile(r"^>\s*\*\*Code:\*\*\s*(.+)$", re.M)
# Signal (c): the R0.1 clause records the first would-have-blocked event.
EVENT_LINE = re.compile(
    r"First would-have-blocked event:\*\*\s*(\d{4}-\d{2}-\d{2})"
)

# Phase 0 -> 1 thresholds (BOOTSTRAP.md §3). Tune for your project size.
MIN_CODE_OWNING_DOCS = 3


def code_owning_docs() -> list[Path]:
    """design_*.md files that declare a `> **Code:**` owner line."""
    out: list[Path] = []
    if not DOCS.exists():
        return out
    for doc in sorted(DOCS.rglob("design_*.md")):
        if {"archive", "skill"} & set(doc.relative_to(DOCS).parts):
            continue
        if CODE_LINE.search(doc.read_text(encoding="utf-8")):
            out.append(doc)
    return out


def doc_tests_present() -> bool:
    return (REPO_ROOT / "tests" / "docs").is_dir()


def gate_present() -> bool:
    return (REPO_ROOT / "scripts" / "check_docs_sync.py").is_file()


def skeleton_dirs_present() -> list[str]:
    """A2: the control loop's shape must be visible even when empty."""
    required = ["changelog", "decisions", "in_process", "audit", "skill"]
    return [d for d in required if not (DOCS / d).is_dir()]


def first_block_event() -> str | None:
    """Date of the first would-have-blocked event recorded in BOOTSTRAP.md."""
    if not BOOT.is_file():
        return None
    m = EVENT_LINE.search(BOOT.read_text(encoding="utf-8"))
    return m.group(1) if m else None


def main() -> int:
    # Output is ASCII-only on purpose: Windows consoles often decode cp1252/GBK.
    print("Bootstrap phase check (BOOTSTRAP.md section 4)\n")

    missing_skel = skeleton_dirs_present()
    owners = code_owning_docs()
    tests_ok = doc_tests_present()
    gate_ok = gate_present()
    event = first_block_event()

    # A2 — skeleton visible
    if missing_skel:
        print(f"  [X] A2 skeleton incomplete - missing docs/: {', '.join(missing_skel)}")
    else:
        print("  [OK] A2 skeleton present (changelog, decisions, in_process, audit, skill)")

    # Phase 0 -> 1 signals
    print()
    print("  Phase 0 -> 1 graduation signals:")
    a = len(owners) >= MIN_CODE_OWNING_DOCS
    print(f"    [{'OK' if a else 'X'}] (a) >= {MIN_CODE_OWNING_DOCS} design docs with a `> **Code:**` "
          f"line  (have {len(owners)})")
    for d in owners:
        print(f"           - {d.relative_to(REPO_ROOT).as_posix()}")
    print(f"    [{'OK' if tests_ok else 'X'}] (b1) tests/docs/ present")
    print(f"    [{'OK' if gate_ok else 'X'}] (b2) scripts/check_docs_sync.py present")
    c = event is not None
    if c:
        detail = f"dated {event}"
    else:
        detail = ("none in BOOTSTRAP.md yet - record the date on the R0.1 "
                  "event line when the warn-only gate first fires")
    print(f"    [{'OK' if c else 'X'}] (c) R0.1 records a would-have-blocked event ({detail})")

    ready = bool(a and tests_ok and gate_ok and c and not missing_skel)
    print()
    if ready:
        print("  => Phase 0 signals MET (confirm tests/docs/ is also green in CI). "
              "Do the tightening action: flip Tier 3 to blocking, delete R0.1 from "
              "BOOTSTRAP.md, set Current phase to 1.")
        return 0
    print("  => Not yet. Keep authoring design docs (design-first, A1) and wiring the "
          "skeleton (A2).")
    return 1


if __name__ == "__main__":
    sys.exit(main())
