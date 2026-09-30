"""
L3 freshness pin — the L2↔L3 edge (docs/design_doc_sync.md §3.1).

Optional governance-kit module, installed with `install.py --with-l3`. Add it
when a human-intuition layer (L3) exists: pages that retell an L2 design doc
for people. Until then this file collects no tests and stays green.

Each L3 page pins, in its frontmatter, the **content hash** of every L2 source
it was aligned to (first 12 hex of sha256 over the source's bytes):

    l3_sources:
      - doc: docs/design_auth.md
        hash: "8f04c1a2b9d3"

Pins are hash-only: nothing forces a `**Version:**` bump when a design doc's
prose changes, so a version pin would stay green across unbumped edits. If a
pinned source declares a `**Version:**` header, the page text must cite that
live version, so a visible version label cannot lag a bumped pin.

**When this fails.** A red pin means the source moved, not that the page is
necessarily wrong. Re-read the source diff, then take exactly one path:
  * still accurate → bump the pin (the bump is the "I looked" record);
  * drifted → fix the page, then bump the pin;
  * cannot re-align now → add `l3_stale: "<what is missing, against which
    source version>"` to the frontmatter and leave the pin unbumped. A stale
    page is exempt from pin checks; the marker carries the truth until the
    debt is paid and the marker removed.

**Mechanism companions.** When a design doc has a
`docs/architecture/mechanism_*.md` companion (design_doc_sync.md §7.1), a page
that pins the contract must pin the companion too. The edge is read from the
mechanism doc's own `> **Engineering Contract:**` line. The stale marker does
not waive this rule.

Prose drift a hash bump cannot see is the `/doc-audit` skill's job (Tier 4).
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]

# PORT: where your L3 pages live (repo-relative). Pages are *.md / *.mdx files
# with the frontmatter above; pages without `l3_sources` are ignored.
L3_ROOTS = [REPO_ROOT / "site" / "docs"]
MECHANISM_DIR = REPO_ROOT / "docs" / "architecture"

FRONTMATTER = re.compile(r"\A---\n(.*?)\n---", re.S)
VERSION_HEADER = re.compile(r"^>\s*\*\*Version:\*\*\s*([0-9][0-9A-Za-z.\-]*)", re.M)
ENGINEERING_CONTRACT = re.compile(r"^>\s*\*\*Engineering Contract:\*\*\s*(.+)$", re.M)
DESIGN_DOC_PATH = re.compile(r"docs/[\w/\-.]*design_[\w\-.]+\.md")
HASH_LEN = 12


def _frontmatter(text: str) -> dict:
    m = FRONTMATTER.match(text)
    return (yaml.safe_load(m.group(1)) or {}) if m else {}


def _short_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:HASH_LEN]


def _pages_with_sources() -> list[Path]:
    pages = sorted(
        p for root in L3_ROOTS if root.exists()
        for p in [*root.rglob("*.md"), *root.rglob("*.mdx")]
    )
    return [p for p in pages
            if isinstance(_frontmatter(p.read_text(encoding="utf-8")).get("l3_sources"), list)]


def _mechanism_companions() -> dict[str, str]:
    """design-doc relpath -> mechanism-doc relpath, from each mechanism doc's
    `> **Engineering Contract:**` line."""
    pairs: dict[str, str] = {}
    if not MECHANISM_DIR.exists():
        return pairs
    for doc in sorted(MECHANISM_DIR.glob("mechanism_*.md")):
        m = ENGINEERING_CONTRACT.search(doc.read_text(encoding="utf-8"))
        if m:
            for design_doc in DESIGN_DOC_PATH.findall(m.group(1)):
                pairs[design_doc] = doc.relative_to(REPO_ROOT).as_posix()
    return pairs


PAGES = _pages_with_sources()


def _page_id(page: Path) -> str:
    return page.relative_to(REPO_ROOT).as_posix()


@pytest.mark.parametrize("page", PAGES, ids=_page_id)
def test_l3_source_schema_is_wellformed(page: Path):
    """Every source pins a content hash against an existing doc; a stale
    marker, when present, must say what is missing."""
    fm = _frontmatter(page.read_text(encoding="utf-8"))
    for src in fm["l3_sources"]:
        assert isinstance(src, dict) and "doc" in src, (
            f"{_page_id(page)}: an l3_sources entry is missing `doc`")
        assert (REPO_ROOT / src["doc"]).exists(), (
            f"{_page_id(page)}: pinned source does not exist: {src['doc']}")
        assert "hash" in src, (
            f"{_page_id(page)}: source `{src['doc']}` has no `hash:` pin — add "
            f"`hash: \"<first {HASH_LEN} hex of sha256(doc bytes)>\"`.")
    if "l3_stale" in fm:
        assert isinstance(fm["l3_stale"], str) and fm["l3_stale"].strip(), (
            f"{_page_id(page)}: `l3_stale` must be a non-empty reason — what is "
            f"missing, against which source version.")


@pytest.mark.parametrize("page", PAGES, ids=_page_id)
def test_l3_pins_mechanism_companion(page: Path):
    """A page that retells a contract must also pin its mechanism companion.
    One-way: retelling a mechanism doc alone is allowed."""
    fm = _frontmatter(page.read_text(encoding="utf-8"))
    pinned = {src["doc"] for src in fm["l3_sources"] if isinstance(src, dict) and "doc" in src}
    missing = [(d, m) for d, m in sorted(_mechanism_companions().items())
               if d in pinned and m not in pinned]
    assert not missing, (
        f"\n{_page_id(page)} pins an L2 contract without its mechanism companion:\n"
        + "\n".join(f"  {d} → also pin {m}" for d, m in missing)
        + "\nAdd the companion to `l3_sources` and retell it (design_doc_sync.md §3.1).")


@pytest.mark.parametrize("page", PAGES, ids=_page_id)
def test_l3_pins_match_live_sources(page: Path):
    """Each pinned source still matches the hash this page aligned to, and a
    live `**Version:**` label is cited in the page."""
    text = page.read_text(encoding="utf-8")
    fm = _frontmatter(text)
    if "l3_stale" in fm:
        pytest.skip(f"declared stale: {fm['l3_stale']!r}")

    failures: list[str] = []
    for src in fm["l3_sources"]:
        target = REPO_ROOT / src["doc"]
        if not target.exists() or "hash" not in src:
            continue  # the schema test owns existence and pin shape
        live = _short_hash(target)
        if live != str(src["hash"]):
            failures.append(f"  {src['doc']}: pinned {str(src['hash'])!r}, live {live!r}")
            continue
        m = VERSION_HEADER.search(target.read_text(encoding="utf-8"))
        if m and m.group(1) not in text:
            failures.append(f"  {src['doc']}: live version {m.group(1)!r} is not cited in the page")

    assert not failures, (
        f"\n{_page_id(page)} is pinned to L2 sources that have moved:\n"
        + "\n".join(failures)
        + "\n\nRe-read the source diff, then: still accurate → bump the pin; drifted →\n"
          "fix the page, then bump; can't re-align now → add `l3_stale: \"<what is\n"
          "missing>\"` and leave the pin unbumped (design_doc_sync.md §3.1).")
