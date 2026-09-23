---
name: doc-audit
description: Tier-4 semantic doc-code drift audit. Run at sprint milestones (not per commit) to find design docs whose prose no longer matches the code they own — the drift mechanical checks (tests/docs, check_docs_sync.py) provably cannot see. Use when the user asks to audit docs, check doc-code sync deeply, verify documentation accuracy, or after a batch of feature work lands. Writes findings to docs/audit/.
---

# Doc-Audit — Semantic Drift Audit (Tier 4)

> **Install location:** `.claude/skills/doc-audit/SKILL.md` (Claude Code). If
> you use a different agent harness, treat this file as the audit runbook and
> wire it into whatever skill/prompt mechanism that harness has.

This is the judgement layer of the doc-code sync system (`docs/design_doc_sync.md` §5). Tiers 1–3 run in the Docs workflow and catch mechanical desync (missing files, broken links, a board that contradicts a Status, code changed without its doc touched). They **cannot** read meaning, so they miss the most dangerous failure: a design doc that is structurally perfect and internally consistent but **describes a mechanism the code no longer implements** (canonical shape: an auth doc still describing the old token scheme long after the implementation switched).

Your job is to read code and its owning design doc together and report where the prose has drifted from the implementation.

## When to run

- At sprint milestones, or after a batch of feature work has landed.
- When the user explicitly asks to audit documentation accuracy.
- NOT on every commit — this costs model time and is a deliberate, reviewed pass.

## Method

1. **Resolve the audit range.**
   - Look in `docs/audit/` for the most recent `*_doc_sync.md` audit; its date is the lower bound. If none exists, default to the last ~30 days or ask the user for a base ref.
   - Confirm the range with the user if ambiguous: `git log --oneline <base>..HEAD` to show what is covered.

2. **Get the code↔doc pairs that changed.**
   - Run `python scripts/check_docs_sync.py --base <base> --json`.
   - The `ownership_map` gives every `design doc → code globs` relationship. The `satisfied` / `violations` / `unowned` lists tell you which code actually changed in range and which doc owns it.
   - Prioritize: pairs where code changed are the highest-yield. Also spot-check docs whose owned code changed even if the doc *was* touched (Tier 3 only proves the doc was edited, not that the edit fixed the drift).

3. **Read each pair for semantic drift.** For each owning design doc whose code changed, read the relevant doc sections and the changed code, and look specifically for:
   - **Mechanism drift** — doc describes an approach/algorithm/data flow the code no longer uses.
   - **Field/signature drift** — doc names a field, parameter, return type, or default that no longer exists or changed value.
   - **Invariant drift** — doc asserts a guarantee the code no longer upholds.
   - **Constant drift** — doc cites a numeric default/threshold/version the code contradicts.
   - **Vestigial prose** — doc still documents a removed feature, or a "Future:" item that has since shipped.

4. **Cross-check the aggregation layers** the mechanical tiers only partially cover:
   - Does `docs/in_process/priority.md`'s narrative match the actual `## Track` records in the docs it cites? (A row can claim "remaining: X" after X already landed.)
   - Do `Superseded by [link]` annotations still point at the live owner?
   - Do `**Version:**` headers match the newest changelog entry's *substance*, not just its number?

5. **(Only if an L3 human-intuition layer exists.)** For each L3 page whose frontmatter pins a design doc that changed in range, read the page against the doc and flag prose drift the version pin cannot see: a stale default/number, a renamed or removed mechanism, an explanation that no longer matches the design. The pin proves the page was *re-aligned*, not that its prose is *correct* — that judgement is yours. The design doc is authoritative; report, don't rewrite the page.

6. **Write findings to `docs/audit/<YYYY-MM-DD>_doc_sync.md`.** One entry per drift, each with:
   - **Location** — `doc path §section` ↔ `code path:line`.
   - **Drift** — one sentence: what the doc claims vs. what the code does.
   - **Evidence** — the doc quote and the contradicting code, briefly.
   - **Suggested reconciliation** — which side is authoritative and the edit (or an in_process item if it's a real design question, not just stale prose).

## Hard rules

- **Report, do not silently rewrite.** Authoritative design docs stay under the user's control. Produce the audit file; let the user approve edits. You may *propose* exact diffs in the audit, but do not apply them to `design_*.md` unless the user asks.
- **Distinguish drift from intent.** A doc describing a *deliberately unbuilt* future ("Non-Goals", "Future: v3") is not drift. Only flag prose that claims the *current* system works a way it does not.
- **Cite evidence for every finding.** No finding without a doc quote and a code reference. An unsupported "this looks outdated" is noise.
- **Respect the sync boundary.** Only `design_*.md` docs (and the aggregation docs above) are sync targets. High-level vision/blueprint docs are deliberately broader than the code — do not flag breadth gaps there as drift.

## Output summary

End by telling the user: the range audited, how many pairs reviewed, how many drifts found (by severity), and the path to the written audit file. If zero drift, say so plainly — a clean audit is a real result.
