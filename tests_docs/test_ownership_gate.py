"""
Tier 3 unit tests — pin the ownership-gate semantics (design_doc_sync.md §4).

Every pinned behavior guards against a real bug found in the origin project:
fnmatch-style `*` crossing `/` (one doc's glob silently claiming files in a
subpackage owned by another doc), a bypass check that plain prose could trip,
a bypass trailer on one commit absorbing another commit's violation, and a
`> **Code:**` line naming a directory rather than a glob — owning nothing while
the gate read green. Temporary Git repositories also exercise the CLI's
working-tree debt and merge-commit bypass behavior.

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
import subprocess
import sys
from pathlib import Path

import pytest

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


def test_reference_docs_are_not_real_ownership_docs():
    """Imported foreign design docs under docs/reference/ must not enter the
    owner map: their `> **Code:**` globs describe another repo, but overlapping
    paths (e.g. `backend/api/**`) may exist here too, so a foreign doc would
    become a satisfiable co-owner and silently absorb Tier 3 violations."""
    ownership = gate.build_ownership_map()
    foreign = [doc for doc in ownership if doc.startswith("docs/reference/")]
    assert foreign == [], (
        f"foreign reference docs entered the ownership map: {foreign}"
    )


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
# An owner token that matches nothing: the gate reads green while owning zero
# ---------------------------------------------------------------------------

def test_a_directory_shaped_owner_token_claims_nothing():
    """`src/pkg/` is not a glob — it matches no file at all.

    This is the failure mode the next test guards against in the real map: an
    unowned file cannot owe a document, so the gate reports zero violations
    precisely because the claim is empty. Green means "nobody owes anything",
    not "everything is in sync".
    """
    pattern = gate.glob_to_regex("src/pkg/")
    assert not pattern.match("src/pkg/state.py")
    # It matches the bare directory string, which git never reports as a file.
    assert gate.glob_to_regex("src/pkg/**").match("src/pkg/state.py")


def test_every_path_shaped_owner_token_matches_a_live_file():
    """Every `> **Code:**` token that looks like a repository path must claim
    at least one real file.

    Only tokens containing `/` are checked. A `> **Code:**` line may also carry
    bare filenames inside explanatory prose (`fields.py`, `state.py`); those
    have no directory component, cannot be mistaken for a path claim, and
    cannot silently absorb a violation. A slash-bearing token that matches
    nothing is always a defect — a trailing-slash directory, a typo, or a path
    left behind by moved code.
    """
    listed = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=REPO_ROOT, capture_output=True, text=True, check=True,
    ).stdout.split()
    live = [path for path in listed if (REPO_ROOT / path).is_file()]
    empty = [
        (doc, glob)
        for doc, globs in gate.build_ownership_map().items()
        for glob in globs
        if "/" in glob
        and not any(gate.glob_to_regex(glob).match(f) for f in live)
    ]
    assert empty == [], (
        "these ownership claims match no tracked file, so every file they were "
        f"meant to cover is unowned and silently exempt: {empty}"
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


# ---------------------------------------------------------------------------
# Bypass scope: a trailer covers only its own commit's files
# ---------------------------------------------------------------------------

TRAILER = "typo fix\n\ndocs-sync: not-needed\n"
PLAIN = "feat: real change\n"


def test_trailer_waves_only_its_own_commits_files():
    eligible = gate.bypass_eligible_files([
        (TRAILER, ["src/core/paths.py"]),
        (PLAIN, ["src/api/routes.py"]),
    ])
    assert eligible == {"src/core/paths.py"}, (
        "a trailer on one commit absorbed another commit's violation — "
        "the range-global bypass bug is back"
    )


def test_file_touched_by_plain_and_trailer_commits_stays_gated():
    eligible = gate.bypass_eligible_files([
        (TRAILER, ["src/api/routes.py"]),
        (PLAIN, ["src/api/routes.py"]),
    ])
    assert eligible == set(), (
        "a plain commit's change to the same file was waved by a sibling "
        "commit's trailer"
    )


def test_no_trailer_means_nothing_is_eligible():
    assert gate.bypass_eligible_files([(PLAIN, ["a.py"]), (PLAIN, ["b.py"])]) == set()


# ---------------------------------------------------------------------------
# Real Git histories: unit manifests alone cannot expose Git diff semantics.
# ---------------------------------------------------------------------------

@pytest.fixture
def history(tmp_path, monkeypatch):
    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, capture_output=True, text=True,
            check=True,
        ).stdout.strip()

    git("init", "-b", "main")
    git("config", "user.name", "Gate Test")
    git("config", "user.email", "gate@example.invalid")
    git("config", "commit.gpgsign", "false")
    git("config", "core.hooksPath", str(tmp_path / "empty-hooks"))
    (tmp_path / "src").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "src/core.py").write_text("value = 0\n", encoding="utf-8")
    (tmp_path / "docs/design_core.md").write_text(
        "# Core\n\n> **Code:** `src/**`\n", encoding="utf-8",
    )
    git("add", ".")
    git("commit", "-m", "base")
    base = git("rev-parse", "HEAD")
    monkeypatch.setattr(gate, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(gate, "DOCS", tmp_path / "docs")
    # The integration fixture is independent of a target's PORT settings.
    monkeypatch.setattr(gate, "CODE_SCOPES", ("src/",))
    monkeypatch.setattr(gate, "CODE_EXEMPT_PREFIXES", ())
    monkeypatch.setattr(sys, "argv", ["check_docs_sync.py", "--base", base])
    return tmp_path, git


@pytest.mark.parametrize("staged", [False, True])
def test_uncommitted_debt_becomes_a_violation_when_committed(history, capsys, staged):
    root, git = history
    (root / "src/core.py").write_text("value = 1\n", encoding="utf-8")
    if staged:
        git("add", ".")
    assert gate.main() == 0
    assert "DOCS OWED" in capsys.readouterr().out
    git("add", ".")
    git("commit", "-m", PLAIN)
    assert gate.main() == 1
    assert "VIOLATIONS" in capsys.readouterr().out


@pytest.mark.parametrize("message", [PLAIN, TRAILER])
def test_worktree_edits_cannot_hide_or_inherit_a_commits_waiver(history, capsys, message):
    root, git = history
    (root / "src/core.py").write_text("value = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", message)
    (root / "src/core.py").write_text("value = 2\n", encoding="utf-8")
    assert gate.main() == 1
    output = capsys.readouterr().out
    assert "VIOLATIONS" in output
    assert "DOCS OWED" not in output


def test_cli_trailer_does_not_absorb_another_files_plain_commit(history, capsys):
    root, git = history
    (root / "src/core.py").write_text("value = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", TRAILER)
    (root / "src/other.py").write_text("value = 2\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", PLAIN)
    assert gate.main() == 1
    output = capsys.readouterr().out
    assert "bypassed (1)" in output
    assert "VIOLATIONS (1)" in output
    assert "src/other.py" in output.split("VIOLATIONS", 1)[1]


@pytest.mark.parametrize("merge_edit", ["none", "existing", "new"])
@pytest.mark.parametrize("merge_waiver", [False, True])
def test_merge_owns_its_new_content_but_preserves_inherited_waivers(
    history, capsys, merge_edit, merge_waiver,
):
    root, git = history
    git("checkout", "-b", "side")
    (root / "src/core.py").write_text("value = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", TRAILER)
    git("checkout", "main")
    (root / "unowned.txt").write_text("main branch\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", "unrelated change")
    git("merge", "--no-ff", "--no-commit", "side")
    if merge_edit != "none":
        name = "core.py" if merge_edit == "existing" else "new.py"
        (root / "src" / name).write_text("value = 999\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", TRAILER if merge_waiver else "merge without waiver")
    assert gate.main() == (0 if merge_edit == "none" or merge_waiver else 1)
    output = capsys.readouterr().out
    if merge_edit == "none":
        assert "bypassed (1)" in output
    else:
        assert ("bypassed" if merge_waiver else "VIOLATIONS (1)") in output
        # Even a further worktree edit cannot turn merge debt into DOCS OWED.
        (root / "src" / name).write_text("value = 1000\n", encoding="utf-8")
        assert gate.main() == 1
        assert "DOCS OWED" not in capsys.readouterr().out


def test_merge_trailer_cannot_absorb_plain_source_commit(history, capsys):
    root, git = history
    git("checkout", "-b", "side")
    (root / "src/core.py").write_text("value = 1\n", encoding="utf-8")
    git("add", ".")
    git("commit", "-m", PLAIN)
    git("checkout", "main")
    git("merge", "--no-ff", "side", "-m", TRAILER)
    assert gate.main() == 1
    assert "VIOLATIONS" in capsys.readouterr().out
