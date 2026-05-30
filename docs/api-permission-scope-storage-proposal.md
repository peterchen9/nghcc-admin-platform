# API Permission Scope Storage Proposal

Created: 2026-05-30

## Goal

Design durable storage for API permission scopes before any enforcement rollout. This proposal is design-only: it does not change runtime behavior, does not add models or migrations, and does not enable `API_PERMISSION_MODE=enforce`.

## Constraints

- Do not deploy to `.240`.
- Do not connect to `.240`.
- Do not modify `.240`.
- Do not enable `API_PERMISSION_MODE=enforce`.
- Do not change the default API behavior; default remains `off`.
- Do not add database tables or migrations in this phase.
- Do not add business features.
- Do not implement storage in this phase.

## Current Baseline

The current API permission skeleton maps selected endpoints to string scopes and supports three modes: `off`, `report-only`, and `enforce`. The default is `off`. In `report-only`, the helper logs allow/deny decisions without blocking requests.

Current scope checks are intentionally temporary:

- Superusers are allowed with reason `superuser`.
- Non-superusers are allowed only if an in-memory `user.api_scopes` iterable contains the required scope.
- Normal active users without `api_scopes` produce `deny/missing_scope` in report-only logs.

Durable scope storage is therefore required before `enforce` can be considered.

## Required Scope Set

Initial storage must support these existing scope strings without renaming them:

| Scope | Purpose | Notes |
| --- | --- | --- |
| `api:hymns:read` | Read hymn metadata through `/api/hymns/*` GET endpoints. | Read-only API scope; not page menu visibility. |
| `api:hymns:write` | Create/update/delete hymn metadata. | Must be explicit; should not follow staff automatically. |
| `api:hymns:upload` | Upload hymn files. | Separate from metadata write because file upload has different risk. |
| `api:humnos:read` | Lookup humnos media metadata through `/api/humnos/info/`. | POST method, but read-like operation. |
| `api:humnos:write` | Run humnos side-effect/download workflow. | May later split into `api:humnos:download`; storage should allow that. |

## Design Requirements

1. Store user-level API scope grants.
2. Store group-level API scope grants.
3. Calculate effective scopes deterministically.
4. Keep staff defaults conservative and explicit.
5. Preserve superuser bypass as a visible audited decision.
6. Support migration/backfill from current users/groups without changing default behavior.
7. Support rollback by disabling use of stored scopes or returning to report-only/off.
8. Allow review tooling to list effective scopes before enforcement.
9. Avoid coupling API authorization to page/menu visibility.
10. Avoid broad wildcard behavior unless a future migration explicitly adds and tests it.

## Option A: New API Scope Model

Create a dedicated API permission domain with explicit scope records and grant records.

Proposed conceptual model:

| Entity | Purpose |
| --- | --- |
| `ApiScope` | Canonical scope registry, for example `api:hymns:read`, with label, category, active flag, and description. |
| `UserApiScopeGrant` | Direct grant from user to scope, with enabled flag and audit metadata. |
| `GroupApiScopeGrant` | Grant from Django group to scope, with enabled flag and audit metadata. |

No migration is added in this phase; these are future implementation candidates.

### User Scope Grants

User grants are direct exceptions or precise assignments. They should include:

- `user`
- `scope`
- `enabled`
- `created_at`
- `created_by`
- optional `reason`

Direct user grants should be used sparingly for exceptions, service-like accounts, or temporary access that cannot be expressed through a group.

### Group Scope Grants

Group grants are the normal administrative path. They should include:

- `group`
- `scope`
- `enabled`
- `created_at`
- `created_by`
- optional `reason`

Groups should represent operational roles, not page routes. Example future groups could include hymn editors, hymn uploaders, humnos operators, and API reviewers.

### Effective Scope Calculation

For authenticated non-superusers:

1. Start with an empty set.
2. Add scopes from enabled group grants for all groups the user belongs to.
3. Add scopes from enabled direct user grants.
4. Add staff default scopes only if a future setting explicitly enables a documented staff policy.
5. Return allow only when the required scope is in the effective set.

There is no deny grant in the first implementation. This keeps the merge rule simple, auditable, and reversible. If deny grants are ever needed, they should be a separate proposal because deny precedence can create surprising outcomes.

### Staff Default Policy

Recommended staff default policy:

- `is_staff=True` grants no API scopes by default.
- Staff access remains an admin-site capability, not an API authorization role.
- Any staff API access must come from explicit group or user grants.
- Read scopes may be backfilled to a documented group if local report-only review proves they are needed.
- Write/upload/download scopes must never be granted solely because `is_staff=True`.

This preserves current default behavior and avoids silently widening API access.

### Superuser Bypass Audit

Superuser bypass should remain allowed, but it must be visible.

Audit/report-only output should continue to emit:

- `decision=allow`
- `reason=superuser`
- `user_is_superuser=True`
- required scope
- endpoint
- method

Future review tooling should summarize superuser bypass counts separately from explicit scope grants so superuser activity does not hide missing role design.

### Migration / Backfill Strategy

Future implementation should use a staged, reversible backfill:

1. Add storage behind `API_PERMISSION_MODE=off` and keep behavior unchanged.
2. Create canonical `ApiScope` rows for current scope strings.
3. Create role groups only after reviewing local/staging report-only logs.
4. Backfill no grants for normal users by default.
5. Backfill no grants for staff by default.
6. Backfill no grants for superusers; they continue to rely on audited bypass.
7. Optionally create empty suggested groups, such as `api_hymns_readers`, without assigning users until reviewed.
8. Run report-only comparison between required scopes and effective scopes.
9. Only after review, assign explicit group/user grants locally or in a reviewed migration plan.

The backfill should produce a review report before any permission data is changed in production-like data.

### Rollback Strategy

Rollback should not require data deletion.

1. Set `API_PERMISSION_MODE=off` to bypass all API permission checks.
2. If needed, keep `report-only` off until logs are reviewed.
3. Leave scope tables and grants in place but unused.
4. Revert the code path that reads storage if it causes errors.
5. Do not delete grant data during incident rollback; preserve it for audit.

Because the current default remains `off`, the primary rollback lever is the existing feature flag.

### Pros

- Cleanly separates API authorization from UI/menu visibility.
- Supports user and group grants directly.
- Keeps scope names stable and auditable.
- Allows review tooling to show exact effective scopes.
- Avoids overloading Django permission codenames with API-specific semantics.

### Cons

- Requires new models and migrations in a later implementation phase.
- Requires an admin/review UI or management command later.
- Adds a new authorization surface that must be documented and tested.

## Option B: Reuse Django Permission

Represent API scopes as Django permissions, either on existing models or a proxy/content-type holder.

### User Scope Grants

Direct grants would use `user.user_permissions`. The effective scope check would map `api:hymns:read` to a Django permission codename, then call Django permission APIs.

### Group Scope Grants

Group grants would use `group.permissions`. This reuses mature Django admin behavior and existing group concepts.

### Effective Scope Calculation

For authenticated non-superusers:

1. Map required API scope to a Django permission codename.
2. Use Django's permission resolution across user and group permissions.
3. Preserve superuser bypass as a separate audited reason.
4. Treat staff as no API scopes unless assigned permissions.

### Pros

- Reuses Django's built-in user/group permission storage.
- Avoids new grant tables if permissions can be created through migrations.
- Admin UI already exists.
- Familiar to Django maintainers.

### Cons

- Django permissions are model/content-type centered, while these scopes are endpoint/operation centered.
- Existing model permissions may imply CRUD semantics that do not match API behavior, especially upload/download.
- Creating custom permissions still needs migrations.
- Effective scope reports need mapping logic from API scope strings to permission codenames.
- Higher risk that future maintainers conflate page, model, and API authorization.

## Option C: Reuse Menu Permission

Use existing menu permission assignments as the source of API scopes.

### User Scope Grants

User grants would come from menu items assigned directly or indirectly to a user. A mapping table or code map would translate menu routes to API scopes.

### Group Scope Grants

If groups are layered onto menu permissions later, group grants would follow the same menu-to-scope mapping.

### Effective Scope Calculation

For authenticated non-superusers:

1. Resolve allowed menu routes.
2. Map those routes to API scopes.
3. Allow when the required API scope is included.

### Pros

- Reuses existing UI visibility data.
- May feel intuitive for page-specific read access.
- Minimal conceptual change for page navigation permissions.

### Cons

- Menu permissions describe UI visibility, not API operations.
- `/api/humnos/info/` and `/api/humnos/download/` do not map cleanly to page access.
- Write/upload/download would become dangerously coupled to seeing a page.
- Menu routes cannot express endpoint method distinctions cleanly.
- Previous read-only API planning already concluded API read permission should not be derived from page menu permission.

## Recommendation

Adopt **Option A: New API Scope Model**.

Reasons:

1. API authorization needs endpoint and method semantics, not page visibility.
2. Upload and download/side-effect workflows need separate grantability from generic page access.
3. User and group grants can be reviewed and reported without translating through menu routes or model codenames.
4. Staff can remain conservative by default.
5. Superuser bypass can stay explicit and auditable.
6. Future enforcement can read one API-specific effective-scope source while preserving `API_PERMISSION_MODE=off` as rollback.

Option B is a viable fallback if the project strongly prefers Django admin-native permission management, but it should still keep API scope strings as the public contract and avoid reusing generic model CRUD permissions directly. Option C should not be used for API scope storage.

## Proposed Future Tests

When implementation begins, add focused tests before enabling enforcement:

- Direct user grant allows the required scope.
- Group grant allows the required scope.
- User with no direct or group grant logs/denies `missing_scope`.
- Staff without explicit grants receives no API scope.
- Superuser bypass allows and reports `reason=superuser`.
- Upload scope is independent from metadata write scope.
- Humnos read scope is independent from humnos write/download scope.
- Invalid or inactive scope grants are ignored.
- `API_PERMISSION_MODE=off` preserves existing responses.
- `API_PERMISSION_MODE=report-only` preserves existing responses and logs effective-scope reason.

## Next Step

Implement Option A behind the existing feature flag in a later phase:

1. Add models and migrations only after this proposal is reviewed.
2. Add a management/report command to list effective scopes.
3. Add tests for effective-scope calculation.
4. Run local report-only comparison.
5. Keep default mode `off`.
6. Do not consider `enforce` until storage, audit, tests, and rollback have been verified.

## Implementation Phase 1 Status

Updated: 2026-05-30

Option A phase 1 has been implemented locally with storage and report-only helpers only.

Added:

- `ApiScope`
- `UserApiScopeGrant`
- `GroupApiScopeGrant`
- Canonical `ApiScope` seed migration for:
  - `api:hymns:read`
  - `api:hymns:write`
  - `api:hymns:upload`
  - `api:humnos:read`
  - `api:humnos:write`
- `get_effective_api_scopes(user)`
- `get_effective_api_scope_decision(user, scope)`
- `report_api_effective_scopes` management command

Effective-scope phase 1 rules:

1. Superusers receive an audited allow decision with `reason=superuser`, but no stored grants are backfilled.
2. Non-superuser effective scopes are the union of enabled active group grants and enabled active direct user grants.
3. `is_staff=True` grants no API scopes by default.
4. Disabled grants and inactive scopes are ignored.
5. Deny grants and wildcard scopes are not implemented.

Behavior constraints preserved:

- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce` enablement.
- `API_PERMISSION_MODE` default remains `off`.
- Existing API decorator blocking behavior is not changed by the storage helper.
- No formal user/group grants are backfilled.

## Transactional Apply Phase Status

Updated: 2026-05-30

Reviewed transactional writes have been added for the storage model without changing API enforcement behavior.

- `apply_api_scope_reviewed_plan` remains dry-run by default.
- Mutating apply requires both `--apply` and `--confirm-apply`.
- Apply is limited to reviewed local plan actions: create group, create group grant, create user grant, and assign user to group.
- Each mutating row writes `ApiScopeGrantAudit` in the same database transaction.
- Rollback action rows remain dry-run/preview-only for this phase.
- No grants are automatically backfilled from report-only logs or existing staff/superuser status.
