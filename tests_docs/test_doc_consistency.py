"""
Tier 1 — mechanical doc-structure consistency (design_doc_sync.md §2).
STARTER version shipped with the governance kit — extend as conventions grow.

Checks enforced:
  1. Every CLAUDE.md file tree matches the directory it describes:
     listed entries exist; immediate children of the directory are listed
     (a tree containing a bare `...` line opts out of the completeness half).
  2. Every control directory in REQUIRED_CLAUDE_DIRS that exists carries a
     CLAUDE.md map (a README does not satisfy it) — the coverage half of the
     map contract.
  3. Every relative markdown link under docs/ resolves to an existing file.
  4. Every in_process plan/problem/change/feature doc carries the required
     head fields (docs/skill/in_process_plan_format.md) and a Track section.
  5. Every top-level in_process plan_*/problem_* doc appears on the
     priority board (priority.md), so no plan can fall off the radar.

All checks are vacuously green in a fresh install and start biting as soon
as the convention they guard is first used.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DOCS = REPO_ROOT / "docs"
IN_PROCESS = DOCS / "in_process"

# Imported external reference docs (docs/reference/) are intentionally outside
# the local doc-sync control system: their maps and links describe another repo.
# Keep in step with DOC_CONTROL_EXCLUDE in scripts/check_docs_sync.py.
DOC_CONTROL_EXCLUDE = {"reference"}

# Directories never walked for CLAUDE.md discovery or completeness checks.
# PORT: add your generated/vendored roots.
PRUNE_DIRS = {
    ".git", ".venv", "venv", ".vscode", ".claude", ".github", ".idea",
    ".pytest_cache", "node_modules", "__pycache__", ".next", "dist", "build",
    "target", "governance-kit", *DOC_CONTROL_EXCLUDE,
}

# Names a CLAUDE.md tree may list but is never *required* to list.
COMPLETENESS_EXEMPT = {
    "CLAUDE.md", "AGENTS.md", "__init__.py", "__pycache__",
    ".DS_Store", "node_modules", "package-lock.json",
}

# Control directories that MUST carry a local CLAUDE.md *if they exist*.
# This is the coverage half of the map contract: the other tests keep an
# existing CLAUDE.md honest; this one keeps a key directory from having none.
# A README does not satisfy it — the loading convention is CLAUDE.md.
# PORT: paths are repo-relative; add code roots (backend/, frontend/, ...) as
# they appear. Listing a dir that does not exist yet is a no-op, not a failure.
REQUIRED_CLAUDE_DIRS = [
    "docs",
    "docs/skill",
    "docs/changelog",
    "docs/decisions",
    "docs/in_process",
    "docs/audit",
]

# Both ASCII (`|--`, `` `-- ``) and box-drawing (├──, └──) tree styles count.
TREE_MARKER = re.compile(r"^(?P<indent>[\s|│`]*)(?:\|--|`--|├──|└──)\s+(?P<name>\S+)")
MD_LINK = re.compile(r"\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
FENCE = re.compile(r"^```")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _iter_files(root: Path, pattern: str):
    """rglob with PRUNE_DIRS respected."""
    if not root.exists():
        return
    for path in sorted(root.rglob(pattern)):
        if any(part in PRUNE_DIRS for part in path.parts):
            continue
        yield path


def _all_claude_mds() -> list[Path]:
    return list(_iter_files(REPO_ROOT, "CLAUDE.md"))


def _fenced_blocks(text: str) -> list[list[str]]:
    """Return the line-lists of every fenced code block."""
    blocks, current, inside = [], [], False
    for line in text.splitlines():
        if FENCE.match(line):
            if inside:
                blocks.append(current)
                current = []
            inside = not inside
            continue
        if inside:
            current.append(line)
    return blocks


def _strip_fenced(text: str) -> str:
    out, inside = [], False
    for line in text.splitlines():
        if FENCE.match(line):
            inside = not inside
            continue
        if not inside:
            out.append(line)
    return "\n".join(out)


BARE_ROOT = re.compile(r"[\w().-]+/$")


def _parse_tree(block: list[str], base_name: str) -> list[tuple[Path, bool]] | None:
    """
    Parse an ASCII file tree into (relative_path, is_dir) entries.
    Returns None if the block is not a tree (fewer than 2 tree-marker lines).
    Depth is derived from marker indentation (4 chars per level).

    A bare `name/` line before the first marker names the tree's root. When
    it is the CLAUDE.md's own directory it adds nothing; when it is a
    subdirectory (an illustrative snippet) entries resolve under it.
    """
    entries, stack = [], []
    marker_lines = [l for l in block if TREE_MARKER.match(l)]
    if len(marker_lines) < 2:
        return None
    root = Path()
    for line in block:
        if TREE_MARKER.match(line):
            break
        bare = line.strip()
        if BARE_ROOT.fullmatch(bare) and bare.rstrip("/") != base_name:
            root = Path(bare.rstrip("/"))
    for line in block:
        m = TREE_MARKER.match(line)
        if not m:
            continue
        depth = len(m.group("indent")) // 4
        name = m.group("name")
        is_dir = name.endswith("/")
        if name.startswith("(") and not is_dir:
            continue  # placeholder annotation, e.g. `-- (created on demand)
        name = name.rstrip("/")
        stack = stack[:depth]
        entries.append((root / Path(*stack, name), is_dir))
        if is_dir:
            stack.append(name)
    return entries


def _tree_is_partial(block: list[str]) -> bool:
    """A tree containing a bare `...` line opts out of completeness."""
    return any(l.strip().rstrip("#").strip() in {"...", "…"} for l in block)


# ---------------------------------------------------------------------------
# 1. CLAUDE.md tree <-> filesystem
# ---------------------------------------------------------------------------

def test_claude_md_trees_entries_exist():
    """Every entry listed in a CLAUDE.md file tree must exist on disk."""
    failures = []
    for claude in _all_claude_mds():
        base = claude.parent
        for block in _fenced_blocks(claude.read_text(encoding="utf-8")):
            entries = _parse_tree(block, base.name)
            if entries is None:
                continue
            for rel, _ in entries:
                if not (base / rel).exists():
                    failures.append(f"{claude.relative_to(REPO_ROOT)}: listed `{rel}` does not exist")
    assert not failures, "Stale CLAUDE.md tree entries:\n" + "\n".join(failures)


def test_claude_md_trees_are_complete():
    """Every immediate child of a CLAUDE.md's directory must appear in its tree."""
    failures = []
    for claude in _all_claude_mds():
        base = claude.parent
        listed: set[str] = set()
        has_tree = False
        partial = False
        for block in _fenced_blocks(claude.read_text(encoding="utf-8")):
            entries = _parse_tree(block, base.name)
            if entries is None:
                continue
            has_tree = True
            partial = partial or _tree_is_partial(block)
            listed |= {entry.parts[0] for entry, _ in entries}
        if not has_tree or partial:
            continue
        for child in base.iterdir():
            name = child.name
            if name.startswith(".") or name in COMPLETENESS_EXEMPT or name in PRUNE_DIRS:
                continue
            if name not in listed:
                failures.append(f"{claude.relative_to(REPO_ROOT)}: `{name}` exists but is not listed")
    assert not failures, "Incomplete CLAUDE.md trees (add the entry or a `...` line):\n" + "\n".join(failures)


def test_control_dirs_have_claude_md():
    """Every control directory that exists must carry a CLAUDE.md, not a README.

    The two tests above keep an *existing* CLAUDE.md accurate; they say nothing
    about a directory that has none. This is that missing coverage half — a key
    directory silently shipping with only a README (or nothing) is the failure
    this pins. Install the kit placeholder for the slot rather than a README.
    """
    failures = []
    for rel in REQUIRED_CLAUDE_DIRS:
        d = REPO_ROOT / rel
        if not d.is_dir():
            continue  # dir not created yet — coverage grows as dirs appear
        if not (d / "CLAUDE.md").is_file():
            has_readme = (d / "README.md").is_file()
            hint = " (has a README — rename it to CLAUDE.md)" if has_readme else ""
            failures.append(f"{rel}/ is missing CLAUDE.md{hint}")
    assert not failures, (
        "Control directories without a CLAUDE.md map:\n" + "\n".join(failures)
    )


# ---------------------------------------------------------------------------
# 2. Markdown links resolve
# ---------------------------------------------------------------------------

# Frozen history and imported reference material may link at since-moved files
# or at another repo's layout.
LINK_CHECK_EXCLUDE = {"archive", *DOC_CONTROL_EXCLUDE}


def test_docs_relative_links_resolve():
    """Every relative markdown link under docs/ must point at an existing file."""
    failures = []
    for md in _iter_files(DOCS, "*.md"):
        rel_parts = set(md.relative_to(DOCS).parts)
        if rel_parts & LINK_CHECK_EXCLUDE:
            continue
        text = _strip_fenced(md.read_text(encoding="utf-8"))
        for target in MD_LINK.findall(text):
            if target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            target_path = target.split("#", 1)[0]
            if not target_path or "<" in target_path:  # template placeholder
                continue
            resolved = (md.parent / target_path).resolve()
            if not resolved.exists():
                failures.append(f"{md.relative_to(REPO_ROOT)}: broken link `{target}`")
    assert not failures, "Broken relative links in docs/:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# 3. in_process head format
# ---------------------------------------------------------------------------

PLAN_PREFIXES = ("plan_", "problem_", "change_", "feature_")
HEAD_FIELDS = ("**Type:**", "**Status:**", "**Priority:**", "**Date:**", "**Owner:**")
HEAD_EXEMPT: set[str] = set()  # PORT: in_process files that match a prefix but are not plans
DATE_RE = re.compile(r"\*\*Date:\*\*\s*(\d{4}-\d{2}-\d{2})")


def _plan_docs() -> list[Path]:
    return [md for md in _iter_files(IN_PROCESS, "*.md")
            if md.name not in HEAD_EXEMPT and md.name.startswith(PLAN_PREFIXES)]


def test_in_process_docs_have_required_head():
    """Every plan/problem/change/feature doc carries the standard head block."""
    failures = []
    for md in _plan_docs():
        head = "\n".join(md.read_text(encoding="utf-8").splitlines()[:15])
        for field in HEAD_FIELDS:
            if field not in head:
                failures.append(f"{md.relative_to(REPO_ROOT)}: missing `{field}` in head")
        if "**Date:**" in head and not DATE_RE.search(head):
            failures.append(f"{md.relative_to(REPO_ROOT)}: `**Date:**` is not YYYY-MM-DD")
    assert not failures, "in_process head-format violations (see docs/skill/in_process_plan_format.md):\n" + "\n".join(failures)


def test_in_process_docs_have_track_section():
    """Every plan/problem/change/feature doc keeps an append-only Track section."""
    failures = []
    for md in _plan_docs():
        if "## Track" not in md.read_text(encoding="utf-8"):
            failures.append(f"{md.relative_to(REPO_ROOT)}: missing `## Track` section")
    assert not failures, "Missing Track sections:\n" + "\n".join(failures)


# ---------------------------------------------------------------------------
# 4. Priority board coverage
# ---------------------------------------------------------------------------

def test_top_level_plans_are_on_priority_board():
    """Every top-level in_process plan_*/problem_* doc must be named in priority.md."""
    plans = [md for md in sorted(IN_PROCESS.glob("*.md"))
             if md.name.startswith(("plan_", "problem_"))] if IN_PROCESS.exists() else []
    board_file = IN_PROCESS / "priority.md"
    if not plans and not board_file.exists():
        return  # fresh repo: nothing to track yet
    assert board_file.exists(), (
        "in_process plans exist but there is no priority.md board — install "
        "the kit placeholder (templates/placeholders/in_process__priority.md)"
    )
    board = board_file.read_text(encoding="utf-8")
    failures = [f"{md.name} is not referenced anywhere in priority.md"
                for md in plans if md.name not in board]
    assert not failures, "Plans missing from the priority board:\n" + "\n".join(failures)
