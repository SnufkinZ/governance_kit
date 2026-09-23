# In-Process Plan File Format

Every plan, problem, or change document under `docs/in_process/` follows the head format below. The frontmatter lets readers triage a doc in seconds; Part I preserves what the requester actually meant as one independently readable account; Part II contains the author's analysis and proposal; the `Track` section keeps a running history so decisions never get lost when the doc moves to `docs/changelog/`.

`**Priority:**` in the frontmatter is informational only. The single source of truth for active prioritization is [`docs/in_process/priority.md`](../in_process/priority.md); per-doc frontmatter gets updated lazily next time the doc is touched.

---

## File head template

```
# Doc Name

**Type:** New Feat / Bug / Change /
**Status:** Discussion note / To be completed / In progress / Completed
**Priority:** Emergency / High / Medium / Low
**Date:** xxxx-xx-xx
**Owner:** backend / frontend / fullstack / docs
**Related work:** `docs/xxx`, `docs/xxx`
---
## Part I — Requester Intent and Use Cases

Faithfully paraphrase the requester's problem, desired outcome, reasons,
constraints, examples, concrete use cases, acceptance signals, and open
questions. Identify the source and date when useful. Keep this as one coherent,
independently readable account. Do not insert author recommendations here.
---
## Part II — Plan Author Analysis and Proposed Design

State explicitly that this part is the author's analysis and has not been
specified or approved by the requester unless a passage cites Part I. Describe
the problem in system context and develop the proposed solution here.
---
... (add as needed)
---
## Track

### (Describe what do you do)
**Date:** xxxx-xx-xx
**Author:** xxx
**Change:** What changed / what was found
**Result:** Outcome or decision
**Next:** Follow-up if any
---
### (Describe what do you do)
**Date:** xxxx-xx-xx
**Author:** xxx
**Change:** What changed / what was found
**Result:** Outcome or decision
```

---

## Conventions

- **Preserve intent before designing.** A new plan must capture the requester's
  material intent as a faithful paraphrase before expanding it into a design.
  Preserve rationale, constraints, examples, and acceptance signals; do not
  silently narrow, broaden, conventionalize, or rewrite the request to fit the
  current system.
- **Keep provenance readable.** Keep requester intent and use cases together in
  Part I rather than distributing fragments among architecture sections. A
  reader must be able to understand what the requester asked for without
  reading the author's proposed solution.
- **Separate authority.** Clearly distinguish requester-decided requirements,
  author recommendations, inferred consequences, current-system facts, and
  unresolved decisions. Questions the requester raised remain open in Part I;
  an answer proposed in Part II must not be rewritten as though the requester
  chose it. If the request conflicts with architecture or existing authority,
  state the conflict rather than editing away the intent.
- **Label the design boundary.** Part II must begin with an explicit authorship
  boundary. Do not rely on tone or section names such as "Overview" to imply
  which statements are analysis. Later sections may reference Part I, but must
  not become a second, altered copy of the request.
- **Check coverage.** Before handoff, trace every material part of the request to
  a plan section or mark it explicitly out of scope. Later revisions must not
  erase original intent: record changed intent and its authority in `Track`, and
  mark superseded material in place.
- One file per discrete concern. If a doc grows two unrelated discussion threads, split it.
- The `Track` section is append-only. Don't rewrite past entries; add a new one with a `**Change:**` that explains the revision.
- When a section of one in-process doc is superseded by another, annotate the superseded section's head in-place with `> Superseded by [link]` and add a row to `priority.md` → **Superseded sections still living in active docs**.
