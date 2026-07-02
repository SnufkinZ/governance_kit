# Changelog Draft — inbox

<!--
INBOX CONTRACT (enforced by tests/docs/test_change_log_draft.py):
- Below this header, only dated batch headings are allowed, shaped exactly
  like "## YYYY-MM-DD — topic" - dates non-decreasing: append new batches
  at the END of the file.
- Every batch leads with a `Docs:` line naming the design docs it will touch
  (`Docs: TBD` if unknown; if no design doc would change, the fact fails the
  recording bar - do not log it, git already records file-level diffs).
- Consume = delete: once a batch is absorbed into docs/changelog/ and the
  design docs, delete the batch. No "Consumed" sections - git is the history.
- 120-line cap: if this file exceeds it, a docs pass is overdue.
-->
