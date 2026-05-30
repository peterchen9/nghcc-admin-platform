# API Scope Reviewed Grant Backfill Plan

Created: 2026-05-31

## Goal

Build a human-reviewed grant backfill proposal from the latest local report-only CSV and the `plan_api_scope_grants` dry-run output.

This phase produces recommendations only. It does not apply grants, create groups, assign users, enable enforcement, deploy to `.240`, connect to `.240`, modify `.240`, change the default `API_PERMISSION_MODE=off`, change default API behavior, or add business features.

## Inputs

Latest local report-only CSV:

- `reports/api-permission-review.csv`
- 16 review rows
- `deny/missing_scope=8` for `user_id=8`
- `allow/superuser=8` for `user_id=1`
- Safe CSV fields only: `time`, `user_id`, `endpoint`, `method`, `scope`, `decision`, `reason`

Dry-run command used:

```powershell
$reportPath = (Resolve-Path "reports").Path
docker-compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
  -v "${reportPath}:/app/reports" `
  web `
  python manage.py plan_api_scope_grants `
  --report-csv reports/api-permission-review.csv `
  --active-only
```

No `--apply` was used.

## Suggested Groups To Create

The dry-run recommended these role groups. They should be created only after human approval in a reviewed apply CSV.

| Group | Purpose | Create? |
| --- | --- | --- |
| `api_hymns_readers` | Hymn API read-only access. | Suggested |
| `api_hymns_editors` | Hymn metadata read/write access. | Suggested |
| `api_hymns_uploaders` | Hymn read/upload access without broad metadata write. | Suggested |
| `api_humnos_readers` | Humnos metadata lookup access. | Suggested |
| `api_humnos_operators` | Humnos lookup plus download/workflow operation access. | Suggested |

## Suggested Scope Grants

These group grants are suggested by policy and dry-run output. They are not applied in this phase.

| Group | Scope | Action |
| --- | --- | --- |
| `api_hymns_readers` | `api:hymns:read` | Suggest grant |
| `api_hymns_editors` | `api:hymns:read` | Suggest grant |
| `api_hymns_editors` | `api:hymns:write` | Suggest grant |
| `api_hymns_uploaders` | `api:hymns:read` | Suggest grant |
| `api_hymns_uploaders` | `api:hymns:upload` | Suggest grant |
| `api_humnos_readers` | `api:humnos:read` | Suggest grant |
| `api_humnos_operators` | `api:humnos:read` | Suggest grant |
| `api_humnos_operators` | `api:humnos:write` | Suggest grant |

Direct user grants are not suggested by this backfill plan. Direct user grants remain exception-only and require separate documented review.

## User Assignments Requiring Human Review

The report-only CSV maps `user_id=8` to the local active staff user `peterchen` in the dry-run output. The user has observed missing scopes for:

- `api:hymns:read`
- `api:hymns:write`
- `api:hymns:upload`
- `api:humnos:read`
- `api:humnos:write`

Candidate group assignments that would cover the observed missing scopes:

| Username | Candidate group | Covers | Review status |
| --- | --- | --- | --- |
| `peterchen` | `api_hymns_editors` | `api:hymns:read`, `api:hymns:write` | Requires human review |
| `peterchen` | `api_hymns_uploaders` | `api:hymns:read`, `api:hymns:upload` | Requires human review |
| `peterchen` | `api_humnos_operators` | `api:humnos:read`, `api:humnos:write` | Requires human review |

These assignments are not automatically approved by report-only observations. A reviewer must confirm whether this user should have write, upload, and humnos operator access. If the answer is no, do not include the corresponding `assign_user_to_group` row in an executable reviewed apply plan.

Staff status is not a grant source. Superuser rows remain audited bypass rows and should not be backfilled with grants.

## Sample CSV Artifacts

Proposal samples:

- `docs/samples/api-scope-reviewed-backfill-sample.csv`
- `docs/samples/api-scope-reviewed-backfill-rollback-sample.csv`

The backfill sample is a proposal artifact. It includes group creation, group grant, and candidate user assignment rows with review notes. Before any apply, a human reviewer must:

1. Remove unapproved user assignment rows.
2. Replace sample reviewer/ticket metadata with the real approval metadata.
3. Compute and record the reviewed plan checksum.
4. Run the apply command in dry-run mode and inspect the audit preview.
5. Prepare the rollback CSV for the exact approved rows.
6. Use `--apply --confirm-apply` only in a later explicitly approved phase.

This phase did not run `--apply`.

## Rollback Mapping

Rollback must be explicit and reviewed. The sample rollback CSV maps proposed apply rows as follows:

| Apply action | Rollback action |
| --- | --- |
| `create_group_grant` | `disable_group_grant` |
| `assign_user_to_group` | `remove_user_from_group` |
| `create_user_grant` | `disable_user_grant` |
| `create_group` | Keep group by default; optional cleanup only through reviewed `delete_empty_group` with `--delete-empty-groups`. |

Groups should not be deleted by default. Disabling grants preserves audit continuity. Incident rollback can still use `API_PERMISSION_MODE=off` without deleting grant data.

## Acceptance Notes

- Groups suggested: five role groups.
- Group grants suggested: eight role-to-scope grants.
- User assignments: candidate assignments exist for `peterchen`, but all require human review.
- Direct user grants: none suggested.
- Apply status: no `--apply` executed.
- Enforcement status: `API_PERMISSION_MODE=enforce` not enabled.
- Default status: `API_PERMISSION_MODE` remains `off` by default.

## Next Step

Review the candidate user assignments with the operational owner. If approved, create a final reviewed apply CSV and matching rollback CSV from the samples, run dry-run validation with checksum pinning, and only then consider a separately approved local apply. Enforcement remains out of scope until reviewed grants, rollback, audit output, smoke tests, CSRF tests, and full pytest results are accepted.
