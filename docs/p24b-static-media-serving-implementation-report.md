# P24B Static/Media Serving Implementation Report

Scope: production static/media serving architecture in examples only. No deploy, no `.240` connection, no production env change, no production DB change, and no production migration.

## Current problem

The Django app defines:

| Setting | Current value |
| --- | --- |
| `STATIC_URL` | `static/` |
| `STATIC_ROOT` | `/app/staticfiles` inside the container |
| `STATICFILES_DIRS` | `/app/static` inside the container |
| `MEDIA_URL` | `/media/` |
| `MEDIA_ROOT` | `/app/media` inside the container |

`backend/nads26/urls.py` only serves media when `settings.DEBUG` is true. That is correct for production, but it means the production runtime must provide an external static/media server. Without a reverse proxy serving shared static and media volumes, `DEBUG=False` production would have broken admin assets, app assets, uploaded files, and CKEditor media.

## Changes made

| File | Change |
| --- | --- |
| `docker-compose.production.example.yml` | Kept Nginx, web, `collectstatic`, and media on shared named volumes; made service `env_file` entries optional for compose config validation with `.env.production.example`. |
| `deploy/nginx/nghcc-admin-platform.conf.example` | Added explicit `autoindex off` and `X-Content-Type-Options` while keeping direct `/static/` and `/media/` serving through aliases. |
| `docs/p24b-static-media-serving-implementation-report.md` | Added this report. |

No local `docker-compose.yml` behavior was changed.

## Static serving strategy

Production static files are collected by the release-profile `collectstatic` service:

```text
python manage.py collectstatic --noinput
```

The production example mounts the shared static named volume at:

| Container | Mount |
| --- | --- |
| `collectstatic` | `nghcc-admin-static-data:/app/staticfiles` |
| `web` | `nghcc-admin-static-data:/app/staticfiles` |
| `nginx` | `nghcc-admin-static-data:/var/www/nghcc-admin/static:ro` |

Nginx serves `/static/` directly from the read-only static mount. This does not depend on `DEBUG=True` and does not require Django to serve static assets.

## Media serving strategy

Production media uploads use the shared media named volume:

| Container | Mount |
| --- | --- |
| `web` | `nghcc-admin-media-data:/app/media` |
| `migrate` | `nghcc-admin-media-data:/app/media` |
| `nginx` | `nghcc-admin-media-data:/var/www/nghcc-admin/media:ro` |

The web container writes uploads to `/app/media`. Nginx serves `/media/` directly from the same volume mounted read-only. Django media serving remains limited to `DEBUG=True` through `urls.py`, so production media serving is handled by the reverse proxy.

## Nginx strategy

The Nginx example:

- Uses `alias /var/www/nghcc-admin/static/` for `/static/`.
- Uses `alias /var/www/nghcc-admin/media/` for `/media/`.
- Uses `try_files $uri =404` for static/media paths.
- Explicitly disables directory listing with `autoindex off`.
- Sets `client_max_body_size 20m`.
- Sends `X-Content-Type-Options: nosniff`.
- Proxies Django/Gunicorn traffic to `web:8000`.
- Passes `Host`, `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Host`, and `X-Forwarded-Proto`.
- Keeps HTTPS/TLS as a deployment-specific decision and does not assume a final domain or `.240`.

## Docker volume strategy

The production example uses named volumes:

| Volume | Purpose |
| --- | --- |
| `nghcc-admin-static-data` | Collected static files served read-only by Nginx. |
| `nghcc-admin-media-data` | Uploaded media written by web and served read-only by Nginx. |
| `nghcc-admin-mysql-data` | MySQL data storage. |

The DB still has no published host port in the production example. The only public HTTP entrypoint is Nginx.

## Validation results

Validation commands for this phase:

```powershell
docker compose config
docker compose build
docker compose --env-file .env.production.example -f docker-compose.production.example.yml config
.\scripts\run-csrf-tests.ps1
.\scripts\run-smoke-tests.ps1
```

Results:

- `docker compose config`: PASS; local compose rendered successfully.
- `docker compose -f docker-compose.production.example.yml --env-file .env.production.example config`: PASS; production example rendered successfully with Nginx static/media read-only mounts and no DB published port.
- `docker compose -f docker-compose.production.example.yml --env-file .env.production.example --profile release config`: PASS; release-profile `collectstatic` and `migrate` services rendered successfully.
- `docker compose build`: PASS; local web image built successfully.
- `.\scripts\run-csrf-tests.ps1`: PASS; 103 passed, 39 skipped.
- `.\scripts\run-smoke-tests.ps1`: PASS; 103 passed, 39 skipped.

The production example was config-validated only. It was not deployed, did not connect to `.240`, did not apply a real production env, did not run a production DB, and did not execute a production migration.

## Remaining production NO-GO blockers

Production remains **NO-GO**:

- `SECRET_KEY` production handling is not applied to a real production env.
- `ALLOWED_HOSTS` is not finalized.
- DB port exposure is fixed only in the production example; no production deployment validation has occurred.
- Auto migration on startup is split only in the production example; no production deployment validation has occurred.
- Production env has not been applied.
- No `.240` validation has been performed.
- HTTPS/TLS and secure-cookie policy still require final approval.
- Backup, restore, and rollback drill evidence is still required before production migration or deployment.
