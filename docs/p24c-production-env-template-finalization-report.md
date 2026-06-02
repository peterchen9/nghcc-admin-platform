# P24C Production Env Template Finalization Report

Scope: production environment template and policy documentation only.

Guardrails preserved:

- No deploy.
- No `.240` connection.
- No production env creation or modification.
- No production DB modification.
- No production migration execution.
- No API scope apply.
- No `API_PERMISSION_MODE=enforce`.
- No merge.
- No PR.

## Changes made

| File | Change |
| --- | --- |
| `.env.production.example` | Hardened comments and placeholder values, documented required production policies, and marked template values as unusable until replaced. |
| `docs/p24c-production-env-template-finalization-report.md` | Added this decision report. |

## Required variable policy

Production `.env.production` must explicitly set the following values before any deployment approval:

| Area | Required variables | Policy |
| --- | --- | --- |
| App identity | `APP_NAME`, `APP_ENV`, `COMPOSE_PROJECT_NAME` | Keep production-specific names explicit. |
| HTTP/HTTPS entrypoint | `APP_PORT`; optional `APP_TLS_PORT` | Prefer HTTPS for real user access. HTTP requires an approved temporary internal-only exception. |
| Django secret/debug | `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DEBUG` | Secret must be high entropy and secret-managed. Debug must remain false. |
| Host policy | `DJANGO_ALLOWED_HOSTS` | Exact approved host/domain list only. No wildcard hosts. Raw IP access requires explicit approval. |
| Origin/CSRF policy | `CSRF_TRUSTED_ORIGINS`, `ENABLE_CSRF_PROTECTION` | CSRF remains enabled for production target. Origins must include exact scheme, host, and non-standard port. |
| Permission policy | `ENABLE_MENU_PERMISSION_ENFORCEMENT`, `API_PERMISSION_MODE` | Menu enforcement remains off until separately approved. API mode remains `off`; `enforce` is NO-GO without explicit approval. |
| Cookie/security headers | `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SESSION_COOKIE_HTTPONLY`, `CSRF_COOKIE_HTTPONLY`, `SECURE_CONTENT_TYPE_NOSNIFF`, `X_FRAME_OPTIONS` | Secure cookies must match the final browser URL. HTTPS should keep secure cookies true. |
| Database | `DB_ENGINE`, `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_ROOT_PASSWORD` | DB values must be explicit and non-default. `DB_HOST=db` keeps traffic inside compose. MySQL must not be published. |
| Uploads | `UPLOAD_DIR`, `UPLOAD_MAX_SIZE_MB`, `UPLOAD_ALLOWED_EXTENSIONS`, `UPLOAD_STRICT_MIME_CHECK` | Upload limits and allowed extensions stay explicit. Strict MIME mode remains deferred until legacy upload behavior is verified. |

## Placeholder policy

`.env.production.example` contains `UNUSABLE_REPLACE_ME_*` values on purpose.

These values are allowed only for local compose config rendering. They must not be copied into a real production `.env.production`. A production release must block if any required variable is empty, missing, set to a local default, or still contains an `UNUSABLE_REPLACE_ME_*` placeholder.

Unsafe values include:

- `local-dev-only-secret`
- `change_me`
- wildcard hosts such as `*`
- localhost-only browser hosts for production
- unapproved raw IP hosts
- HTTP origins without an approved temporary exception
- `API_PERMISSION_MODE=enforce` without explicit security approval
- published MySQL host ports

## HTTP/HTTPS and cookie decision

Production target remains HTTPS-preferred:

- If users access the app through HTTPS, keep `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True`.
- If a temporary HTTP-only internal production phase is approved, set those cookie flags to `False` only for that approved phase and document the exception.
- Cookie policy must match the final browser URL and reverse proxy behavior, not only internal container traffic.

## Host and origin decision

`DJANGO_ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` are still final-value blockers because no final production host/domain was approved in P24C.

Rules:

- `DJANGO_ALLOWED_HOSTS` must list only approved final browser hosts.
- `CSRF_TRUSTED_ORIGINS` must list only approved final browser origins.
- Non-standard ports must be included in CSRF origins.
- Raw IP access and HTTP origins require explicit approval.

## DB and API mode decision

The production compose example continues to keep MySQL internal-only:

- `DB_HOST=db`
- `DB_PORT=3306`
- no `DB_EXTERNAL_PORT`
- no published MySQL port in `docker-compose.production.example.yml`

`API_PERMISSION_MODE=off` remains the production default and rollback lever. `report-only` and `enforce` are not enabled by P24C. `enforce` requires explicit approval, reviewed scopes, rollback evidence, and security verification.

## Validation results

Commands:

```powershell
docker compose --env-file .env.production.example -f docker-compose.production.example.yml config
docker compose --env-file .env.production.example -f docker-compose.production.example.yml --profile release config
```

Results:

- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml config`: PASS; production compose example rendered with the hardened example env values used for interpolation.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml --profile release config`: PASS; release-profile `migrate` and `collectstatic` services rendered successfully.
- Validation was config-only. It did not deploy, start containers, connect to `.240`, create a production env, modify production DB, or run migrations.

## Remaining production NO-GO blockers

Production remains **NO-GO** until all of the following are closed:

- Real `.env.production` is created outside Git with every `UNUSABLE_REPLACE_ME_*` value replaced.
- Final production host/domain is approved.
- Final CSRF trusted origin list is approved.
- HTTPS/TLS and secure-cookie decision is approved.
- Backup, restore, and rollback evidence is recorded.
- Production-like static/media verification through Nginx passes.
- Production-like smoke and CSRF verification through the final public URL passes.
- Any production migration receives explicit approval.
- Any future `API_PERMISSION_MODE=enforce` receives explicit approval.

## GO / NO-GO

| Question | Decision | Reason |
| --- | --- | --- |
| GO for hardened production env template? | GO | Template now documents required variables and marks placeholders unusable. |
| GO for compose config validation? | GO | Production and release-profile compose config rendering passed. |
| GO for production deploy? | NO-GO | Final host/origin/TLS/secrets/backup/rollback and production-like verification remain open. |
| GO for production migration? | NO-GO | No migration approval or backup/rollback evidence in this phase. |
| GO for `API_PERMISSION_MODE=enforce`? | NO-GO | Enforcement requires a separate approved security phase. |
