# Workboard Runtime Directory

This directory holds the **runtime state** of the global [`../WORKBOARD.md`](../WORKBOARD.md): task cards, receipts, notices, and the templates they are created from.

The **protocol** — activation levels L0–L3, L1 self-registration, the Integrator role, cross-window dispatch, commit granularity, parallel eligibility, round/subround decomposition, integration economy, scope levels, isolation policy, and the status model — lives in [`../../skill/parallel_workboard.md`](../../skill/parallel_workboard.md). It is not restated here.

```
workboard/
|-- CLAUDE.md      # This file
|-- tasks/         # One card per coordinated task, from templates/task_card.md
|-- receipts/      # One receipt per completed task, from templates/task_receipt.md
|-- notices/       # Append-only coordination events, from templates/coordination_notice.md
`-- templates/     # The three generic forms
```

A completed campaign's cards, receipts, and notices are archived together with its reports rather than left here.
