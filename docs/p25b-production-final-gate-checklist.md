# P25B Production Final-Gate Checklist

Scope: documentation-only final pre-production gate checklist derived from P25.

Guardrails preserved:

- No deploy.
- No `.240` connection.
- No production env creation or modification.
- No production DB access or modification.
- No production migration.
- No backup or restore command executed against production.
- No API scope apply.
- No `API_PERMISSION_MODE=enforce`.
- No merge.
- No PR.

## 1. P25 Local Drill Summary

P25 validated the production-like stack locally on 2026-06-02:

| Area | P25 result |
| --- | --- |
| Production compose startup | PASS; `docker-compose.production.example.yml` brought up DB, web, and Nginx locally. |
| Static flow | PASS; `collectstatic` copied `1412` files and `/static/admin/css/base.css` returned `200 text/css` through Nginx. |
| Media flow | PASS; temporary media probe returned `200 text/plain`; `/media/` directory probe returned `404`. |
| CSRF negative-path | PASS; unauthenticated/missing-token POST returned `403`. |
| Smoke probes | PASS; `/api/health/`, `/admin/login/`, `/`, `/hymns/`, `/webav/`, `/eureka/`, `/api/hymns/`, `/api/humnos/info/`, and `/ckeditor/upload/` returned expected local drill responses. |
| Runbook assumptions | PASS; `migrate` and `collectstatic` ran as release-profile one-off commands; web startup ran Gunicorn only. |
| Local cleanup | PASS; temporary drill env files and media probe were removed; local compose stack was restored. |

P25 proves the production-like stack can be validated locally. It does not prove
that the real production environment is ready.

## 2. Remaining Production-Only Gaps

| Gap | Status | Required evidence |
| --- | --- | --- |
| Real production env | Open | Approved `.env.production` outside Git with no placeholders, local defaults, or wildcard hosts. |
| Final production host/domain | Open | Approved final `DJANGO_ALLOWED_HOSTS`; bad-host rejection evidence. |
| Final CSRF origins | Open | Approved final `CSRF_TRUSTED_ORIGINS`; credentialed CSRF checks from final browser origin. |
| HTTPS/TLS decision | Open | Approved TLS certificate/proxy plan, or explicit temporary HTTP-only exception. |
| Secure-cookie decision | Open | `SESSION_COOKIE_SECURE` and `CSRF_COOKIE_SECURE` match the final browser URL and TLS decision. |
| `.240` access approval | Open | Explicit instruction naming host, purpose, operator, date/window, and allowed commands. |
| Production backup evidence | Open | DB dump, media archive, compose/env snapshot, rendered config, checksums, and retention location. |
| Restore drill evidence | Open | Staging-like restore drill using production backup artifacts passes before migration approval. |
| Production static/media evidence | Open | `/static/` and `/media/` pass through final public URL under `DEBUG=False`. |
| Authenticated final-URL smoke | Open | Approved credentialed smoke verifies core workflows through the final public URL. |
| Production migration approval | Open | Explicit approval after backup/checksum/restore evidence; migration remains one-off. |
| API enforcement approval | Open/deferred | `API_PERMISSION_MODE=off` remains default; `enforce` requires separate security approval. |

## 3. Required Real Production Inputs

Production deploy planning cannot start until these inputs are provided and
recorded:

- Approved production target host, path, and operator.
- Approved final public URL and whether raw IP access is allowed.
- Approved deployment window and rollback decision window.
- Approved production compose file or production copy of `docker-compose.production.example.yml`.
- Approved production Nginx config and TLS/proxy owner.
- Real `.env.production` outside Git with:
  - `DJANGO_SECRET_KEY`
  - `DJANGO_DEBUG=False`
  - `DEBUG=False`
  - `DJANGO_ALLOWED_HOSTS`
  - `CSRF_TRUSTED_ORIGINS`
  - `ENABLE_CSRF_PROTECTION=True`
  - `SESSION_COOKIE_SECURE`
  - `CSRF_COOKIE_SECURE`
  - `DB_ENGINE`
  - `DB_HOST`
  - `DB_PORT`
  - `DB_NAME`
  - `DB_USER`
  - `DB_PASSWORD`
  - `DB_ROOT_PASSWORD`
  - `API_PERMISSION_MODE=off`
- Approved staff/test credentials for final-URL smoke verification.
- Approved backup storage location and retention period.
- Approved rollback owner and incident communication path.

Any `UNUSABLE_REPLACE_ME_*`, `change_me`, `local-dev-only-secret`, wildcard
host, unapproved HTTP origin, or `API_PERMISSION_MODE=enforce` value is a hard
**NO-GO**.

## 4. `.240` Access Prerequisites

Access to `.240` remains **NO-GO** unless all prerequisites are met:

- The user explicitly instructs access to `.240` for this phase.
- The instruction names the exact purpose: inspect only, backup, deploy, smoke,
  rollback, or another approved action.
- The approved command scope is recorded before access.
- The production target path is confirmed before any write action.
- A no-write/no-migration mode is used unless explicit write or migration
  approval is included.
- Current git commit and local working tree status are recorded.
- Secrets are not printed into chat or committed.
- No production DB mutation occurs without separate explicit approval.

If access is approved for inspection only, do not deploy, restart, migrate,
restore, edit env, or modify files.

## 5. Backup and Restore Evidence Gate

Before any production deploy or migration:

| Evidence | Required before GO |
| --- | --- |
| DB backup | `mysqldump` from internal DB container/network, non-zero `.sql.gz`, exit code `0`. |
| Media backup | Archive of production media volume/path, non-zero `.tar.gz`, exit code `0`. |
| Compose snapshot | Current production compose file copied into backup evidence directory. |
| Env snapshot | Current production env copied outside Git and handled as a secret. |
| Rendered config | `docker compose ... config` output captured for the approved env/compose. |
| Checksums | `SHA256SUMS-<release_id>.txt` generated and verified with `sha256sum -c`. |
| Restore drill | DB and media restore drill passes in staging-like environment using the captured artifacts. |
| Rollback decision | Rollback owner chooses forward fix vs restore policy before migration. |

Missing backup, checksum, or restore-drill evidence is a hard **NO-GO**.

## 6. Final Host, Origin, TLS, and Cookie Gate

Before deploy planning can proceed:

- `DJANGO_ALLOWED_HOSTS` must list only approved final browser hosts.
- `CSRF_TRUSTED_ORIGINS` must list exact final browser origins with scheme and
  non-standard port when applicable.
- HTTPS is preferred for real user access.
- Temporary HTTP-only production requires explicit written exception, internal
  access scope, and compensating controls.
- `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` are required for
  HTTPS.
- If HTTP-only exception is approved, secure-cookie flags may be `False` only
  for that exception window.
- Bad-host request must return rejected/invalid-host behavior.
- Cookie headers must be inspected through the final public URL.

Unapproved host/origin/TLS/cookie values are **NO-GO**.

## 7. Authenticated Final-URL Smoke Checklist

Smoke verification must use the final public URL through Nginx or the approved
reverse proxy. Do not bypass the proxy by calling Django directly.

Required checks:

| Check | Expected result |
| --- | --- |
| `/api/health/` | `200`, database status `ok`. |
| `/admin/login/` GET | `200`, CSRF cookie issued. |
| Admin login POST with CSRF | Authenticates approved staff account. |
| Admin page | Loads for approved staff account. |
| Logout POST with CSRF | Completes expected protected logout flow. |
| `/static/admin/css/base.css` | `200 text/css`. |
| Known `/media/<file>` | `200` with expected content type. |
| `/media/` directory probe | No directory listing; expected `404` or equivalent. |
| CKEditor upload | Staff-only, POST-only, CSRF-protected positive path verified. |
| `/hymns/` or approved hymns flow | Loads or redirects according to auth policy. |
| `/webav/` humnos flow | Loads or redirects according to auth policy. |
| `/eureka/` flow | Loads or redirects according to auth policy. |
| Eureka delete | GET is non-destructive; POST requires CSRF. |
| API permission mode | Confirm `API_PERMISSION_MODE=off` unless separately approved. |
| Bad Host header | Rejected with invalid-host behavior. |
| Cookie headers | Match HTTPS/HTTP decision. |

Authenticated final-URL smoke must be recorded before production deploy GO.

## 8. Final Gate Decision Table

| Gate | Required status for GO | Current P25B status |
| --- | --- | --- |
| P25 local production-like drill | PASS | GO |
| Real production env | Approved and placeholder-free | NO-GO |
| `.240` access | Explicitly approved and scoped | NO-GO |
| Final host/origin/TLS/cookie | Approved and documented | NO-GO |
| Production backup/checksum | Captured and verified | NO-GO |
| Restore drill | Completed and recorded | NO-GO |
| Production compose/runtime | Approved target config rendered | NO-GO |
| Static/media final URL | Verified through proxy | NO-GO |
| Authenticated final-URL smoke | Completed with approved credentials | NO-GO |
| Production migration | Explicitly approved one-off action | NO-GO |
| `API_PERMISSION_MODE=enforce` | Separately approved if used | NO-GO |
| Production deploy planning | All gates above satisfied | NO-GO |

## 9. GO / NO-GO

| Question | Decision | Reason |
| --- | --- | --- |
| GO for P25B final-gate checklist? | GO | P25 findings were converted into explicit production pre-gates. |
| GO for requesting production inputs? | GO | Inputs are now listed and can be gathered without production action. |
| GO for `.240` access? | NO-GO | No explicit `.240` access approval is included in P25B. |
| GO for production deploy planning? | NO-GO | Required production env, access, backup, host/origin/TLS, restore, and smoke evidence are missing. |
| GO for production deploy? | NO-GO | Final gates are not satisfied. |
| GO for production DB modification or migration? | NO-GO | No explicit approval or backup/restore evidence. |
| GO for `API_PERMISSION_MODE=enforce`? | NO-GO | Requires separate security approval. |

## 10. P25B Validation Results

Validation performed:

- Read back `AGENTS.md`.
- Reviewed P25 staging-like readiness drill report.
- Reviewed P24E closure review.
- Reviewed P24C env policy and P24D migration/backup/rollback runbook.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml config`: PASS; production compose example rendered without starting containers.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml --profile release config`: PASS; release-profile `migrate` and `collectstatic` services rendered without starting containers.

No runtime tests were run because P25B is docs-only and does not change
application behavior, compose behavior, settings, or scripts.
