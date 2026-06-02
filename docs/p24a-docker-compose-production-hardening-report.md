# P24A Docker/Compose Production Hardening Report

Scope: production-ready Docker/Compose architecture examples and local validation only.

Guardrails preserved:

- No deploy.
- No `.240` connection.
- No production env modification.
- No production DB modification.
- No production migration execution.
- No API scope apply.
- No `API_PERMISSION_MODE=enforce`.
- No merge.
- No PR.

## Changes made

| File | Change |
| --- | --- |
| `docker-compose.production.example.yml` | Added production compose example with Nginx entrypoint, internal-only DB, named static/media/mysql volumes, web healthcheck, and release-profile `migrate` and `collectstatic` services. |
| `deploy/nginx/nghcc-admin-platform.conf.example` | Added reverse proxy example that serves `/static/` and `/media/` directly and proxies Django/Gunicorn traffic to `web:8000`. |
| `.env.production.example` | Replaced unclear placeholder content with an explicit production template and required-value policy. |
| `docs/p24a-docker-compose-production-hardening-report.md` | Added this report. |

Existing local `docker-compose.yml` and `backend/Dockerfile` were not changed, so local compose behavior is preserved.

## Production compose strategy

The production example is a separate file and is not automatically used by local development:

```text
docker-compose.production.example.yml
```

Key strategy:

- `nginx` is the only published HTTP entrypoint.
- `web` exposes port `8000` only inside Docker networking.
- `db` has no published host port.
- `nghcc-admin-mysql-data` stores MySQL data.
- `nghcc-admin-static-data` stores collected static files.
- `nghcc-admin-media-data` stores uploaded media.
- `migrate` is a release-profile one-off service.
- `collectstatic` is a release-profile one-off service.
- `web` startup runs only gunicorn and does not automatically run migrations.

The example keeps rollback feasible because schema changes are separated from normal container restart, static/media/mysql data are on named volumes, and the runtime topology can be rolled back independently from release commands.

## Nginx/static/media strategy

The Nginx example:

- Serves `/static/` from `/var/www/nghcc-admin/static/`.
- Serves `/media/` from `/var/www/nghcc-admin/media/`.
- Proxies all other traffic to `web:8000`.
- Sets `client_max_body_size 20m`.
- Passes `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Host`, and `X-Forwarded-Proto`.
- Includes HTTPS/TLS comments without assuming a final domain or treating `.240` as the only production environment.

Production TLS remains a separate deployment decision. When HTTPS is enabled, `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` should remain set in production env.

## Env policy

`.env.production.example` now states that production must explicitly set:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `ENABLE_CSRF_PROTECTION=True`
- `SESSION_COOKIE_SECURE`
- `CSRF_COOKIE_SECURE`
- `DB_HOST`
- `DB_PORT`
- `DB_NAME`
- `DB_USER`
- `DB_PASSWORD`
- `DB_ROOT_PASSWORD`
- `API_PERMISSION_MODE=off`

Production must not use placeholder secrets, default DB passwords, wildcard hosts, or `API_PERMISSION_MODE=enforce` unless separately authorized.

## Migration strategy

Production web startup is split from migration:

```text
web command: gunicorn nads26.wsgi:application --bind 0.0.0.0:8000
migrate command: python manage.py migrate --noinput
collectstatic command: python manage.py collectstatic --noinput
```

Required release order before any production migration:

1. Capture DB backup.
2. Capture media backup.
3. Capture compose/env snapshot.
4. Verify checksums.
5. Run migration as an explicit release command.
6. Run smoke tests after migration.
7. Confirm rollback path before changing traffic.

No production migration was executed in P24A.

## Local validation results

Validation commands required for P24A:

```powershell
docker compose build
.\scripts\run-csrf-tests.ps1
.\scripts\run-smoke-tests.ps1
```

Results:

- `docker compose config`: PASS; local compose rendered successfully.
- `docker compose build`: PASS; local web image built successfully.
- `.\scripts\run-csrf-tests.ps1`: PASS; 103 passed, 39 skipped.
- `.\scripts\run-smoke-tests.ps1`: PASS; 103 passed, 39 skipped.

Production example was not deployed or run against production. It was not used for a production-like startup because this phase does not create a real `.env.production`, does not approve production migration, and does not deploy. It is an architecture example that requires a real `.env.production`, backup evidence, and release approval before use.

## Remaining production NO-GO blockers

Production remains **NO-GO** until all of the following are closed:

- Final production host/domain and `DJANGO_ALLOWED_HOSTS` decision.
- Final `CSRF_TRUSTED_ORIGINS` decision.
- HTTPS/TLS and secure-cookie decision.
- Production `.env.production` with real non-placeholder secrets.
- Verified DB backup, media backup, compose/env snapshot, and checksum process.
- Restore and rollback drill.
- Production-like static/media verification through Nginx.
- Production-like smoke verification through the final public URL.
- Explicit approval for any production migration.
- Separate approval before any future `API_PERMISSION_MODE=enforce`.

Recommended next phase: **P24B Static/Media Serving Implementation** after the production compose example is reviewed.
