# Parallel Workboard Skill

How explicitly tracked work and large parallel campaigns run when agents, windows, or vendors share this repository. *Optional governance-kit module — installed with `install.py --with-workboard`; a project that never runs parallel agents does not need it.* The mechanism is deliberately generic, opt-in, and reversible. **It coordinates work; it does not define product behavior, replace plan or design authority, or grant approvals.**

Runtime state lives in [`../in_process/WORKBOARD.md`](../in_process/WORKBOARD.md) (the global board) and [`../in_process/workboard/`](../in_process/workboard/) (cards, receipts, notices, templates). This file is the protocol.

## Choose the lowest level that is safe

| Level | Use when | Required control |
|---|---|---|
| **L0 — Solo** | one short, isolated task | no board registration |
| **L1 — Explicitly tracked** | the human explicitly asks to register an important or cross-session task | one board row; the initiating task owns its updates |
| **L2 — Parallel** | multiple tasks share a checkout or dependency surface | temporary Integrator, frozen base, task cards, reservations |
| **L3 — Campaign** | multi-round or cross-workstream program with landings | dedicated temporary Integrator, locks, receipts, serial integration |

If coordination cost approaches the expected parallelism benefit, reduce parallelism or fall back to serial execution. L2/L3 does not by itself require a separate integration agent — see [Integration economy](#integration-economy).

**Most work is L0.** A single reviewer walking a gate ladder, a bug fix, a doc pass, or an ordinary cross-session continuation does not self-enrol. L1 exists only when the human explicitly requests registration; L2/L3 are the normal reason to activate the mechanism.

## L1 self-registration

The instruction "register the current task in Workboard L1 and begin" is self-contained. The agent does not ask the user to invent an ID or restate this protocol. It:

1. reads the global board and current lock;
2. derives a descriptive provider-neutral ID as `L1-<YYYYMMDD>-<short-purpose-slug>`; if that path exists, appends `-2`, `-3`, …;
3. creates `workboard/tasks/<TASK-ID>.md` from the generic card with objective, owner, base, critical reads, reserved writes/resources, and expected result;
4. if no L2/L3 Integrator owns the board and the lock permits, adds one L1 row to `Active tasks`; otherwise writes a registration notice and leaves the global board to the Integrator;
5. records that the same instruction supplied `EXECUTION_AUTHORIZED`, claims the card, sets it to `IN_PROGRESS`, and begins immediately unless a real dependency or reservation conflict is found.

The ID describes the work, not the AI vendor or an arbitrary sequence — for example `L1-20260728-auth-token-rotation`.

## Integrator

Integrator is a temporary role, not a scheduled service. The initiating task may hold it for L1/L2; a large L3 campaign may use a dedicated pinned task. It is invoked on claim, notice, receipt, and round-close events rather than polling. In cross-window or cross-vendor work no direct agent messaging is required: the shared cards, notices, and receipts are the transport.

The Integrator alone:

- edits the global board during L2/L3;
- freezes and changes the campaign base;
- checks dependencies, read invalidation, reservations, and shared resources;
- decomposes a nominal round when its tasks are not one parallel-safe set;
- grants Level-B write-reservation expansion when conflict-free;
- serially edits shared indexes/plans and performs integration;
- records external approval without inventing it;
- marks integrated tasks `DONE` and prepares dependency-safe follow-on cards.

**Assigning an Integrator, freezing a base, preparing cards, or satisfying dependencies never authorizes worker execution.** The Integrator must not spawn, create, message, assign, or start workers unless the human explicitly instructs it to dispatch those exact tasks.

Workers may continue unaffected work if the Integrator is temporarily unavailable, recording their state in their card or receipt for later reconciliation.

## Cross-window and cross-vendor operation

Coordination must not depend on provider-specific thread tools:

1. the Integrator freezes a committed base, or an explicitly accepted hash-bound overlay under the exception below, and sets dependency-safe cards to `PREPARED`, execution authority `NOT GRANTED`;
2. **The human sends an exact Task ID to a chosen worker; that message is the execution authorization**;
3. the worker records `EXECUTION_AUTHORIZED`, then claims only its card by filling `Owner`, `Base`, and `IN_PROGRESS`;
4. findings affecting another task are written as a uniquely named file under `notices/`;
5. completion creates `receipts/<TASK-ID>.md` and moves only that card to `REVIEW_READY`;
6. the user invokes the Integrator, which scans cards/notices/receipts and updates the global board serially.

Owner identity is provider-neutral, for example `claude-window-wave6` or `codex-window-ledger`.

Workers sharing one checkout must not stage, commit, rebase, reset, clean, or switch branches. Report-only workers modify only their reserved files. A task needing git or production changes receives its own worktree/branch. If providers do not share a filesystem, the equivalent transport is one branch/PR per isolated task, with its receipt in that branch.

## Commit granularity

The default commit unit is the **integrated round**, not an individual worker task. Report/review workers leave their outputs uncommitted; after all required receipts are ready, the Integrator reconciles them, applies shared updates, runs the round checks, and stops at `AWAITING_COMMIT`.

The human may explicitly exempt dependency subrounds inside one campaign from separate commits. Under that exception an accepted subround freezes a **hash-bound overlay**: one committed anchor plus the exact SHA-256 identity of its accepted integration handoff and the immutable inputs that handoff names. The next subround may use that overlay as its base without an intermediate commit. The Integrator records the exception and hashes on the board and every affected card. Acceptance still does not dispatch workers, grant domain authority, or authorize any git operation; the campaign retains one later commit boundary unless the human says otherwise.

**Completion, integration, a task card, a receipt, or an earlier instruction to run the round is not commit authorization.** No worker or Integrator may stage, commit, amend, or push coordinated work until the human gives an explicit current instruction for that git action. Commit and push are separate permissions.

An independently releasable production landing may need its own worktree, branch, and rollback commit. That is an explicit exception recorded in its card, not the default, and it still requires the human's explicit commit instruction. Intermediate branch commits may be squashed at integration when preserving them adds no release or diagnostic value.

## Parallel eligibility

Tasks may run together only when **all** hold:

1. prerequisites and authority are stable at the frozen base;
2. reserved writes do not overlap;
3. one task will not invalidate a surface another task reads;
4. shared mutable resources (schema, snapshot version, generated index, environment, deployment target) do not collide;
5. neither task needs an in-flight joint redesign.

Disjoint seed names or file writes alone do not prove independence.

## Round and subround decomposition

A named round is not evidence that its tasks may run concurrently. Before preparing a multi-task round, the Integrator builds the effective dependency graph from prerequisites, frozen-base requirements, critical reads, reserved writes, shared mutable resources, design coupling, authority gates, and release/rollback boundaries. **Only one parallel-safe layer of that graph may be active at a time.**

When the nominal round is not one parallel-safe set, prefer decomposition over a long-lived coordinating worker:

1. keep tasks in the same **subround** when they share one campaign objective, authority envelope, and exit gate, and a serial integration barrier can give the next layer a precise base;
2. promote to a separate **round** when the work introduces an authority objective the parent round does not contain, an independently releasable or rollbackable landing, a schema or snapshot-version boundary, a materially different frozen base, or a result that should be accepted or rejected independently. A planned approval gate already inside the parent objective may remain a subround boundary, but execution stops at that gate;
3. within each subround activate only a maximal parallel-safe set; after its receipts are integrated, freeze the resulting base before preparing the next;
4. if a newly discovered conflict invalidates the schedule, continue unaffected tasks, mark affected cards dependency-held or stale, and replan. **Do not disguise serialization as parallel work.**

Use hierarchical labels such as `R2C.1`, `R2C.2`; task IDs may use the filesystem-safe compact form `R2C1`. Record the dependency and integration barrier on every affected card and show subrounds separately on the board.

Subround decomposition changes scheduling, not authority. It does not dispatch a worker, authorize a continuously running Integrator, waive an approval gate, or grant git operations.

## Integration economy

An integration pass is a fixed cost; the benefit of parallelism grows with the number of inputs. Where `w` is one worker's duration, `i` one integration pass, `h` one human authorization round-trip, and `g` the number of gates: serial single-agent execution costs about `N·w + h`; parallel execution with a separate integrator costs about `w + i + g·h`. When the human is not continuously available, `h` dominates every other term, so **reduce gates first, then integration passes, then parallel width.** A round is not better because it looks parallel.

### Integration threshold

A separate integration card is justified by the number of parallel inputs it reconciles, not by the existence of a round. Prepare one only when the subround has **three or more parallel inputs**, or when one of these holds:

1. **authority gate** — the exit is a decision packet the human must accept, so the pass produces that handoff rather than merging;
2. **deliberate adversarial review** — an independent reviewer cross-checking the other outputs is the point of the round;
3. **release boundary** — the subround crosses a schema/snapshot-version, migration, or independently rollbackable release boundary.

A single-worker subround never has an integration card. When an independent second reading of a one-worker result is still wanted, prepare an **acceptance** card typed `verification`: it checks and reports, merges nothing, and owns no shared index.

### Closing-worker merge

When a subround has two parallel cards and no exception applies, do not add a third agent. Name one card the **closing worker** on both cards. The other worker finishes into its receipt and stops. The closing worker reads that receipt, performs the same mechanical base/reservation/coverage/contradiction checks an Integrator would, writes the shared indexes under a published serial manifest, and stops at the subround's normal stop state.

The closing worker gains no authority the subround did not already hold. It may not accept its own content decisions, resolve a contradiction it finds, or expand either reservation. A contradiction, novel finding, or new authority question is reported and stops the pass. If either output needs genuine reconciliation rather than mechanical merging, the two cards were not independently parallel — escalate to a real integration pass.

### Conditional authorization

The human's authorization of an integration or closing pass may carry an explicit stated condition, for example: *integrate; if the mechanical checks pass with no contradiction and no new authority question, continue to the declared next step and stop there; otherwise stop and report.* This removes a round-trip only where there was nothing left to decide.

A condition belongs to one authorization and is never standing. It may carry only mechanical continuation: verification, index/ledger reconciliation, freezing the accepted hash-bound overlay under an already-published manifest, and preparing the next dependency-safe subround. It never carries an approval gate, a production/schema/snapshot/migration change, a scope change, a worker dispatch, or any git operation. Any unmet condition, contradiction, novel finding, or unanswered authority question forces the stop, and the agent reports exactly which conditional steps it did and did not take.

## Scope and autonomy

A card defines the requested outcome, invariants, authority boundary, and reserved mutations. It does **not** limit investigation, reasoning, read-only inspection, or implementation technique.

**Reservation and authority are independent controls.** A reservation prevents concurrent write conflicts; it does not define semantic or implementation authority.

- **A — local autonomy:** required for the same objective, inside the reservation/authority boundary, changes no public contract or shared resource. Proceed and record it.
- **B — reservation expansion:** same objective and semantics, but needs an unreserved implementation file/resource. Send a scope-change notice; continue unaffected work. The Integrator may approve when no task is invalidated; **a missing reservation alone is not an authority stop.**
- **C — authority expansion:** changes behavior, public contract, plan/design, schema/snapshot, external effect, approved scope, or another task's ownership. Stop only the affected part and request that authority.

Reservation expansion must never be used to smuggle in an authority change. Rules exist to protect useful work, not to prescribe how an agent solves the problem; a blocked administrative update must not stop technically independent work.

## Isolation policy

| Work | Default isolation |
|---|---|
| read-only review or unique report | frozen shared base + unique reserved output |
| experiment or generated artifacts | isolated worktree when it can dirty shared state |
| independently releasable production change | branch/worktree; PR when independently reviewable and rollbackable |
| shared schema/snapshot/index or hot coordination docs | one serial Integrator/landing owner |

During L2/L3, workers do not edit `WORKBOARD.md`, `priority.md`, directory indexes, shared evidence indexes, changelogs, or another task's card unless their card explicitly reserves the file.

## Status model

```
PLANNED → PREPARED → EXECUTION_AUTHORIZED → CLAIMED → IN_PROGRESS →
REVIEW_READY → INTEGRATING → AWAITING_COMMIT | AWAITING_ACCEPTANCE → DONE
```

Exceptional states: `BLOCKED`, `RETURNED`, `STALE`, `PARTIAL`, `SUPERSEDED`, `CANCELLED`.

Workers may report through `REVIEW_READY`. The pass that closes a round — an Integrator, or the closing worker of a two-card subround — moves through `INTEGRATING` and stops at one of two terminals:

- `AWAITING_COMMIT` — the default. The round's durable result is a git commit, and the pass may go `DONE` only while carrying out the human's explicit commit instruction.
- `AWAITING_ACCEPTANCE` — only where the human exempted a dependency subround from its own commit. Their acceptance freezes the hash-bound overlay that becomes the next subround's base, and the card becomes `DONE / ACCEPTED`. The campaign still reaches a real `AWAITING_COMMIT` later.

The closing pass enters the applicable waiting state when its stated checks are
complete; that transition reports a fact and grants nothing. Only the human's
explicit current instruction may perform the commit, or accept a hash-bound
overlay and move the task from its waiting state to `DONE`.

A written status line is one lifecycle state plus optional qualifiers separated by `/`. Qualifiers state authority and scheduling, never progress: `NOT GRANTED`, `DEPENDENCY-HELD`, `OPTIONAL`, `ACCEPTED`, and `CONDITIONALLY REINSTATED` on a `SUPERSEDED` card that revives when its stated condition occurs. **A qualifier never grants what the lifecycle state does not.**

For the explicit L1 instruction in §L1, `EXECUTION_AUTHORIZED` and `CLAIMED` may be recorded atomically with the transition to `IN_PROGRESS`; they are not skipped semantically and no second dispatch is required.

## Communication and approval

Workers report facts; they do not privately renegotiate task authority. Use [`../in_process/workboard/templates/coordination_notice.md`](../in_process/workboard/templates/coordination_notice.md) for a dependency, invalidation, overlap, or scope expansion, saved under `workboard/notices/`. The recipient may keep working inside unaffected scope. The Integrator decides whether to acknowledge, reverify, return, reorder, or merge tasks.

Continuous two-way design negotiation means the work was not independently parallel: merge it or serialize it.

The global schema uses only generic approval fields. Domain-specific gates, review names, deployment environments, or release vocabulary belong in the card's domain metadata and referenced authority. A worker may report that a package is prepared; it may not claim an approval the recorded authority did not grant.

## Templates and cleanup

- [`task_card.md`](../in_process/workboard/templates/task_card.md) — assignment and reservation
- [`task_receipt.md`](../in_process/workboard/templates/task_receipt.md) — fixed closeout block
- [`coordination_notice.md`](../in_process/workboard/templates/coordination_notice.md) — bounded event

Keep cards concise; formal findings belong in the workstream's own report home. After integration the board retains a short result link. Choose the cleanup policy when the campaign is opened and do not mix them:

- **ordinary round:** before the integrated commit, delete temporary worker cards, receipts, and notices; keep the formal results, the board's short result link, and only an integration receipt when it adds durable value. If scaffolding already entered an earlier authorized commit, history retains it; otherwise it was intentionally ephemeral;
- **audit-retained campaign:** preserve cards, receipts, notices, and the final board snapshot, then archive them together with the reports when the campaign closes.

## Relationship to domain authority

This protocol carries no domain authority of its own. A domain gate ladder (a review or release procedure your project defines) decides *what* must be approved and by whom; this file decides only *how* several agents avoid colliding while producing it. When the two appear to conflict, the domain authority wins and the board is wrong.

To retire the mechanism entirely: delete the board and the `workboard/` directory, then remove the repository instruction pointers. Existing plans, task artifacts, branches, commits, and reports remain valid.
