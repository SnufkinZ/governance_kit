"""
Tier 2 — truth-propagation contradiction checks (design_doc_sync.md §3).
STARTER version shipped with the governance kit — extend as conventions grow.

Tier 1 verifies structure; this file verifies that recorded truth has
propagated. The failure mode it targets: a doc's own Status records "landed",
but an aggregation layer (priority board, changelog, version header) still
claims otherwise.

Checks enforced:
  1. A doc whose Status is terminal (Implemented/Completed/Superseded) must
     not be the subject of an Active-priority-table row.
  2. An in_process doc cited as done in the Completed section must carry a
     terminal Status in its own head.
  3. The priority board snapshot may not lag the newest recorded event by
     more than SNAPSHOT_MAX_LAG_DAYS.
  4. A design doc's **Version:** header must appear in its changelog file.

All checks are vacuously green in a fresh install and start biting as soon
as the convention they guard is first used.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
IN_PROCESS = DOCS / "in_process"
CHANGELOG = DOCS / "changelog"
PRIORITY = IN_PROCESS / "priority.md"

SNAPSHOT_MAX_LAG_DAYS = 14  # board refresh cadence; tune to your sprint length
DOC_CONTROL_EXCLUDE = {"reference"}  # imported external docs; see test_doc_consistency.py

# Anchored: the Status *opens* with a terminal word ("Implemented — ...").
# Phase-partial statuses ("Phase 1 implemented; Phase 2 deferred") and
# template non-terminals ("To be completed") do not match. Used where a match
# accuses the board of contradiction, so it must be strict.
TERMINAL_ANCHORED = re.compile(
    r"\*\*Status:\*\*\s*\**\s*(Implemented|Completed|Superseded)\b", re.I
)
# Loose: any completion signal anywhere in the Status line (except the
# template non-terminal "to be completed"). Used where a match merely
# confirms agreement with the board, so partial completion counts.
TERMINAL_LOOSE = re.compile(
    r"\*\*Status:\*\*[^\n]*?(?<!to\sbe\s)\b(implemented|completed|superseded)\b", re.I
)
STATUS_LINE = re.compile(r"\*\*Status:\*\*([^\n]*)")
DATE_VALUE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")
SNAPSHOT = re.compile(r"\*\*Snapshot date:\*\*\s*(\d{4}-\d{2}-\d{2})")
VERSION_LINE = re.compile(r">\s*\*\*Version:\*\*\s*(\S+)")
ROW_SUBJECT = re.compile(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)")
BULLET_LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

PLAN_PREFIXES = ("plan_", "problem_", "change_", "feature_")


def _section(text: str, heading_prefix: str) -> str:
    """Body of the first `## <heading_prefix>...` section (to the next `## `)."""
    pattern = re.compile(
        rf"^## {re.escape(heading_prefix)}[^\n]*$(.*?)(?=^## |\Z)", re.M | re.S
    )
    m = pattern.search(text)
    return m.group(1) if m else ""


def _doc_status(path: Path) -> str:
    m = STATUS_LINE.search(path.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else ""


def _board() -> str | None:
    return PRIORITY.read_text(encoding="utf-8") if PRIORITY.is_file() else None


# ---------------------------------------------------------------------------
# 1 + 2. Status <-> priority board
# ---------------------------------------------------------------------------

def test_active_table_subjects_are_not_terminal():
    """A doc the board still treats as active work must not self-report done."""
    board = _board()
    if board is None:
        return
    failures = []
    for line in _section(board, "Active priority table").splitlines():
        m = ROW_SUBJECT.match(line.strip())
        if not m:
            continue
        target = (IN_PROCESS / m.group(2).split("#")[0]).resolve()
        if not target.is_file():
            continue  # broken links are Tier 1's job
        head = "\n".join(target.read_text(encoding="utf-8").splitlines()[:15])
        if TERMINAL_ANCHORED.search(head):
            failures.append(
                f"{target.name} has terminal Status `{_doc_status(target)}` "
                f"but still owns an Active-table row — move the row to Completed"
            )
    assert not failures, "Board says active, doc says done:\n" + "\n".join(failures)


def _active_table_subjects(board: str) -> set[Path]:
    subjects = set()
    for line in _section(board, "Active priority table").splitlines():
        m = ROW_SUBJECT.match(line.strip())
        if m:
            subjects.add((IN_PROCESS / m.group(2).split("#")[0]).resolve())
    return subjects


def test_completed_entries_have_terminal_status():
    """A plan cited as done on the board must say so in its own head.

    A bullet's subject is its *first* link only (later links are context).
    Docs that also own an Active-table row are exempt — section-level
    completion of a still-active plan is legitimate.
    """
    board = _board()
    if board is None:
        return
    still_active = _active_table_subjects(board)
    failures = []
    seen: set[Path] = set()
    for line in _section(board, "Completed").splitlines():
        if not line.strip().startswith("- "):
            continue
        m = BULLET_LINK.search(line)
        if not m:
            continue
        href = m.group(2)
        if not Path(href).name.startswith(PLAN_PREFIXES):
            continue
        target = (IN_PROCESS / href.split("#")[0]).resolve()
        if not target.is_file() or target in seen or target in still_active:
            continue
        seen.add(target)
        head = "\n".join(target.read_text(encoding="utf-8").splitlines()[:15])
        if not TERMINAL_LOOSE.search(head):
            failures.append(
                f"{target.relative_to(REPO_ROOT)}: board lists it as Completed but its "
                f"Status is `{_doc_status(target)}` — update the doc head"
            )
    assert not failures, "Board says done, doc head disagrees:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# 3. Snapshot staleness
# ---------------------------------------------------------------------------

def test_priority_snapshot_not_stale():
    """The board snapshot may lag recorded events by at most SNAPSHOT_MAX_LAG_DAYS.

    "Events" are every `**Date:**` recorded in in_process docs (head + Track
    entries). The board is allowed to lag — refresh is at sprint milestones,
    not per commit — but not indefinitely.
    """
    newest: tuple[date, str] | None = None
    if IN_PROCESS.exists():
        for md in sorted(IN_PROCESS.rglob("*.md")):
            for value in DATE_VALUE.findall(md.read_text(encoding="utf-8")):
                d = date.fromisoformat(value)
                if newest is None or d > newest[0]:
                    newest = (d, md.name)
    if newest is None:
        return  # nothing recorded yet — nothing to lag behind

    board = _board()
    assert board is not None, "in_process docs record events but priority.md is missing"
    m = SNAPSHOT.search(board)
    assert m, "priority.md has no parseable `**Snapshot date:**` (YYYY-MM-DD)"
    snapshot = date.fromisoformat(m.group(1))

    lag = (newest[0] - snapshot).days
    assert lag <= SNAPSHOT_MAX_LAG_DAYS, (
        f"priority.md snapshot ({snapshot}) lags the newest recorded event "
        f"({newest[0]} in {newest[1]}) by {lag} days (max {SNAPSHOT_MAX_LAG_DAYS}). "
        f"Refresh the board rows and the snapshot date together."
    )


# ---------------------------------------------------------------------------
# 4. Design doc version <-> changelog
# ---------------------------------------------------------------------------

SOURCE_DOC_LINK = re.compile(r"Source document:\s*\[[^\]]*\]\(([^)]+)\)")


def _changelog_source(changelog: Path) -> Path | None:
    """Resolve which document a changelog file tracks.

    Preferred: an explicit `Source document: [name](path)` link in the
    changelog. Fallback: a doc under docs/ whose filename equals the
    changelog's stem (docs/changelog/design_foo.md -> docs/**/design_foo.md).
    """
    m = SOURCE_DOC_LINK.search(changelog.read_text(encoding="utf-8"))
    if m:
        candidate = (changelog.parent / m.group(1)).resolve()
        return candidate if candidate.is_file() else None
    for candidate in sorted(DOCS.rglob(changelog.stem + ".md")):
        if CHANGELOG not in candidate.parents and "archive" not in candidate.parts:
            return candidate
    return None


def _changelog_files() -> list[Path]:
    if not CHANGELOG.exists():
        return []
    return [c for c in sorted(CHANGELOG.glob("*.md"))
            if c.name not in {"CLAUDE.md", "README.md"}]


def test_changelogs_map_to_existing_source_docs():
    failures = [f"{c.name}: cannot resolve its source document"
                for c in _changelog_files() if _changelog_source(c) is None]
    assert not failures, (
        "Changelog files with no resolvable source doc (rename to match the "
        "doc's filename or add a `Source document:` link):\n" + "\n".join(failures)
    )


def test_design_doc_version_appears_in_changelog():
    """If a design doc declares **Version:** X, its changelog must record X.

    Iterates *forward* from the design docs (not from the changelog files),
    so a versioned doc with no changelog file at all is a failure — history
    lives in docs/changelog/, not inline.
    """
    changelog_by_source: dict[Path, Path] = {}
    for changelog in _changelog_files():
        source = _changelog_source(changelog)
        if source is not None:
            changelog_by_source[source.resolve()] = changelog

    failures = []
    for doc in sorted(DOCS.rglob("design_*.md")):
        # archive/ is frozen history; skill/ holds authoring templates with
        # placeholder heads; reference/ is imported external material;
        # changelog/ files are histories, not design docs.
        excluded = {"archive", "skill", *DOC_CONTROL_EXCLUDE}
        if excluded & set(doc.relative_to(DOCS).parts) or CHANGELOG in doc.parents:
            continue
        m = VERSION_LINE.search(doc.read_text(encoding="utf-8"))
        if not m:
            continue  # unversioned doc — nothing to cross-check
        version = m.group(1)
        changelog = changelog_by_source.get(doc.resolve())
        if changelog is None:
            failures.append(
                f"{doc.relative_to(REPO_ROOT)} declares Version {version} but has "
                f"no changelog file under docs/changelog/ — create one (history "
                f"belongs there, not inline)"
            )
            continue
        pattern = re.compile(rf"(?<![\w.])v?{re.escape(version)}(?![\w.])")
        if not pattern.search(changelog.read_text(encoding="utf-8")):
            failures.append(
                f"{doc.relative_to(REPO_ROOT)} declares Version {version} but "
                f"{changelog.name} has no `{version}` entry — add the changelog "
                f"entry or correct the stale header"
            )
    assert not failures, "Version header / changelog mismatches:\n" + "\n".join(failures)
