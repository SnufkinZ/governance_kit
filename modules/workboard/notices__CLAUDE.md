# Coordination Notice Mailbox

This directory is the provider-neutral event channel for the global Workboard.
The protocol is [`../../../skill/parallel_workboard.md`](../../../skill/parallel_workboard.md).

Use a unique append-only filename:

```text
notices/<FROM-TASK-ID>--<sequence>--<type>.md
```

Create it from
[`../templates/coordination_notice.md`](../templates/coordination_notice.md).
Notices report dependency, invalidation, overlap, scope-expansion, or lock
events. They do not change authority or reservations by themselves.

A worker may continue unaffected scope after writing a notice. If the finding
blocks correctness, it sets its own card to `BLOCKED` or `RETURNED`. The user
invokes the temporary Integrator to decide and record the result; workers from
different vendors do not need a direct communication channel.
