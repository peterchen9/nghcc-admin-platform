# API Scope Reviewed Apply / Backfill Plan

Created: 2026-05-30

## Goal

Design a reviewed apply/backfill workflow for API scope groups, grants, and user assignments. This phase is intentionally dry-run only: it documents the apply contract and adds a skeleton command that validates reviewed plans without writing database state.

## Constraints

- Do not deploy to `.240`.
- Do not connect to `.240`.
- Do not modify `.240`.
- Do not enable `API_PERMISSION_MODE=enforce`.
- Do not change default API behavior; default remains `off`.
- Do not directly write grants in this phase.
- Do not automatically backfill grants.
- Do not add business features.

## Reviewed Plan Format

The executable skeleton supports CSV. YAML is documented as the future human-friendly equivalent, but it is not accepted by the command yet because this phase avoids adding parser dependencies.

Required CSV columns:

| Column | Required | Purpose |
| --- | --- | --- |
| `action` | Yes | One reviewed operation, such as `create_group` or `create_group_grant`. |
| `group` | Conditional | Django group name for group creation, group grants, and user assignment. |
| `username` | Conditional | User username for user grants and user-to-group assignment. |
| `scope` | Conditional | Canonical API scope string for grant operations. |
| `plan_version` | Yes | Positive reviewed plan version used for checksum/audit traceability. |
| `reason` | Yes | Human review reason; copied into future audit/grant reason fields. |
| `reviewed_by` | Yes | Reviewer identifier. |
| `reviewed_at` | Yes | Review timestamp/date, preferably ISO 8601. |
| `ticket` | Yes | Issue/change ticket or review reference. |
| `rollback_of` | No | Optional id/reference to the action being rolled back. |
| `notes` | No | Free-form operational notes. |

Example CSV:

```csv
action,group,username,scope,plan_version,reason,reviewed_by,reviewed_at,ticket,rollback_of,notes
create_group,api_hymns_readers,,,1,"Approved reader role",peter,2026-05-30,SEC-API-001,,"Create role shell first"
create_group_grant,api_hymns_readers,,api:hymns:read,1,"Approved reader scope",peter,2026-05-30,SEC-API-001,,"Grant after group exists"
assign_user_to_group,api_hymns_readers,local-reader,,1,"Observed read need in report-only logs",peter,2026-05-30,SEC-API-001,,"No direct grant"
create_user_grant,,service-account,api:humnos:read,1,"Temporary documented exception",peter,2026-05-30,SEC-API-002,,"Review expiry separately"
```

Future YAML equivalent:

```yaml
reviewed_plan_version: 1
reviewed_by: peter
reviewed_at: 2026-05-30
ticket: SEC-API-001
actions:
  - action: create_group
    group: api_hymns_readers
    reason: Approved reader role
  - action: create_group_grant
    group: api_hymns_readers
    scope: api:hymns:read
    reason: Approved reader scope
  - action: assign_user_to_group
    group: api_hymns_readers
    username: local-reader
    reason: Observed read need in report-only logs
```

## Apply Command Skeleton

Added dry-run skeleton:

```powershell
python backend/manage.py apply_api_scope_reviewed_plan --plan-file reviewed-api-scope-plan.csv
```

Current behavior:

- Parses and validates reviewed CSV rows.
- Computes a SHA-256 checksum for the exact reviewed plan file.
- Emits CSV dry-run audit-preview rows with event id, plan version, checksum, action, status, principal, scope, review metadata, and notes.
- Reads current groups, users, scopes, and existing grants only to report whether an action would create, reuse, or fail later.
- Never creates groups.
- Never creates grants.
- Never assigns users.
- Never deletes or disables anything.
- `--apply` is reserved and deliberately raises an error in this phase.

Optional validation arguments:

```powershell
python backend/manage.py apply_api_scope_reviewed_plan `
  --plan-file reviewed-api-scope-plan.csv `
  --expected-plan-version 1 `
  --expected-checksum <sha256> `
  --reviewed-by peter `
  --ticket SEC-API-001
```

If validation fails, the command raises an error before producing a usable preview.

## Action Semantics

### create groups

`create_group` declares a reviewed Django group that may later hold API grants. In dry-run, the command only reports whether the group already exists or would be created.

### create grants

`create_group_grant` declares a reviewed group-to-scope grant. `create_user_grant` declares a direct user exception. In dry-run, the command verifies required identifiers and reports whether the referenced group/user/scope exists.

Direct user grants remain exceptions. Group grants remain the preferred path.

### assign users

`assign_user_to_group` declares adding a reviewed user to a reviewed role group. In dry-run, the command reports whether the user and group exist and whether the membership already exists.

### rollback

Rollback actions are explicit rows, not automatic inference:

- `rollback_group_grant`
- `rollback_user_grant`
- `rollback_user_group_assignment`

Rollback should prefer disabling/removing the specific reviewed action in a later apply implementation, with `rollback_of` pointing to the original row or ticket. Incident rollback can also keep using `API_PERMISSION_MODE=off` without deleting grant data.

### audit log

Every reviewed row must include `plan_version`, `reason`, `reviewed_by`, `reviewed_at`, and `ticket`. Future apply mode should write an audit row before and after each mutation, including dry-run output, actor, target, action, previous state, new state, result, and the exact plan checksum.

### dry-run

Dry-run is the default and only supported behavior in this phase. The command output is the audit preview. Tests assert that the command does not create groups, grants, or user assignments.

## Backfill Policy

Backfill is reviewed action-by-action. There is no automatic conversion from report-only logs to grants.

Allowed reviewed backfill inputs:

1. `plan_api_scope_grants` CSV output.
2. `report_api_effective_scopes` output.
3. Report-only log review CSV.
4. Manual reviewer decision captured in the reviewed plan.

Not allowed:

- Staff-wide default grants.
- Superuser grants to explain bypass behavior.
- Page/menu visibility derived API grants.
- Automatic grants from `deny/missing_scope` rows.

## Tests

Added tests in `tests/security/test_api_scope_storage.py` to confirm:

- Reviewed dry-run accepts valid CSV plan rows and emits audit-preview output.
- Audit-preview output includes plan version, checksum, and event id.
- Dry-run does not create groups.
- Dry-run does not create `GroupApiScopeGrant` or `UserApiScopeGrant` rows.
- Dry-run does not assign users to groups.
- Dry-run does not write `ApiScopeGrantAudit` rows.
- `--apply` is disabled and writes nothing.
- Invalid reviewed plans are rejected during validation.

## Next Step

After this dry-run skeleton is reviewed, the next implementation phase can add an explicit apply mode behind a separate approval step. That phase should add transactional writes to `ApiScopeGrantAudit`, grant mutation guarded by `transaction.atomic()`, rollback execution, and another test pass before any production-like use.

## Transactional Apply Update

Updated: 2026-05-30

The reviewed apply command now has an explicitly confirmed mutating path:

```powershell
python backend/manage.py apply_api_scope_reviewed_plan `
  --plan-file reviewed-api-scope-plan.csv `
  --apply `
  --confirm-apply
```

Default behavior is still dry-run. `--apply` alone is rejected and writes nothing.

Implemented apply actions:

- `create_group`
- `create_group_grant`
- `assign_user_to_group`
- `create_user_grant`

Every mutating apply row writes `ApiScopeGrantAudit` inside the same transaction as the group/grant/membership change. Rollback action rows remain preview-only in this phase and are rejected from mutating apply until a separately reviewed rollback command path is implemented.
