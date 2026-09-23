# Task Card — `<TASK-ID>`

> Delete instructional placeholders when instantiating this template. Keep the
> card outcome-oriented; add optional fields only when coordination risk needs
> them.

**Status:** `PLANNED | PREPARED | EXECUTION_AUTHORIZED | CLAIMED | IN_PROGRESS | REVIEW_READY | ...`
**Workstream:** `<name>`
**Round / subround:** `<round label; use a hierarchical label when decomposed>`
**Type:** `review | build | fix | experiment | integration | deploy | other`
**Owner:** `<agent/thread or unassigned>`
**Integrator:** `<agent/thread or none>`
**Base:** `<commit/version or not-applicable>`
**Execution authority:** `NOT GRANTED` until the human sends this exact Task ID
to a worker or explicitly orders the Integrator to dispatch it.

## Objective

`<The outcome this task must produce.>`

## Context and authority

- `<Authoritative plan/design/request>`
- **Approval required:** `<yes/no; authority and record if applicable>`
- **Git authority:** none unless the human explicitly instructs the current task
  to stage/commit/push; completion is not authorization.
- **Domain metadata:** `<optional, non-global vocabulary>`

## Scope

**In:** `<required outcome and invariants>`

**Out:** `<explicit exclusions that prevent accidental expansion>`

The agent may inspect and reason beyond this scope. Mutation or external action
outside it follows the expansion policy below.

## Dependencies and isolation

- **Depends on:** `<task/base/decision or none>`
- **Integration barrier:** `<prior subround integration/base or none>`
- **Invalidated by:** `<task/surface or none>`
- **Isolation:** `<shared checkout / worktree / branch / external>`
- **Read-critical surfaces:** `<only when another task could invalidate them>`
- **Reserved writes/resources:** `<exact paths/resources or none>`
- **Forbidden shared surfaces:** `<only coordination-specific restrictions>`

## Work

`<What must be investigated or built; avoid prescribing implementation steps
unless an accepted design requires them.>`

## Deliverables and acceptance

- `<artifact/result>`
- `<questions that must be answered>`
- `<tests/checks and expected bar>`

## Expansion policy

- Level A local autonomy: allowed and recorded.
- Level B reservation expansion: for an unreserved file/resource required by
  the already-authorized objective, notify the Integrator; continue unaffected
  work. A missing reservation alone is not an authority stop.
- Level C authority expansion: stop affected work and request authority.

Reservations prevent write/resource conflicts; they do not define semantic or
implementation authority. The Integrator may add a conflict-free Level-B
reservation, but may not use it to expand behavior, public contracts,
production/schema/snapshot/migration authority, release boundaries, lifecycle
targets, task objectives, or another task's ownership.

## Stop conditions

- frozen base or critical read surface becomes stale;
- correctness requires Level-C expansion;
- a reservation/shared-resource conflict appears;
- accepted authorities contradict and cannot be reconciled inside the task.

## Closeout

Create `docs/in_process/workboard/receipts/<TASK-ID>.md` from the fixed
[`task_receipt.md`](../templates/task_receipt.md) shape, change only this card to
`REVIEW_READY`, and link all deliverables. In a shared checkout, do not perform
git operations; the Integrator owns serial integration.
