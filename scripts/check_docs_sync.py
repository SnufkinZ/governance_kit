#!/usr/bin/env python3
"""
Tier 3 — design-doc ownership gate (design_doc_sync.md §4). PORTABLE version.

Builds the code-path -> owning-design-doc map from `> **Code:**` frontmatter
lines in design docs, then checks a git diff range: every changed code file
that has owners requires at least ONE owner doc to be changed in the same
range. Bypass with a `docs-sync: not-needed` trailer (the bypass itself is
the audit trail). The trailer is scoped to its own commit: it waves only
files touched exclusively by trailer-carrying commits — a violation from a
plain commit or from uncommitted changes is never absorbed by someone
else's trailer.

Work in progress does not fail the gate. A violation whose changes exist
only in the working tree is reported as DOCS OWED and exits 0: the doc pass
belongs at the end of a change, not against code that is still moving. The
debt is never waived — committing those changes puts them back in the range
as hard violations.

PORTING: this file has no domain knowledge. Adjust only CODE_SCOPES,
CODE_EXEMPT_PREFIXES and (if you import foreign docs) DOC_CONTROL_EXCLUDE for
your repo's layout, and DOCS if design docs do not live under `docs/`.

Usage:
    python scripts/check_docs_sync.py                  # diff against origin/main (or main)
    python scripts/check_docs_sync.py --base <ref>     # explicit base
    python scripts/check_docs_sync.py --warn-only      # report but exit 0  (Phase 0 mode)
    python scripts/check_docs_sync.py --json           # machine-readable map + pairs

Exit codes: 0 ok / bypassed / docs owed / warn-only; 1 violations; 2 setup error.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOCS = REPO_ROOT / "docs"

CODE_LINE = re.compile(r"^>\s*\*\*Code:\*\*\s*(.+)$", re.M)
GLOB_TOKEN = re.compile(r"`([^`]+)`")
BYPASS_TRAILER = "docs-sync: not-needed"
# The bypass must be a trailer *line*, not a substring mentioned in prose.
BYPASS_LINE = re.compile(rf"^{re.escape(BYPASS_TRAILER)}\s*$", re.M | re.I)

# ── PORT THESE TWO for your repo ──────────────────────────────────────────────
# Only changes inside these roots require a doc owner. Keep the doc-sync system's
# own implementation (scripts/, tests/docs/) in scope so it governs itself.
CODE_SCOPES = ("src/", "backend/", "frontend/", "scripts/", "tests/docs/")
# Changes here never require a doc owner (generated / runtime / vendored).
# An exempt prefix only has effect if it sits UNDER one of CODE_SCOPES —
# a path outside every scope root is already out of scope.
CODE_EXEMPT_PREFIXES = ("frontend/node_modules/", "src/generated/")
# ──────────────────────────────────────────────────────────────────────────────

# docs/ subdirectories whose design_*.md never own code here. `archive` is
# frozen history and `skill` holds templates with example `> **Code:**` lines.
# `reference` holds imported *foreign* design docs: their globs describe another
# repo, but paths like `backend/api/**` may exist here too, so a foreign doc
# would become a satisfiable co-owner and silently absorb violations meant for
# the local owning doc. Keep in step with DOC_CONTROL_EXCLUDE in tests/docs/.
DOC_CONTROL_EXCLUDE = {"archive", "skill", "reference"}


def _git(*args: str) -> str:
    result = subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"git {' '.join(args)} failed: {result.stderr.strip()}", file=sys.stderr)
        sys.exit(2)
    return result.stdout


def build_ownership_map() -> dict[str, list[str]]:
    """design-doc relpath -> list of code globs, from `> **Code:**` lines."""
    owners: dict[str, list[str]] = {}
    for doc in sorted(DOCS.rglob("design_*.md")):
        if DOC_CONTROL_EXCLUDE & set(doc.relative_to(DOCS).parts):
            continue
        m = CODE_LINE.search(doc.read_text(encoding="utf-8"))
        if not m:
            continue  # contract/index docs deliberately own no code
        globs = GLOB_TOKEN.findall(m.group(1))
        if globs:
            # POSIX separators: git path output is POSIX, so keys must be too
            # (str() would produce backslash keys on Windows).
            owners[doc.relative_to(REPO_ROOT).as_posix()] = globs
    return owners


def changed_files(base: str) -> list[str]:
    """Committed + staged + working-tree changes relative to base."""
    names: set[str] = set()
    for args in (["diff", "--name-only", f"{base}...HEAD"],
                 ["diff", "--name-only", "HEAD"],
                 ["diff", "--name-only", "--cached"]):
        names |= {l for l in _git(*args).splitlines() if l.strip()}
    return sorted(names)


def uncommitted_files() -> set[str]:
    """Staged + working-tree changes — changes that belong to no commit, so no
    commit's trailer can vouch for them."""
    names: set[str] = set()
    for args in (["diff", "--name-only", "HEAD"],
                 ["diff", "--name-only", "--cached"]):
        names |= {l for l in _git(*args).splitlines() if l.strip()}
    return names


def commit_manifest(base: str) -> list[tuple[str, list[str]]]:
    """(full message, changed files) for every commit in base..HEAD.

    Combined merge diffs attribute paths whose result differs from every
    parent to the merge itself. Paths inherited unchanged from a parent keep
    that parent's commit history and bypass eligibility; a clean merge does
    not revoke its source commits' trailers. Disable rename detection so old
    and new paths remain separate ownership claims.
    """
    # NUL cannot appear in a commit message, so it safely delimits records;
    # \x01 separates the message from the --name-only file list.
    raw = _git("log", f"{base}..HEAD", "-c", "--no-renames",
               "--name-only", "--format=%x00%B%x01")
    manifest: list[tuple[str, list[str]]] = []
    for record in raw.split("\x00"):
        if "\x01" not in record:
            continue
        message, _, files = record.partition("\x01")
        manifest.append(
            (message, [l for l in files.splitlines() if l.strip()])
        )
    return manifest


def bypass_eligible_files(manifest: list[tuple[str, list[str]]]) -> set[str]:
    """Files touched ONLY by trailer-carrying commits. A file also touched by a
    plain commit stays gated — one commit's trailer never vouches for another
    commit's changes."""
    waved: set[str] = set()
    plain: set[str] = set()
    for message, files in manifest:
        (waved if BYPASS_LINE.search(message) else plain).update(files)
    return waved - plain


def committed_files(manifest: list[tuple[str, list[str]]]) -> set[str]:
    """Every file touched by some commit in the range."""
    seen: set[str] = set()
    for _message, files in manifest:
        seen.update(files)
    return seen


_GLOB_CACHE: dict[str, re.Pattern[str]] = {}


def glob_to_regex(glob: str) -> re.Pattern[str]:
    """Compile an ownership glob with directory-aware semantics.

    `**` crosses directory boundaries; `*` and `?` do not. (fnmatch lets `*`
    match `/`, which makes `pkg/sub/*.py` wrongly claim files in sub-subpackages
    owned by other docs.)
    """
    cached = _GLOB_CACHE.get(glob)
    if cached is not None:
        return cached
    parts: list[str] = []
    i = 0
    while i < len(glob):
        if glob.startswith("**", i):
            parts.append(".*")
            i += 2
        elif glob[i] == "*":
            parts.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            parts.append("[^/]")
            i += 1
        else:
            parts.append(re.escape(glob[i]))
            i += 1
    pattern = re.compile("".join(parts) + r"\Z")
    _GLOB_CACHE[glob] = pattern
    return pattern


def owners_of(path: str, ownership: dict[str, list[str]]) -> list[str]:
    return [doc for doc, globs in ownership.items()
            if any(glob_to_regex(g).match(path) for g in globs)]


def in_scope(path: str) -> bool:
    """Does a changed file require a design-doc owner?"""
    return (path.startswith(CODE_SCOPES)
            and not path.startswith(CODE_EXEMPT_PREFIXES)
            and not path.endswith(".md"))  # docs-about-code are not code


def resolve_base(explicit: str | None) -> str:
    if explicit:
        return explicit
    for candidate in ("origin/main", "origin/master", "main", "master"):
        if subprocess.run(["git", "rev-parse", "--verify", "--quiet", candidate],
                          cwd=REPO_ROOT, capture_output=True).returncode == 0:
            return candidate
    print("No base ref found (origin/main, origin/master, main, master); "
          "pass --base. A brand-new repo needs at least one commit first.",
          file=sys.stderr)
    sys.exit(2)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", help="git base ref to diff against")
    parser.add_argument("--warn-only", action="store_true", help="never exit 1")
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit ownership map + changed-file pairing as JSON "
                             "(unfiltered: owed and bypassed files count as violations)")
    args = parser.parse_args()

    base = resolve_base(args.base)
    ownership = build_ownership_map()
    changed = changed_files(base)
    changed_set = set(changed)

    code_changes = [f for f in changed if in_scope(f)]

    violations: list[tuple[str, list[str]]] = []   # (code file, unsatisfied owners)
    satisfied: list[tuple[str, list[str]]] = []
    unowned: list[str] = []
    for path in code_changes:
        own = owners_of(path, ownership)
        if not own:
            unowned.append(path)
        elif any(doc in changed_set for doc in own):
            satisfied.append((path, own))
        else:
            violations.append((path, own))

    if args.as_json:
        print(json.dumps({
            "base": base,
            "ownership_map": ownership,
            "satisfied": satisfied,
            "violations": violations,
            "unowned": unowned,
        }, indent=2))
        return 0

    print(f"docs-sync gate - base: {base}, changed files: {len(changed)}, "
          f"code changes in scope: {len(code_changes)}")
    if satisfied:
        print(f"\n  in sync ({len(satisfied)}):")
        for path, own in satisfied:
            print(f"    {path}  <->  {', '.join(own)}")
    if unowned:
        print(f"\n  no design-doc owner yet ({len(unowned)}) - consider adding "
              f"a `> **Code:**` line to the relevant design doc:")
        for path in unowned:
            print(f"    {path}")
    owed: list[tuple[str, list[str]]] = []
    if violations:
        manifest = commit_manifest(base)
        uncommitted = uncommitted_files()
        eligible = bypass_eligible_files(manifest) - uncommitted
        waved = [(p, own) for p, own in violations if p in eligible]
        violations = [(p, own) for p, own in violations if p not in eligible]
        if waved:
            print(f"\n  bypassed ({len(waved)}) - touched only by "
                  f"`{BYPASS_TRAILER}` commits (the trailer is the audit trail):")
            for path, own in waved:
                print(f"    {path}  ->  {', '.join(own)}")

        # A file whose changes live only in the working tree is unfinished work,
        # not a desync: the doc pass is scheduled for the end of the change, so
        # failing here would only push an agent into writing docs against code
        # that is still moving. The debt is reported, never waived - the moment
        # these changes are committed they re-enter the range as hard violations.
        in_a_commit = committed_files(manifest)
        owed = [(p, own) for p, own in violations
                if p in uncommitted and p not in in_a_commit]
        violations = [(p, own) for p, own in violations if (p, own) not in owed]

    if owed:
        print(f"\n  DOCS OWED ({len(owed)}) - uncommitted work in progress. Do NOT "
              f"update these docs yet; write them in one pass when the change is "
              f"final, before committing:")
        for path, own in owed:
            print(f"    {path}  ->  {', '.join(own)}")

    if violations:
        print(f"\n  VIOLATIONS ({len(violations)}) - code changed, owning design doc untouched:")
        for path, own in violations:
            print(f"    {path}  ->  {', '.join(own)}")
        if args.warn_only:
            print("\n  (warn-only: reporting but not failing - Phase 0 mode)")
            return 0
        print(f"\n  Fix: update the owning design doc in the same change, or - if the "
              f"code change truly has no design impact - add a `{BYPASS_TRAILER}` "
              f"trailer to the commit that carries it, explaining why. The trailer "
              f"covers only its own commit's files.")
        return 1

    if owed:
        print("\n  OK - no committed desync (see DOCS OWED above).")
    else:
        print("\n  OK - no unsatisfied design-doc owners.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
