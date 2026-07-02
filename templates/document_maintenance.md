## Documentation Update Workflow

Use a draft-first documentation workflow during implementation.

1. **Maintain a draft log while coding.**  
   During implementation, keep `docs/in_process/change_log_draft.md` updated. The draft log is an **inbox, not a journal** — follow the editing contract embedded in its header comment: append dated batches (`## YYYY-MM-DD — <topic>`) at the end of the file only, and lead every batch with a `Docs:` line naming the design docs the batch will touch. If no design doc would need to change because of a fact, it fails the recording bar — don't log it (git already records file-level diffs).

2. **Record facts only when you are coding.**  
   The draft log must contain raw implementation facts only: files added, classes changed, behavior changes, API changes, validator rules, tests added, design impacts, and unresolved questions. Do not write polished design prose in the draft log.

3. **Update formal docs after all coding work is done and the human approves.**  
   After all required functions or system are implemented and tested, read:
   - `docs/in_process/change_log_draft.md`
   - the actual code
   - the affected existing docs

   Then update the formal docs in one focused pass, using each batch's `Docs:` line as the checklist. **Consume = delete:** once a batch is absorbed, delete it from the draft log — no "Consumed" sections, no marking; `docs/changelog/` and git history are the record of what was absorbed. After a full pass the draft log is just its header again.

4. **Write formal docs as current design references.**  
   When updating formal docs, describe the current system accurately and concisely. Do not copy the draft log directly. Convert raw facts into timeless design prose.

5. **Keep history out of formal docs.**  
   Put implementation history, dates, step records, and “what changed” narratives in changelogs, ADRs, or in-process docs, not in formal design docs.

6. **Use the final documentation pass only for cleanup.**  
   At project close, only compress, deduplicate, remove stale terms, and check consistency. The final pass must not be the first time major formal documentation is written.

---

## Automated Sync Enforcement

The discipline above is backed by automated checks so a missed update fails loudly instead of rotting silently. The full design is `docs/design_doc_sync.md`; in short:

- **Before pushing**, run `python scripts/check_docs_sync.py`. If you changed code that a `design_*.md` owns (declared via its `> **Code:**` header), the gate requires you to update that design doc in the same change — or to add a `docs-sync: not-needed` trailer to a commit message stating why no doc change was needed.
- **`pytest tests/docs/`** enforces the mechanical contracts: CLAUDE.md file trees match the filesystem, markdown links resolve, in_process docs carry the standard head + Track section, the priority board does not contradict a doc's own Status, and the draft log obeys its inbox contract (dated batches, `Docs:` lines, consumed batches deleted, 120-line cap that forces an overdue docs pass). When you add/rename/move a file or finish a plan, these tests tell you exactly which map to update.
- **At sprint milestones**, run the `/doc-audit` skill for semantic drift the mechanical checks cannot see (prose describing a mechanism the code no longer implements). It writes findings to `docs/audit/`.