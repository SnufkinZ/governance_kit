# Task Receipt Mailbox

This directory is the provider-neutral completion channel for the global
Workboard. The protocol is [`../../../skill/parallel_workboard.md`](../../../skill/parallel_workboard.md).

Each coordinated task writes exactly one uniquely owned receipt:

```text
receipts/<TASK-ID>.md
```

Create it from [`../templates/task_receipt.md`](../templates/task_receipt.md).
The worker may create or update only its own receipt. A receipt reports work; it
does not mark the global task `DONE`, alter another task, grant approval, or
authorize integration.

After writing the receipt, the worker changes its unique task card to
`REVIEW_READY`. The user may then invoke the temporary Integrator in any
provider/window; the Integrator scans receipts and updates
[`../../WORKBOARD.md`](../../WORKBOARD.md) serially.
