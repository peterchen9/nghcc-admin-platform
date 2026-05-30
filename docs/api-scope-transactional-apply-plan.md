# API Scope Transactional Apply / Audit Plan

Created: 2026-05-30

## Goal

Design the next transactional apply layer for reviewed API scope plans while keeping this phase non-mutating for grants. The implementation added in this phase may validate reviewed plans, compute checksums, expose audit-preview output, and create durable audit storage, but it must not create groups, create grants, assign users, remove grants, or enable enforcement.

## Constraints

- Do not deploy to `.240`.
- Do not connect to `.240`.
- Do not modify `.240`.
- Do not enable `API_PERMISSION_MODE=enforce`.
- Do not change default API behavior; default remains `off`.
- Do not open `--apply` for actual writes.
- Do not write grants in this phase.
- Do not automatically backfill users, groups, or grants.
- Do not add business features.

## Durable Audit Model

Added design/storage candidate: `ApiScopeGrantAudit`.

The model is intended to record one audit event per reviewed plan row when a future transactional apply mode is enabled. In this phase, the model and migration exist only as durable storage preparation; `apply_api_scope_reviewed_plan` still emits preview rows and does not insert audit rows.

Primary fields:

| Field | Purpose |
| --- | --- |
| `event_id` | Stable id derived from plan checksum, row number, and action target. |
| `plan_version` | Positive reviewed plan version declared by each plan row. |
| `plan_checksum` | SHA-256 checksum of the exact reviewed plan file bytes. |
| `row_number` | CSV line number for traceability back to the reviewed file. |
| `action` | Reviewed operation, such as `create_group_grant` or `rollback_user_grant`. |
| `dry_run` | Whether the event was preview-only. Future apply rows should be `False`. |
| `status` | Preview/apply result, for example `ok`, `applied`, `rolled_back`, or `failed`. |
| `principal_type` / `principal_name` | Human-readable target for review reports. |
| `group` / `user` / `scope` | Nullable links to current durable objects where they exist. |
| `reviewed_by` / `reviewed_at` / `ticket` | Required review metadata copied from the plan. |
| `reason` / `rollback_of` | Reviewer justification and rollback reference. |
| `previous_state` | JSON snapshot before mutation. |
| `planned_state` | JSON snapshot of intended state. |
| `result` | JSON result details, error messages, or created/updated object ids. |

Indexing focuses on plan traceability and operations review:

- `(plan_checksum, row_number)`
- `ticket`
- `(action, status)`

## Reviewed Plan Versioning

CSV plans now require `plan_version`.

Validation rules:

1. `plan_version` must be a positive integer.
2. Every row must include `reason`, `reviewed_by`, `reviewed_at`, and `ticket`.
3. `ticket` identifies the reviewed change request.
4. Optional command arguments may pin the expected metadata:
   - `--expected-plan-version`
   - `--expected-checksum`
   - `--reviewed-by`
   - `--ticket`
5. If any row fails validation, the command raises `CommandError` before emitting a usable plan preview.

Checksum flow:

1. Reviewer produces the exact CSV plan.
2. Operator records the SHA-256 checksum in the ticket/change request.
3. Dry-run is executed with `--expected-checksum <sha256>` when available.
4. Audit preview echoes `plan_checksum` and per-row `audit_event`.
5. Future apply mode must reject checksum mismatches before opening a transaction.

## Transactional Apply Design

Future apply mode should run all mutating work inside a single `transaction.atomic()` block:

1. Parse the reviewed plan and compute checksum.
2. Validate all rows and metadata before starting writes.
3. Lock or re-read target users, groups, scopes, memberships, and grants.
4. Write a pending `ApiScopeGrantAudit` event for each row with `previous_state`.
5. Apply rows in deterministic file order.
6. Update each audit event with `planned_state`, `status`, and `result`.
7. Commit only if every required row succeeds.
8. Roll back the database transaction if any row fails.

This phase intentionally stops before step 4. The command remains dry-run and preview-only.

## Rollback Execution Design

Rollback must be explicit and reviewed. It is not inferred from logs or previous plans.

Supported rollback action names remain:

- `rollback_group_grant`
- `rollback_user_grant`
- `rollback_user_group_assignment`

Rollback execution rules for a future mutating phase:

1. Each rollback row must include `rollback_of`.
2. `rollback_of` should reference the original `event_id`, original reviewed row id, or ticket action id.
3. The command should look up the original audit event and verify target consistency.
4. Grant rollback should prefer disabling a grant over deleting it when audit continuity matters.
5. User/group assignment rollback may remove the specific reviewed membership only when it was introduced by a reviewed apply row.
6. Rollback events must create their own `ApiScopeGrantAudit` rows linked by `rollback_of`.
7. Incident rollback can still use `API_PERMISSION_MODE=off` without deleting permission data.

## Current Command Behavior

`apply_api_scope_reviewed_plan` remains dry-run only.

Current capabilities:

- Validates required columns and per-action required identifiers.
- Requires positive `plan_version`.
- Requires `ticket`.
- Requires `rollback_of` for rollback rows.
- Computes SHA-256 `plan_checksum`.
- Supports optional expected checksum/version/reviewer/ticket validation.
- Emits audit-preview CSV with `audit_event`, `plan_version`, `plan_checksum`, and row metadata.
- Reads existing users, groups, scopes, and grants only to describe future behavior.

Current non-capabilities:

- Does not create `Group` rows.
- Does not create, update, disable, or delete grants.
- Does not assign users to groups.
- Does not write `ApiScopeGrantAudit` rows.
- Does not run rollback mutations.
- `--apply` remains disabled and raises an error.

## Tests

Added/updated tests in `tests/security/test_api_scope_storage.py` to confirm:

- Dry-run emits audit-preview rows with version, checksum, and stable event ids.
- Dry-run writes no groups, grants, group memberships, or audit rows.
- `--apply` is still disabled and writes nothing.
- Plan validation blocks malformed reviewed plans before preview.

## Next Step

After this design is reviewed, the next implementation phase can add an explicitly approved transactional apply mode. That phase should write durable audit events inside a database transaction and include rollback execution tests before any use outside local review.

## Transactional Apply Implementation Status

Updated: 2026-05-30

The explicitly approved transactional apply phase has been implemented locally.

Preserved constraints:

- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce` enablement.
- Default command behavior remains dry-run.
- No default API behavior changed.
- No automatic grant backfill.
- Writes happen only when both `--apply` and `--confirm-apply` are present.

Implemented mutating actions:

- `create_group`
- `create_group_grant`
- `create_user_grant`
- `assign_user_to_group`

Apply behavior:

1. The command reads and validates the full reviewed CSV plan before writes.
2. `--apply` without `--confirm-apply` raises `CommandError` and writes nothing.
3. `--apply --confirm-apply` runs all write work inside one `transaction.atomic()` block.
4. Each applied row writes an `ApiScopeGrantAudit` row with `dry_run=False`, `previous_state`, `planned_state`, `result`, checksum, row number, reviewer, and ticket metadata.
5. If any row fails during apply, the whole transaction rolls back, including groups, grants, memberships, and audit rows.

Rollback status:

- Rollback rows remain supported for dry-run validation and preview.
- Rollback rows are rejected in mutating apply mode for this phase.
- Rollback execution must remain an explicit future command path or separately reviewed apply path; it is not inferred or automatically executed.

Tests now cover:

- Dry-run writes nothing.
- `--apply` without `--confirm-apply` writes nothing.
- `--apply --confirm-apply` writes reviewed test groups, grants, memberships, and audit rows.
- Audit rows are written for applied actions.
- Injected transaction failure rolls back prior writes and audit rows.
