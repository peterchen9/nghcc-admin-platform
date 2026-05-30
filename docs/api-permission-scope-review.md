# API Permission Scope Review

Created: 2026-05-30

## Goal

Review `reports/api-permission-review.csv` from the local `API_PERMISSION_MODE=report-only` sample, confirm whether `missing_scope` decisions match the current skeleton design, and list scope storage requirements for the next design phase.

## Constraints

- Did not deploy to `.240`.
- Did not connect to `.240`.
- Did not modify `.240`.
- Did not enable `API_PERMISSION_MODE=enforce`.
- Did not change default API behavior; default remains `off`.
- Did not add business features.
- Did not implement or design final scope storage.
- Did not commit `reports/api-permission-review.csv`.

## Review Input

Source: `reports/api-permission-review.csv`

Rows reviewed: 16

Safe review columns only:

| Field | Notes |
| --- | --- |
| `time` | Empty in this local sample. |
| `user_id` | Local user id only. |
| `endpoint` | Decorated API endpoint pattern. |
| `method` | HTTP method. |
| `scope` | Mapped API permission scope. |
| `decision` | Report-only allow/deny decision. |
| `reason` | Decision reason. |

## Decision / Reason Distribution

| decision | reason | count | Review result |
| --- | --- | ---: | --- |
| `allow` | `superuser` | 8 | Expected. Superuser bypass is currently explicit in the permission skeleton. |
| `deny` | `missing_scope` | 8 | Expected. The sampled active non-superuser has no API scope storage or `api_scopes` assignment. |

## Missing Scope Review Result

`missing_scope` is expected for the normal active local user in this report-only sample.

Reason:

- The report-only skeleton checks mapped scopes but does not block in `report-only`.
- No durable API scope storage exists yet.
- The local non-superuser sample has no explicit `api_scopes`.
- `user_has_api_scope()` and `get_api_permission_decision()` currently allow only superuser bypass or in-memory `user.api_scopes` membership.

This means the CSV confirms that the skeleton can identify missing scopes, not that enforcement is ready.

## Endpoint Scope Matrix

| Endpoint | Method | Required scope | Category | Superuser bypass | Staff default scope | Review note |
| --- | --- | --- | --- | --- | --- | --- |
| `/api/hymns/` | GET | `api:hymns:read` | read | Yes | Needs policy decision | Normal active user logged `deny/missing_scope`; expected until storage/default grants exist. |
| `/api/hymns/` | POST | `api:hymns:write` | write | Yes | Do not grant blindly; needs role policy | Write creates hymn metadata; should require explicit role/scope mapping. |
| `/api/hymns/<pk>/` | GET | `api:hymns:read` | read | Yes | Needs policy decision | Read access should be aligned with future API read policy, not page visibility alone. |
| `/api/hymns/<pk>/` | PUT | `api:hymns:write` | write | Yes | Do not grant blindly; needs role policy | Metadata update should require explicit write scope. |
| `/api/hymns/<pk>/` | DELETE | `api:hymns:write` | write | Yes | Do not grant blindly; needs role policy | Destructive action; explicit write scope required. |
| `/api/hymns/<pk>/upload/` | POST | `api:hymns:upload` | upload | Yes | Do not grant blindly; needs role policy | File upload is separate from metadata write and should remain separately grantable. |
| `/api/humnos/info/` | POST | `api:humnos:read` | read | Yes | Needs policy decision | POST method is used for lookup/metadata request, but the mapped operation is read-like. |
| `/api/humnos/download/` | POST | `api:humnos:write` | download/write | Yes | Do not grant blindly; needs role policy | Download/transcode has side effects and resource cost; current mapping treats it as write. |

## Scope Storage Requirements

The next phase should design storage before any `enforce` planning. Requirements:

1. Store explicit API scopes per user and/or per role/group, with deterministic merge rules.
2. Define whether staff receives any default scopes. Default staff grants should be conservative and documented; write/upload/download should not be granted merely because `is_staff=True`.
3. Preserve superuser bypass as an explicit policy decision and make it visible in audit/review output.
4. Support the current scope names without changing default API behavior:
   - `api:hymns:read`
   - `api:hymns:write`
   - `api:hymns:upload`
   - `api:humnos:read`
   - `api:humnos:write`
5. Keep upload and download classifiable separately from generic write in the data model, even if `api:humnos/download/` currently maps to `api:humnos:write`.
6. Provide an admin/review path to list effective scopes for a user before enforce mode exists.
7. Include migration/backfill rules for existing users, especially superuser, staff, and normal active accounts.
8. Log or report enough information to compare effective scopes against report-only decisions without exposing request bodies, tokens, cookies, headers, or query strings.
9. Add tests for explicit scope, inherited scope, no scope, staff without default scope, and superuser bypass before any enforce rollout.
10. Keep `API_PERMISSION_MODE=off` as the default until storage, audit, tests, and rollback steps are documented.

## Next Step Recommendation

Design a scope storage proposal that covers user-level grants, role/group-level grants, effective-scope calculation, staff defaults, superuser bypass, audit output, tests, and migration/backfill. Do not enable `enforce` until that proposal is reviewed and implemented behind the existing feature flag.
