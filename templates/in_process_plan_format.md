# In-Process Plan File Format

Every plan, problem, or change document under `docs/in_process/` follows the head format below. The frontmatter lets readers triage a doc in seconds; the `Track` section keeps a running history so decisions never get lost when the doc moves to `docs/changelog/`.

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
## Description

Short description of the problem, goal, or context.
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

- One file per discrete concern. If a doc grows two unrelated discussion threads, split it.
- The `Track` section is append-only. Don't rewrite past entries; add a new one with a `**Change:**` that explains the revision.
- When a section of one in-process doc is superseded by another, annotate the superseded section's head in-place with `> Superseded by [link]` and add a row to `priority.md` → **Superseded sections still living in active docs**.
