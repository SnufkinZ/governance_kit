"""
Tier 3 unit tests — pin the ownership-gate semantics (design_doc_sync.md §4).

Both pinned behaviors guard against real bugs found in the origin project:
fnmatch-style `*` crossing `/` (one doc's glob silently claiming files in a
subpackage owned by another doc), and a bypass check that plain prose could
trip. The gate's end-to-end behavior is exercised by CI; these test the pure
functions.

PORTING NOTES
- These tests run AFTER install (they load `scripts/check_docs_sync.py` from
  the repo root two levels up), not from inside the kit folder.
- The glob/bypass tests are layout-independent and run anywhere.
- The in_scope tests mirror the kit defaults for CODE_SCOPES /
  CODE_EXEMPT_PREFIXES. If you edited those constants, update the fixture
  paths marked PORT below to match.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

_spec = importlib.util.spec_from_file_location(
    "check_docs_sync", REPO_ROOT / "scripts" / "check_docs_sync.py"
)
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


# ---------------------------------------------------------------------------
# Glob semantics: `*` stays inside a directory, `**` crosses
# ---------------------------------------------------------------------------

def test_single_star_does_not_cross_directories():
    pattern = gate.glob_to_regex("src/pkg/*.py")
    assert pattern.match("src/pkg/module.py")
    assert not pattern.match("src/pkg/sub/module.py"), (
        "`*` crossed a directory boundary — this is the fnmatch bug: one "
        "doc's glob would claim files in subpackages owned by other docs"
    )


def test_double_star_crosses_directories():
    pattern = gate.glob_to_regex("src/lib/**")
    assert pattern.match("src/lib/api.py")
    assert pattern.match("src/lib/providers/client.py")
    assert not pattern.match("src/lib_other/x.py")


def test_exact_path_glob_matches_only_itself():
    pattern = gate.glob_to_regex("scripts/check_docs_sync.py")
    assert pattern.match("scripts/check_docs_sync.py")
    assert not pattern.match("scripts/check_docs_sync_extra.py")
    assert not pattern.match("vendored/scripts/check_docs_sync.py")


def test_glob_ownership_does_not_leak_across_sibling_docs():
    """A parent package's `*` glob must not claim a subpackage's files."""
    ownership = {
        "docs/design_pkg.md": ["src/pkg/*.py"],
        "docs/design_pkg_sub.md": ["src/pkg/sub/**"],
    }
    assert gate.owners_of("src/pkg/sub/impl.py", ownership) == [
        "docs/design_pkg_sub.md"
    ]
    assert gate.owners_of("src/pkg/top.py", ownership) == ["docs/design_pkg.md"]


# ---------------------------------------------------------------------------
# Scope: the doc-sync system governs its own implementation
# PORT: these paths assume the kit defaults for CODE_SCOPES /
# CODE_EXEMPT_PREFIXES. If you edited those constants, mirror the edit here.
# ---------------------------------------------------------------------------

def test_doc_sync_implementation_is_in_scope():
    assert gate.in_scope("scripts/check_docs_sync.py")
    assert gate.in_scope("tests/docs/test_doc_consistency.py")


def test_paths_outside_scope_roots_are_out_of_scope():
    assert not gate.in_scope("tests/unit/test_something.py")
    assert not gate.in_scope("docs/design_doc_sync.md")


def test_exempt_prefixes_and_docs_about_code_are_out_of_scope():
    assert not gate.in_scope("frontend/node_modules/react/index.js")  # PORT
    assert not gate.in_scope("src/generated/schema.py")               # PORT
    assert not gate.in_scope("backend/CLAUDE.md")  # docs-about-code are .md


# ---------------------------------------------------------------------------
# Real ownership map: invariants that hold in any kit install
# ---------------------------------------------------------------------------

def test_skill_templates_are_not_real_ownership_docs():
    """Examples inside docs/skill/design_*.md must not enter the owner map."""
    ownership = gate.build_ownership_map()
    assert "docs/skill/design_template.md" not in ownership


def test_doc_sync_implementation_is_owned_by_its_design_doc():
    """The sync system governs itself: design_doc_sync.md owns gate + tests."""
    ownership = gate.build_ownership_map()
    for path in ("scripts/check_docs_sync.py",
                 "tests/docs/test_ownership_gate.py"):
        assert "docs/design_doc_sync.md" in gate.owners_of(path, ownership), (
            f"{path} has no owner — docs/design_doc_sync.md should declare "
            "`> **Code:** `tests/docs/**`, `scripts/check_docs_sync.py``"
        )


# ---------------------------------------------------------------------------
# Bypass: a trailer line, not a substring
# ---------------------------------------------------------------------------

def test_bypass_matches_trailer_line_only():
    assert gate.BYPASS_LINE.search("refactor: rename\n\ndocs-sync: not-needed\n")
    assert gate.BYPASS_LINE.search("fix\n\nDocs-Sync: not-needed")  # trailer keys are case-insensitive
    assert not gate.BYPASS_LINE.search(
        "explain why we rejected adding docs-sync: not-needed here\n"
    ), "bypass tripped by mid-line prose mention — substring bug is back"
