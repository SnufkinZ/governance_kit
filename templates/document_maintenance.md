## Documentation Update Workflow

**The governing rule: docs are written once, at the end, on command.** Implementation is iterative — a feature is typically reworked over several rounds, reviewed by several agents, before it settles. Documenting an intermediate state costs a full doc pass for prose that the next round invalidates, and leaves a trail of changelog entries for states the system was never really in.

1. **While the work is in progress, do not touch the docs.**
   Iterate on code and tests freely. Do **not** edit `design_*.md`, do **not** add a `docs/changelog/` entry, do **not** bump a `**Version:**` header, and do not stage a summary of the work anywhere. The uncommitted diff plus the code is a complete and always-accurate record of what changed — it cannot rot, and it needs no maintenance. This holds however many review rounds the change takes and whether or not a fresh agent picks the work up.

   The Tier 3 gate agrees: while the changes are uncommitted it reports them as **DOCS OWED** and exits 0. Seeing that list is not an instruction to write docs now — it is the receipt for the debt you will settle in step 3.

2. **Record only what the diff cannot carry, and only where it belongs.**
   Two things survive no diff: *why* a decision was taken, and what was deliberately left open. Those go to the doc that owns them — the relevant `docs/in_process/` plan or problem doc, or an ADR for a real decision. They do not go into a design doc (not settled yet) and they do not go into a scratch buffer. Everything else — files added, signatures changed, tests added — is in the diff already; restating it is duplicated work that goes stale.

   **Apply the design-impact threshold before touching L2/L3.** A change that neither adds, removes, nor changes a documented contract — including API behavior, state semantics, persistence format/compatibility, or architecture concepts — does **not** update an L2 design document, its changelog/version, or any L3 page. Ordinary bug fixes, race repairs, refactors, and internal control-flow or error-handling changes stay in code and tests **when they preserve the documented contract**. Removing an API or changing existing semantics crosses the threshold even without adding a new concept. When Tier 3 maps a contract-preserving change to an owner document, record the reason in the commit body and add an exact `docs-sync: not-needed` trailer line to the commit carrying those files; do not edit the owner merely to satisfy the mechanical gate.

3. **Write the docs in one pass, after the change is final and the human has given the command.**
   The trigger is explicit: the behavior is settled, and the human says to document it. Then read the full diff, the code, and the affected docs, and update in a single pass — design docs, then one `docs/changelog/` entry, then the `**Version:**` bump. Run `scripts/check_docs_sync.py` at the end: with the work committed, anything still unsynced is now a hard failure, so nothing quietly slips through.

4. **One changelog entry per landed change, not per commit.**
   A changelog entry records a contract change that landed, not the path taken to it. Rounds of debugging, review fixes, and reverts within one feature collapse into the single entry that describes the end state.

5. **Write formal docs as current design references.**
   Describe the current system accurately and concisely. Convert raw implementation facts into timeless design prose — a design doc reads as if the system has always worked this way.

6. **Keep history out of formal docs.**
   Put implementation history, dates, step records, and “what changed” narratives in changelogs, ADRs, or in-process docs, not in formal design docs.

7. **Use the final documentation pass only for cleanup.**
   At project close, only compress, deduplicate, remove stale terms, and check consistency. The final pass must not be the first time major formal documentation is written.

---

## Automated Sync Enforcement

The discipline above is backed by automated checks so a missed update fails loudly instead of rotting silently. The full design is `docs/design_doc_sync.md`; in short:

- **Before pushing**, run `python scripts/check_docs_sync.py`. If you changed code that a `design_*.md` owns (declared via its `> **Code:**` header), the gate requires you to update that design doc in the same change — or to add a `docs-sync: not-needed` trailer to the commit that carries it, stating why no doc change was needed. The trailer covers only its own commit's files. Uncommitted work in progress is listed as **DOCS OWED** and does not fail the gate (step 1); committing it makes the same files hard violations, so the debt is deferred, never waived.
- **`pytest tests/docs/`** enforces the mechanical contracts: CLAUDE.md file trees match the filesystem, markdown links resolve, in_process docs carry the standard head + Track section, the priority board does not contradict a doc's own Status, and every path-shaped `> **Code:**` claim matches a real file. When you add/rename/move a file or finish a plan, these tests tell you exactly which map to update.
- **At milestones**, run the `/doc-audit` skill for semantic drift the mechanical checks cannot see (prose describing a mechanism the code no longer implements). It writes findings to `docs/audit/`.
