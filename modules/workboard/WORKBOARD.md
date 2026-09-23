# Global Workboard

Repository-wide runtime index for coordinated work. Enrollment is **explicit and optional** — ordinary single-agent work stays on the normal workflow, including ordinary cross-session continuation. Use L1 only when the human asks for registration; activate L2/L3 for parallel or campaign work with dependencies, shared files, or shared resources.

The protocol, activation levels, Integrator role, and every authority rule live in [`../skill/parallel_workboard.md`](../skill/parallel_workboard.md). This file holds runtime state only and restates no rule.

**Four rules govern entry, and they are the skill's, not this board's:**

- **Worker entry** — the human sending a registered Task ID to a specific worker is that worker's execution authorization. It resolves the ID here, opens the linked card, verifies `PREPARED`, records the authorization, claims only that card, and follows its base/reservation/receipt contract.
- **L1 self-registration** — "register the current task in Workboard L1 and begin" is sufficient on its own; the worker generates its own descriptive ID and starts.
- **Dispatch** — assigning an Integrator, freezing a base, preparing a card, satisfying dependencies, or setting `PREPARED` never authorizes execution.
- **Git** — neither worker completion nor round integration authorizes `git add`, `commit`, or `push`. Each requires the human's explicit current instruction, and commit and push are separate permissions.

---

## Global control

| Field | Current value |
|---|---|
| Coordination level | **L0 — idle. No campaign active, no worker active.** |
| Board owner / Integrator | none |
| Frozen base | none |
| Workspace lock | open |
| Next control event | none scheduled |

Only the current Board owner/Integrator edits this file during L2/L3 work. Workers update only their unique task card, private artifact, and receipt.

## Tracked workstreams

| Workstream | Priority authority | Execution contract | Coordination | Current runtime state | Next event |
|---|---|---|---|---|---|
| _(none)_ | — | — | — | — | — |

This table tracks execution only. A row never grants design approval, release authority, deployment permission, or permission to expand a task's scope.

## Active tasks

_(none)_

## Prepared tasks

_(none)_

## Integration queue

_(none)_

## Coordination log

_(none)_
