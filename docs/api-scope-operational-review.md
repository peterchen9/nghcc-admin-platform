# API Scope Operational Review Package

Created: 2026-05-31

## Purpose

This package summarizes the API scope design, role group design, rollback flow, audit flow, and pending user assignments for operational permission manager review.

This phase is review-only. It does not deploy to `.240`, connect to `.240`, modify `.240`, run `--apply`, enable `API_PERMISSION_MODE=enforce`, or modify any grants, groups, or users.

## Source Artifacts

| Artifact | Purpose |
| --- | --- |
| `docs/api-scope-reviewed-backfill-plan.md` | Reviewed backfill proposal, suggested role groups, group grants, and pending user assignments. |
| `docs/api-scope-final-apply-dry-run-review.md` | Final checksum-pinned apply and rollback CSV dry-run review results. |
| `docs/api-scope-reviewed-apply-plan.md` | Reviewed apply CSV contract, dry-run behavior, apply safety gates, and audit requirements. |
| `docs/api-scope-reviewed-rollback-plan.md` | Reviewed rollback CSV contract, rollback actions, confirmation gates, and transaction rules. |
| `docs/reviewed/api-scope-final-reviewed-apply.csv` | Final reviewed apply artifact for dry-run review only. |
| `docs/reviewed/api-scope-final-reviewed-rollback.csv` | Final reviewed rollback artifact for dry-run review only. |

## Scope Design

Canonical API scopes remain endpoint and method authorization scopes. They are separate from Django model permissions and menu/page visibility permissions.

| Scope | Intended coverage |
| --- | --- |
| `api:hymns:read` | Read-only access for hymn API endpoints. |
| `api:hymns:write` | Hymn metadata create/update/delete access. |
| `api:hymns:upload` | Hymn file upload access without broad metadata write by default. |
| `api:humnos:read` | Humnos metadata lookup/read access. |
| `api:humnos:write` | Humnos workflow/download operation access where requests have side effects or operational cost. |

Effective scope rules:

1. Superusers remain an audited bypass with `reason=superuser`; they should not receive backfilled grants to explain bypass behavior.
2. Non-superuser effective scopes are the union of enabled group grants and enabled direct user grants.
3. Staff status grants no API scopes by default.
4. Direct user grants are exception-only and require separate documented review.
5. Menu visibility, page access, and Django model permissions do not imply API scopes.
6. `API_PERMISSION_MODE=off` remains the default rollback lever and default behavior.

## Group Design

The reviewed design prefers role groups over direct user grants.

| Group | Grants | Purpose |
| --- | --- | --- |
| `api_hymns_readers` | `api:hymns:read` | Hymn API read-only role. |
| `api_hymns_editors` | `api:hymns:read`, `api:hymns:write` | Hymn metadata read/write role. |
| `api_hymns_uploaders` | `api:hymns:read`, `api:hymns:upload` | Hymn read/upload role without broad metadata write. |
| `api_humnos_readers` | `api:humnos:read` | Humnos metadata lookup role. |
| `api_humnos_operators` | `api:humnos:read`, `api:humnos:write` | Humnos lookup plus operational workflow role. |

The final reviewed apply CSV contains five `create_group` rows and eight `create_group_grant` rows. It intentionally contains no `assign_user_to_group` rows and no `create_user_grant` rows.

Final reviewed apply artifact:

- File: `docs/reviewed/api-scope-final-reviewed-apply.csv`
- Rows: `13`
- SHA-256: `aabbeda8c4382330281cfd897eb6562813db6beb50bc5fbcf53d093a4c473f12`
- Ticket: `SEC-API-FINAL-CSV-DRYRUN-001`
- Reviewed by: `peterchen9`
- Plan version: `2`
- Status: dry-run reviewed only; not applied

## Rollback Flow

Rollback must be explicit, reviewed, checksum-pinned, and run through `rollback_api_scope_reviewed_plan`.

Rollback mapping:

| Apply action | Rollback action |
| --- | --- |
| `create_group_grant` | `disable_group_grant` |
| `assign_user_to_group` | `remove_user_from_group` |
| `create_user_grant` | `disable_user_grant` |
| `create_group` | Keep group by default; optional cleanup only through reviewed `delete_empty_group` with `--delete-empty-groups`. |

Operational rollback rules:

1. Dry-run is the default and writes nothing.
2. Mutating rollback requires both `--apply` and `--confirm-rollback`.
3. Grant rollback disables grant records instead of deleting them.
4. Groups are kept by default to preserve audit continuity.
5. Every rollback row must include `rollback_of`, `reason`, `reviewed_by`, `reviewed_at`, and `ticket`.
6. Confirmed rollback must run in one transaction; any failed row rolls back all prior rollback rows and audit rows.
7. Incident rollback can still set `API_PERMISSION_MODE=off` without deleting grants or groups.

Final reviewed rollback artifact:

- File: `docs/reviewed/api-scope-final-reviewed-rollback.csv`
- Rows: `8`
- SHA-256: `45c59e89d01a9f8fdc3b04f4749a5686ac81a5918f5eefd348131c85144ad4fb`
- Ticket: `SEC-API-FINAL-CSV-DRYRUN-001`
- Reviewed by: `peterchen9`
- Status: dry-run reviewed only; not applied

## Audit Flow

Audit expectations for reviewed apply and rollback:

1. Every reviewed CSV row carries reviewer metadata: `reviewed_by`, `reviewed_at`, `ticket`, `reason`, and checksum.
2. Apply and rollback commands compute SHA-256 checksums for exact plan files.
3. Operational runs should pin expected checksum, reviewer, ticket, and plan version where applicable.
4. Dry-run output is the audit preview and writes no audit rows.
5. Confirmed mutating apply or rollback writes `ApiScopeGrantAudit` rows inside the same transaction as the mutation.
6. Audit rows include action, principal, scope, previous state, planned/new state, result, row number, checksum, reviewer, ticket, and rollback reference where applicable.
7. Report-only CSVs expose only safe fields: `time`, `user_id`, `endpoint`, `method`, `scope`, `decision`, and `reason`.

## Pending Assignments

The following assignments remain pending. They were intentionally excluded from the final reviewed apply CSV and cannot be applied by that artifact.

| Username | Candidate group | Covered scopes | Current status | Required decision |
| --- | --- | --- | --- | --- |
| `peterchen` | `api_hymns_editors` | `api:hymns:read`, `api:hymns:write` | Pending | Approve or reject hymn metadata write access. |
| `peterchen` | `api_hymns_uploaders` | `api:hymns:read`, `api:hymns:upload` | Pending | Approve or reject hymn upload access. |
| `peterchen` | `api_humnos_operators` | `api:humnos:read`, `api:humnos:write` | Pending | Approve or reject humnos operator access. |

If any pending assignment is approved, it must be handled in a separate reviewed assignment CSV with a new ticket, new checksum, matching rollback CSV, and another dry-run review. Do not edit the existing final apply CSV to add assignments.

## Approval Checklist

Permission manager approval should confirm all applicable items before any later local apply phase is considered:

- [ ] Confirm the five role groups are appropriate operational roles.
- [ ] Confirm each of the eight group-to-scope grants matches the intended role boundary.
- [ ] Confirm no direct user grants are needed for this phase.
- [ ] Confirm staff users should continue receiving no API scopes by default.
- [ ] Confirm superusers should remain audited bypass users, not grant-backfilled users.
- [ ] Confirm menu/page visibility must not imply API scope access.
- [ ] Confirm pending `peterchen` assignments are either approved in a separate assignment package or remain excluded.
- [ ] Confirm the rollback CSV disables grants and keeps groups by default.
- [ ] Confirm `API_PERMISSION_MODE=off` remains the default and operational rollback lever.
- [ ] Confirm no `.240` deployment, connection, modification, or permission mutation is approved by this package.

Approval result should record:

- Reviewer:
- Review date:
- Ticket/change reference:
- Approved group rows:
- Approved group grant rows:
- Approved assignment rows, if any, in a separate package:
- Explicit exclusions:

## Reject Checklist

Reject this package or block apply planning if any item is true:

- [ ] A role group is too broad or named ambiguously.
- [ ] A group grant gives write/upload/operator access beyond the role owner's intent.
- [ ] A pending assignment lacks an explicit business owner approval.
- [ ] A direct user grant is being requested without documented exception review.
- [ ] The reviewed apply CSV checksum does not match `aabbeda8c4382330281cfd897eb6562813db6beb50bc5fbcf53d093a4c473f12`.
- [ ] The reviewed rollback CSV checksum does not match `45c59e89d01a9f8fdc3b04f4749a5686ac81a5918f5eefd348131c85144ad4fb`.
- [ ] The rollback plan does not cover every approved mutating grant or assignment row.
- [ ] Someone proposes enabling `API_PERMISSION_MODE=enforce` as part of this package.
- [ ] Someone proposes connecting to, deploying to, or modifying `.240` as part of this package.
- [ ] Local dry-run, smoke, CSRF, or permission tests fail before a later apply phase.

Rejection result should record:

- Reviewer:
- Review date:
- Rejected row or design item:
- Reason:
- Required correction:
- Whether a new checksum-pinned artifact is required:

## Apply Prerequisites

This package does not authorize apply. A later apply phase must meet all prerequisites below before any local apply is considered:

1. Obtain explicit permission manager approval for the role groups and group grants.
2. Resolve every pending assignment as approved or rejected.
3. For approved assignments, create a separate reviewed assignment apply CSV and matching rollback CSV with a new ticket and checksum.
4. Recompute and record SHA-256 checksums for every final apply and rollback CSV.
5. Run apply dry-run with `--expected-plan-version`, `--expected-checksum`, `--reviewed-by`, and `--ticket`.
6. Run rollback dry-run with `--expected-checksum`, `--reviewed-by`, and `--ticket`.
7. Confirm dry-run previews show only intended rows and `dry_run=true`.
8. Run local verification scripts and tests after dry-run review.
9. Confirm `.env` and defaults still keep `API_PERMISSION_MODE=off`.
10. Confirm no `.240` deployment, connection, modification, or permission mutation is included.
11. Prepare an operational rollback window and owner contact before any later apply.
12. Use mutating commands only in a separately approved phase with `--apply --confirm-apply` or `--apply --confirm-rollback` as appropriate.

## Current Review Status

- Role groups: proposed and dry-run validated.
- Group grants: proposed and dry-run validated.
- User assignments: pending and excluded from final reviewed apply CSV.
- Direct user grants: none proposed.
- Rollback plan: dry-run validated for the eight group grant rows.
- Enforcement: not enabled.
- Apply status: not executed.
- `.240` status: not deployed, not connected, not modified.

## Next Step

The permission manager should approve or reject the group design and resolve the pending `peterchen` assignments. Any approved assignment requires a separate reviewed assignment package before any local apply is considered. Enforcement remains out of scope.
