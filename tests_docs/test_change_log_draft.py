"""
Tier 1 — change_log_draft.md inbox contract (docs/skill/document_maintenance.md).
STARTER version shipped with the governance kit.

The draft log is an inbox, not a journal. Checks enforced:
  1. The only headings are the `# Changelog Draft` title and dated batch
     headings `## YYYY-MM-DD — <topic>` — no "Consumed"/history sections
     (consume = delete; docs/changelog/ and git hold that record).
  2. Batch dates are valid and non-decreasing, so new batches land at the end.
  3. Every batch leads with a `Docs:` line naming the design docs it will
     touch, making the docs pass a checklist instead of a re-read.
  4. A size cap forces a docs pass before the inbox can rot into a journal.

All tests pass vacuously if the draft log does not exist yet.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DRAFT = REPO_ROOT / "docs" / "in_process" / "change_log_draft.md"

TITLE = "# Changelog Draft — inbox"
BATCH_RE = re.compile(r"^## (\d{4})-(\d{2})-(\d{2}) — \S.*$")
MAX_LINES = 120


def _lines() -> list[str] | None:
    if not DRAFT.is_file():
        return None
    return DRAFT.read_text(encoding="utf-8").splitlines()


def _batch_headings(lines: list[str]) -> list[tuple[int, str]]:
    """(1-based line number, heading text) for every `## ` line."""
    return [(i, l) for i, l in enumerate(lines, 1) if l.startswith("## ")]


def test_draft_log_headings_are_title_and_dated_batches_only():
    """Only the fixed title and `## YYYY-MM-DD — <topic>` batch headings may exist."""
    lines = _lines()
    if lines is None:
        return
    assert lines and lines[0] == TITLE, (
        f"change_log_draft.md must start with `{TITLE}` (line 1 is: {lines[0] if lines else '<empty>'!r})"
    )
    failures = []
    for i, line in enumerate(lines[1:], 2):
        if not line.startswith("#"):
            continue
        if line.startswith("## "):
            if not BATCH_RE.match(line):
                failures.append(
                    f"line {i}: `{line}` — batch headings must be `## YYYY-MM-DD — <topic>`; "
                    "a 'Consumed'/history section means the batch should have been deleted instead"
                )
        else:
            failures.append(f"line {i}: `{line}` — only `## ` batch headings are allowed below the title")
    assert not failures, "Draft-log heading violations:\n" + "\n".join(failures)


def test_draft_log_batch_dates_valid_and_appended_in_order():
    """Batch dates parse as real dates and never decrease — append at the end only."""
    lines = _lines()
    if lines is None:
        return
    failures = []
    prev: date | None = None
    for i, heading in _batch_headings(lines):
        m = BATCH_RE.match(heading)
        if not m:
            continue  # shape reported by the headings test
        try:
            d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
        except ValueError:
            failures.append(f"line {i}: `{heading}` — not a real calendar date")
            continue
        if prev is not None and d < prev:
            failures.append(
                f"line {i}: `{heading}` — dated before the batch above it; new batches are appended at the end"
            )
        prev = d
    assert not failures, "Draft-log batch-date violations:\n" + "\n".join(failures)


def test_draft_log_batches_lead_with_docs_line():
    """The first content line of every batch names the design docs it will touch."""
    lines = _lines()
    if lines is None:
        return
    failures = []
    for i, heading in _batch_headings(lines):
        first = next((l for l in lines[i:] if l.strip() and not l.startswith("#")), "")
        if not first.startswith("Docs:"):
            failures.append(
                f"line {i}: `{heading}` — first line of a batch must be `Docs: <affected design docs>` "
                "(`Docs: TBD` if unknown); if no doc would change, the facts fail the recording bar"
            )
    assert not failures, "Draft-log batches missing their Docs: line:\n" + "\n".join(failures)


def test_draft_log_within_size_cap():
    """An overflowing inbox means a docs pass is overdue — absorb batches, then delete them."""
    lines = _lines()
    if lines is None:
        return
    assert len(lines) <= MAX_LINES, (
        f"change_log_draft.md is {len(lines)} lines (cap {MAX_LINES}); run a docs pass: absorb open batches "
        "into their design docs + docs/changelog/, then delete the consumed batches"
    )
