# API Scope Grant Assignment Review

Created: 2026-05-30

## Goal

Use `report_api_effective_scopes` and report-only API permission logs to design a group/user API scope grant assignment plan. This phase is review-only: it documents policy and adds a read-only planning command, but it does not write grants or change API behavior.

## Constraints

- Did not deploy to `.240`.
- Did not connect to `.240`.
- Did not modify `.240`.
- Did not enable `API_PERMISSION_MODE=enforce`.
- Did not change default API behavior; default remains `off`.
- Did not automatically backfill any group or user grants.
- Did not add business features.

## Current Canonical Scopes

The current canonical scope registry must keep these scope strings stable:

| Scope | Purpose | Grant note |
| --- | --- | --- |
| `api:hymns:read` | Read hymn metadata through `/api/hymns/*` GET endpoints. | Can be assigned to a reviewed reader/editor/uploader group. |
| `api:hymns:write` | Create, update, and delete hymn metadata. | Assign only to a reviewed hymn editor group or documented exception. |
| `api:hymns:upload` | Upload hymn files. | Keep separate from metadata write; assign only to upload operators. |
| `api:humnos:read` | Lookup humnos media metadata through `/api/humnos/info/`. | Read-like operation even though the endpoint uses POST. |
| `api:humnos:write` | Run humnos side-effect/download workflow. | Treat as higher-risk operator scope because it can trigger work/resource use. |

## Endpoint Mapping

| Endpoint | Method | Required scope | Category |
| --- | --- | --- | --- |
| `/api/hymns/` | GET | `api:hymns:read` | read |
| `/api/hymns/` | POST | `api:hymns:write` | write |
| `/api/hymns/<pk>/` | GET | `api:hymns:read` | read |
| `/api/hymns/<pk>/` | PUT | `api:hymns:write` | write |
| `/api/hymns/<pk>/` | DELETE | `api:hymns:write` | destructive write |
| `/api/hymns/<pk>/upload/` | POST | `api:hymns:upload` | upload |
| `/api/humnos/info/` | POST | `api:humnos:read` | read-like lookup |
| `/api/humnos/download/` | POST | `api:humnos:write` | download/write workflow |

## Inputs Used

- `report_api_effective_scopes` lists current stored effective scopes per user, including staff/superuser flags and visible superuser bypass reason.
- Report-only logs identify observed required scopes and `allow/superuser` or `deny/missing_scope` decisions without blocking requests.
- `plan_api_scope_grants` combines the canonical mapping, current effective scopes, and optional report-only CSV rows into a read-only grant plan.

## Grant Assignment Policy

### Superuser Bypass

Superusers should keep the audited bypass behavior:

- Do not backfill superuser group grants.
- Do not backfill superuser user grants.
- Continue reporting superuser activity as `reason=superuser`.
- Summarize superuser bypass counts separately so they do not hide missing role design.

### Group Grants First

Group grants are the normal assignment path. Recommended initial role groups:

| Group | Suggested scopes | Intended use |
| --- | --- | --- |
| `api_hymns_readers` | `api:hymns:read` | Users that need hymn API read access only. |
| `api_hymns_editors` | `api:hymns:read`, `api:hymns:write` | Users that maintain hymn metadata. |
| `api_hymns_uploaders` | `api:hymns:read`, `api:hymns:upload` | Users that upload hymn files without broad metadata write. |
| `api_humnos_readers` | `api:humnos:read` | Users that look up humnos media metadata. |
| `api_humnos_operators` | `api:humnos:read`, `api:humnos:write` | Users that may run the humnos download/workflow operation. |

These names are recommendations only. Creating groups or assigning users should be a reviewed follow-up, not an automatic command side effect.

### User Grants As Exceptions

Direct user grants should be rare and documented:

- Use for temporary access, service-like accounts, or one-off exceptions that cannot be modeled cleanly as a group.
- Review existing direct user grants periodically.
- Prefer moving repeated direct grants into a group.
- Never use direct user grants as an implicit staff backfill.

### Staff Does Not Imply Scope

`is_staff=True` grants no API scopes by default:

- Staff can access Django admin surfaces according to Django/admin permissions.
- API access still requires explicit group or user grants.
- Read scopes are not automatic for staff.
- Write/upload/download scopes are never granted solely because a user is staff.

## Existing Groups/Users Review Approach

For each active non-superuser observed in report-only logs:

1. Use `report_api_effective_scopes --active-only` to see current stored effective scopes.
2. Compare observed `deny/missing_scope` rows with effective scopes.
3. If a missing scope matches an ongoing operational role, assign the user to a reviewed group in a later manual/apply phase.
4. If the access is temporary or exceptional, consider a direct user grant only after documenting the reason.
5. If the user is staff with no matching group grant, keep the result as `staff_no_default_scope` until a role group is approved.

For superusers:

1. Keep `superuser` as the reason.
2. Do not create grants to explain superuser activity.
3. Use bypass counts to decide whether a real non-superuser role is missing.

## Read-only Grant Plan Command

Added management command:

```powershell
python backend/manage.py plan_api_scope_grants --report-csv reports/api-permission-review.csv --active-only
```

Output is CSV with:

- `endpoint_mapping` rows for canonical endpoint/scope mapping.
- `group_grant` rows for recommended group grants.
- `user_review` rows for users with effective scopes or report-only missing-scope observations.
- `superuser_bypass` rows summarizing report-only superuser decisions.

The command only reads database state and optional CSV input. It does not create groups, create grants, update grants, assign users, enable enforce mode, or change API defaults.

## Review Result

Recommended grant policy:

1. Keep superuser bypass audited and grant-free.
2. Use group grants as the default path.
3. Use direct user grants only for documented exceptions.
4. Do not infer API scopes from `is_staff`.
5. Do not infer API scopes from page/menu visibility.
6. Do not automatically backfill grants from report-only logs.

## Next Step

After this review is accepted, the next phase should run the read-only plan against a local/staging-like report-only CSV, manually review actual users/groups, and prepare a separate apply proposal or migration plan. Enforcement should remain out of scope until grants are reviewed, tests pass, rollback is documented, and `API_PERMISSION_MODE=off` remains the default rollback lever.
