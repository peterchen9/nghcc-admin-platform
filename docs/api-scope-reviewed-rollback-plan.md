# API Scope Reviewed Rollback Plan

Created: 2026-05-30

## Goal

Add an independent reviewed rollback command path for API scope grants and group assignments. Rollback is explicit, human-reviewed, audited, and transactional. It is not inferred from report-only logs, audit rows, or previous apply plans.

## Constraints

- Do not deploy to `.240`.
- Do not connect to `.240`.
- Do not modify `.240`.
- Do not enable `API_PERMISSION_MODE=enforce`.
- Do not change default API behavior; default remains `off`.
- Do not infer rollback from audit output.
- Rollback must come from a human-reviewed rollback plan.
- Dry-run is the default.
- Mutating rollback requires both `--apply` and `--confirm-rollback`.

## Reviewed Rollback CSV

Required columns:

| Column | Purpose |
| --- | --- |
| `action` | Reviewed rollback operation. |
| `group` | Django group name for group rollback actions. |
| `username` | Username for user grant or group membership rollback. |
| `scope` | Canonical API scope for grant rollback actions. |
| `rollback_of` | Required reference to the reviewed apply row, audit event, or ticket action being rolled back. |
| `reason` | Human review reason for the rollback. |
| `reviewed_by` | Reviewer identifier. |
| `reviewed_at` | Review timestamp/date, preferably ISO 8601. |
| `ticket` | Issue/change ticket or incident reference. |
| `notes` | Free-form operational notes. |

Example:

```csv
action,group,username,scope,rollback_of,reason,reviewed_by,reviewed_at,ticket,notes
remove_user_from_group,api_humnos_readers,local-reader,,apply-row-3,"Rollback reviewed membership",peter,2026-05-30,SEC-API-RB-001,"Membership no longer approved"
disable_group_grant,api_humnos_readers,,api:humnos:read,apply-row-2,"Rollback reviewed group grant",peter,2026-05-30,SEC-API-RB-001,"Disable instead of delete"
disable_user_grant,,service-account,api:humnos:read,apply-row-4,"Rollback direct exception",peter,2026-05-30,SEC-API-RB-002,"Disable exception grant"
```

## Command

Dry-run preview:

```powershell
python backend/manage.py rollback_api_scope_reviewed_plan `
  --plan-file reviewed-api-scope-rollback-plan.csv
```

Mutating rollback:

```powershell
python backend/manage.py rollback_api_scope_reviewed_plan `
  --plan-file reviewed-api-scope-rollback-plan.csv `
  --apply `
  --confirm-rollback
```

Optional validation:

```powershell
python backend/manage.py rollback_api_scope_reviewed_plan `
  --plan-file reviewed-api-scope-rollback-plan.csv `
  --expected-checksum <sha256> `
  --reviewed-by peter `
  --ticket SEC-API-RB-001
```

## Supported Actions

- `remove_user_from_group`: removes the reviewed user/group membership when present.
- `disable_user_grant`: sets the direct user grant to `enabled=False`.
- `disable_group_grant`: sets the group grant to `enabled=False`.
- `delete_empty_group`: optional cleanup action. It only deletes an empty group when `--delete-empty-groups` is explicitly provided. By default, groups are not deleted.

Grant rollback disables records instead of deleting them so audit continuity remains visible.

## Audit And Transaction Rules

- Dry-run writes no groups, grants, memberships, or audit rows.
- `--apply` without `--confirm-rollback` raises an error and writes nothing.
- `--apply --confirm-rollback` runs all rows inside one `transaction.atomic()` block.
- Every mutating rollback row writes one `ApiScopeGrantAudit` event with `dry_run=False`, `rollback_of`, previous state, planned state, result, checksum, row number, reviewer, and ticket metadata.
- If any row fails, the whole transaction rolls back, including earlier rollback changes and audit rows.

## Current Status

Implemented locally:

- `rollback_api_scope_reviewed_plan`
- Default dry-run preview
- Confirm-gated mutating rollback
- Transactional audit writes
- Tests for dry-run, missing confirm, confirmed rollback, audit rows, and transaction rollback

This phase remains local only. Do not enable enforcement until reviewed apply, reviewed rollback, audit review, and local smoke/security tests are accepted.
