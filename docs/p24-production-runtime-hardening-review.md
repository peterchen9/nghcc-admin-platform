# P24 Production Runtime Hardening Review

Scope: review only. No production deploy, no `.240` connection, no production environment change, no production DB change, no migration execution, no API scope apply, no `API_PERMISSION_MODE=enforce`, no merge, and no PR.

Evidence reviewed:

- `docker-compose.yml`
- `docker-compose.volume.yml`
- `backend/Dockerfile`
- `backend/nads26/settings.py`
- `backend/nads26/urls.py`
- `.env.example`
- `.env.production.example`
- `frontend/nginx.conf`
- `docs/deployment.md`
- `docs/backup-plan.md`
- `docs/backup-and-restore.md`
- P23A-P23E review reports

Production status after this review: **NO-GO** until the gates in section 5 are closed.

## 1. Runtime Blocker Matrix

| Item | Current state | Production risk | Required decision | Recommended fix | Verification method |
| --- | --- | --- | --- | --- | --- |
| Static serving when `DEBUG=False` | `STATIC_ROOT` is `/app/staticfiles`; `Dockerfile` runs `collectstatic` before gunicorn. No production compose reverse proxy serves `/static/`. Django does not serve static files in production by default. | Admin CSS/JS and app assets may return 404 when `DEBUG=False`; production UI can be partially unusable. | Decide whether static files are served by Nginx, CDN, or a Django static middleware. | Use Nginx as the production static server with a read-only mount of collected static files from `STATIC_ROOT`; keep Django behind the proxy. | Build image, run `collectstatic` separately, start production-like stack with `DJANGO_DEBUG=0`, then verify `GET /static/admin/css/base.css` and app CSS/JS return 200 with correct content type. |
| Media serving when `DEBUG=False` | `MEDIA_ROOT` is `/app/media`; `urls.py` only appends `static(settings.MEDIA_URL, ...)` when `settings.DEBUG` is true. Compose bind-mounts `./uploads:/app/media`; `docker-compose.volume.yml` can override to an external named volume. | Uploaded files and CKEditor media will not be served by Django when `DEBUG=False`; content pages may break or expose inconsistent media paths. | Decide the canonical production media storage and serving path. | Serve `/media/` through Nginx from a persistent named volume mounted read-only in the proxy and read-write in the web container. Avoid Windows bind mounts for production restore fidelity. | Upload or restore a known media file in a staging-like stack, set `DJANGO_DEBUG=0`, verify `GET /media/<known-file>` returns 200 and no directory listing is exposed. |
| `SECRET_KEY` production handling | `settings.py` falls back to `SESSION_SECRET`, then `local-dev-only-secret`. `.env.production.example` includes `DJANGO_SECRET_KEY`, but fallback remains available. | If production starts with a default or weak secret, sessions, password reset tokens, and signed data are compromised; secret rotation may invalidate sessions unexpectedly. | Decide that production must fail readiness if `DJANGO_SECRET_KEY` is missing or known-placeholder. | Require explicit `DJANGO_SECRET_KEY` in production env; add a preflight/readiness check or deploy runbook step that blocks placeholders and fallback values. | Run `python manage.py check --deploy` plus a custom env audit in staging-like mode; confirm missing/placeholder `DJANGO_SECRET_KEY` blocks the production gate. |
| `ALLOWED_HOSTS` finalization | Default is `localhost,127.0.0.1`; `.env.production.example` lists `192.168.16.240,localhost`. Final public host/domain is not fixed in code or docs. | Invalid hosts produce 400s; over-broad hosts weaken host header protections; localhost in production can mask incomplete host policy. | Decide final production hostname(s), whether raw IP access is supported, and whether localhost remains only for internal smoke tests. | Set `DJANGO_ALLOWED_HOSTS` explicitly to the final domain/IP list. Avoid wildcard hosts. Document which host smoke tests must use. | Production-like `curl -H "Host: <allowed>" /api/health/` returns 200; unknown host returns 400. |
| `CSRF_TRUSTED_ORIGINS` | Parsed from env; `.env.production.example` currently uses `http://192.168.16.240:26001`. P23D kept production CSRF disabled in the production example. | Missing or wrong scheme/host breaks credentialed POSTs after CSRF enablement; HTTP origin may be inappropriate once HTTPS exists. | Decide final scheme, host, and port for browser access before enabling CSRF in production. | Set exact HTTPS origin(s) when TLS is available. For temporary HTTP-only internal production, document the risk and use exact HTTP origin only for the approved host. | With `ENABLE_CSRF_PROTECTION=True`, verify login/logout/upload/write flows from the final origin; verify cross-origin POSTs are rejected. |
| `SESSION_COOKIE_SECURE` / `CSRF_COOKIE_SECURE` | Defaults are false. Production example sets both false for current HTTP `.240` usage and comments that HTTPS should set them true. | Secure cookies cannot be used over HTTP; leaving them false under HTTPS exposes cookies over accidental cleartext paths. Setting them true before HTTPS breaks auth over HTTP. | Decide whether production launch is HTTP-only internal or HTTPS behind reverse proxy. | For production approval, prefer HTTPS reverse proxy and set both to true. If a temporary HTTP-only phase is approved, record it as a time-limited exception with compensating network controls. | Browser login smoke test over final URL; inspect `Set-Cookie` headers for `Secure`, `HttpOnly`, and expected `SameSite`; confirm HTTP-to-HTTPS redirect if TLS is enabled. |
| DB port exposure | `docker-compose.yml` publishes MySQL as `${DB_EXTERNAL_PORT:-26003}:3306`. Web uses internal `DB_HOST=db`. | MySQL is reachable outside the Docker network, increasing brute-force, credential leakage, and accidental data modification risk. | Decide whether any host-level DB access is required in production. | Remove published DB port in production compose. Use `docker compose exec db`, SSH tunnel, or a one-off maintenance profile for controlled access. | From host/network, DB port is closed; from web container, `mysqladmin ping -h db` works; backup scripts use container/internal access. |
| Auto migration on startup | `backend/Dockerfile` CMD runs `python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn ...`. | Every container start can mutate production schema before backup/rollback checks; failed migrations can prevent app boot and make rollback ambiguous. | Decide migration ownership: automatic on boot vs explicit release step. | Split migrations into an explicit one-off command/runbook step after backup and before app rollout. Web startup should only start gunicorn after static assets are prepared. | Restart web container without pending migrations and confirm no migration command runs; execute migration command only in staging-like drill with backup and rollback evidence. |
| `collectstatic` behavior | `collectstatic` runs on every web startup into image/container path `/app/staticfiles`. No shared static volume or proxy mount is defined. | Startup can be slower and less deterministic; Nginx cannot serve collected files unless the path is shared; assets may disappear on container replacement if not image-baked or volume-backed. | Decide whether static files are collected at image build, release step, or entrypoint. | Prefer release/build-time or one-off `collectstatic` into a named/static volume mounted read-only by Nginx. Do not couple it to gunicorn boot. | `findstatic` and HTTP static probes pass after deployment; a web restart does not need to recollect assets for serving to continue. |
| Reverse proxy / Nginx requirement | `frontend/nginx.conf` exists but proxies `/static/` and `/media/` back to `backend:8000`; it is not wired into `docker-compose.yml`, and service name `backend` does not match current web service name `web`. | There is no active production reverse proxy for static/media, TLS, headers, or request buffering. Existing Nginx config would not work as-is with current compose names and still would not directly serve files. | Decide whether production requires Nginx in the stack or an external proxy. | Add a production Nginx service/config in a later phase. It should proxy dynamic requests to `web:8000`, serve static/media directly from mounted paths, set forwarding headers, and terminate or sit behind TLS. | Production-like compose includes Nginx; only proxy port is published; `/`, `/api/health/`, `/static/...`, and `/media/...` pass through the final public URL. |
| Backup / rollback requirement | Docs and scripts exist for DB and uploads backup/restore. Backup docs reference `.240` legacy paths and named volume restore concerns. No production gate ties backup completion to migration/startup rollout. | Schema or media changes without verified backup/restore can cause unrecoverable downtime or data loss. | Decide minimum backup, checksum, restore, and rollback evidence required before production change. | Require pre-change DB dump, media archive, compose/env snapshot, checksum verification, restore drill, and rollback command plan before production migration or hardening rollout. | Gate requires backup artifacts, checksums, restore test result, and rollback drill result recorded in a runbook before production release. |

## 2. Recommended Production Architecture

Recommended architecture, not implemented in this phase:

| Component | Recommendation |
| --- | --- |
| web container | Run only Django/gunicorn. Do not run automatic migrations on normal startup. Use explicit release commands for migration and static collection. |
| db container | Keep MySQL on the internal Docker network only. Do not publish MySQL to host/network by default. Use named volume storage and controlled maintenance access. |
| static files | Collect into a deterministic static artifact or named volume. Serve `/static/` directly from Nginx, read-only. |
| media files | Store uploads in a persistent named volume mounted read-write by web and read-only by Nginx. Back up this volume before releases. |
| reverse proxy | Add Nginx or use an equivalent external proxy as the only public entrypoint. It should serve static/media, proxy dynamic traffic, pass `X-Forwarded-*` headers, and support TLS. |
| network exposure | Publish only the reverse proxy port. Keep web and db on private Docker networks. Do not expose DB. Optionally keep web un-published and reachable only by proxy. |
| backup/restore | Before production runtime changes, capture DB dump, media archive, compose/env snapshot, and checksums. Verify restore in a staging-like environment. |
| rollback | Rollback must define app image/config rollback, DB rollback or forward-fix policy, media restore path, and a smoke-test sequence after rollback. |

## 3. Environment Variable Policy

Production env must be explicit. Defaults can remain for local development, but production should not rely on them.

| Env var | Production policy | Default use allowed in production? | Notes |
| --- | --- | --- | --- |
| `DJANGO_SECRET_KEY` | Required; must be unique, high entropy, and secret-managed. | Must not use default. | Missing value must block production readiness. |
| `DJANGO_DEBUG` | Required; must be `0` or `False`. | Must not use default. | `DEBUG=True` is a production blocker. |
| `DJANGO_ALLOWED_HOSTS` | Required; exact final host/domain list. | Must not use default. | Avoid wildcard; decide whether IP and localhost are allowed. |
| `CSRF_TRUSTED_ORIGINS` | Required when CSRF is enabled and browser origin is not same host/scheme. | Must not use default for production CSRF enablement. | Must include scheme, host, and port when needed. |
| `ENABLE_CSRF_PROTECTION` | Required; production target should be `True` after static/media/runtime gates close. | Must not use default. | Current production remains NO-GO while disabled. |
| `SESSION_COOKIE_SECURE` | Required; should be `True` with HTTPS. | Must not use default. | `False` requires explicit HTTP-only exception. |
| `CSRF_COOKIE_SECURE` | Required; should be `True` with HTTPS. | Must not use default. | `False` requires explicit HTTP-only exception. |
| `DB_HOST` | Required; should be internal service name such as `db`. | Must not use default. | Production should not point to exposed public DB endpoint. |
| `DB_PORT` | Required; usually `3306` internally. | Must not use default. | External published DB port should not be needed. |
| `DB_NAME` | Required. | Must not use default. | Must match DB initialization and backup/restore scripts. |
| `DB_USER` | Required. | Must not use default. | Use least-privilege app DB user. |
| `DB_PASSWORD` | Required; secret-managed. | Must not use default. | Placeholder values are blockers. |
| `API_PERMISSION_MODE` | Required; keep `off` or `report_only` until API permission enforcement gates are separately approved. | Must not use default. | Must not be set to `enforce` in this phase. |

## 4. Docker / Compose Hardening Plan

This is a plan only; no Docker or Compose changes are made in P24.

| Question | Review finding | Plan |
| --- | --- | --- |
| Should DB published port be removed? | Yes for production. Current compose publishes `${DB_EXTERNAL_PORT:-26003}:3306`. | Create a production compose override that removes DB port publishing and uses internal Docker networking. Provide a separate maintenance profile or SSH tunnel procedure if direct DB access is required. |
| Should migrate command be split? | Yes. Current Docker CMD runs migrations on every web startup. | Replace production web startup with gunicorn-only command in a later phase. Add explicit `docker compose run --rm web python manage.py migrate --noinput` release step after backup and before rollout. |
| Should Nginx be added? | Yes, unless an external reverse proxy is already guaranteed. Current `frontend/nginx.conf` is not wired and references `backend`, not `web`. | Add a production Nginx service/config that is the only published HTTP(S) entrypoint, proxies dynamic traffic to `web:8000`, and serves static/media directly. |
| Should media use named volume? | Yes. Current base compose uses `./uploads:/app/media`; volume override exists for external `nghcc-admin-media-data`. | Use a named media volume in production for predictable Linux filesystem behavior and backup/restore fidelity. Mount read-write to web and read-only to Nginx. |
| Should healthcheck be added? | DB has a healthcheck; web has none. | Add web healthcheck against `/api/health/` after static/media/proxy plan is finalized. Consider Nginx healthcheck for public entrypoint. |
| Should backup volume strategy be added? | Yes. Backup scripts/docs exist, but not yet tied to production release gates. | Define named volumes for DB and media, pre-release backup commands, checksum verification, restore drill, and rollback evidence as required release artifacts. |

## 5. Production Gate Checklist

### Gate A: env readiness

PASS conditions:

- `DJANGO_SECRET_KEY` is explicit, high entropy, and not a placeholder.
- `DJANGO_DEBUG=0` or `False`.
- `DJANGO_ALLOWED_HOSTS` contains only approved production host(s).
- `CSRF_TRUSTED_ORIGINS` matches final scheme/host/port.
- `ENABLE_CSRF_PROTECTION=True` for production approval.
- `SESSION_COOKIE_SECURE=True` and `CSRF_COOKIE_SECURE=True` when HTTPS is enabled, or an approved temporary HTTP exception exists.
- `API_PERMISSION_MODE` is explicitly set and is not `enforce`.

BLOCK conditions:

- Any required production env var is missing or relies on a local default.
- Any secret or DB password is a placeholder.
- `DJANGO_DEBUG=True`.
- Hosts or origins are wildcard/over-broad.
- `API_PERMISSION_MODE=enforce`.

### Gate B: static/media readiness

PASS conditions:

- Static files are collected deterministically.
- `/static/` is served under `DEBUG=False` by the approved proxy/static strategy.
- `/media/` is served under `DEBUG=False` by the approved proxy/media strategy.
- Media storage is persistent and included in backup/restore.
- CKEditor upload and media retrieval both pass in a staging-like environment.

BLOCK conditions:

- Admin/app static assets 404 under `DEBUG=False`.
- Uploaded media 404s under `DEBUG=False`.
- Nginx/proxy is absent, unwired, or points to the wrong service.
- Media is stored only in an unverified bind mount for production.

### Gate C: DB/network readiness

PASS conditions:

- DB is reachable from web over the internal Docker network.
- DB is not published to host/network by default.
- Only the reverse proxy public port is exposed.
- DB credentials are explicit and non-placeholder.
- DB backup scripts work without requiring public DB exposure.

BLOCK conditions:

- MySQL is reachable directly from the network through a published port.
- Web cannot reach DB internally.
- Backup/maintenance access depends on leaving DB public.

### Gate D: migration/rollback readiness

PASS conditions:

- Web startup does not automatically run production migrations.
- Migration is an explicit release step with pre-change backup evidence.
- DB dump, media archive, compose/env snapshot, and checksums are captured before changes.
- Restore drill and rollback plan are documented and tested in a staging-like environment.

BLOCK conditions:

- Migrations still run on every container startup.
- No current backup/checksum exists before production change.
- Restore or rollback procedure is untested.
- Migration failure would leave no clear rollback path.

### Gate E: smoke verification readiness

PASS conditions:

- Production-like smoke suite covers `/api/health/`, login, logout, admin, credentialed workflows, static assets, media retrieval, CKEditor upload, humnos, hymns, and Eureka delete POST-only behavior.
- Smoke tests use the final public URL through the reverse proxy.
- Cookie security and CSRF behavior are inspected under the final scheme.

BLOCK conditions:

- Smoke tests only hit Django directly and bypass the proxy.
- Static/media checks are absent.
- CSRF or cookie checks are absent under the final origin.
- Eureka destructive action is not verified as POST-only.

## 6. Recommended Next Phase

Recommended next phase: **P24A Docker/Compose Production Hardening**.

Reason: the largest remaining runtime risks are structural. The production stack needs a clear compose architecture before the static/media implementation, env template, and migration runbook can be finalized without rework. P24A should define the production-only topology: reverse proxy service, internal-only DB, no auto migration in web startup, named media/static volume strategy, and healthchecks.

Why not the other options first:

- **P24B Static/Media Serving Implementation** should follow P24A because static/media paths depend on the chosen reverse proxy and volume topology.
- **P24C Production Env Template Finalization** should follow P24A because env names and required values depend on the final compose/proxy/TLS decisions.
- **P24D Migration/Backup/Rollback Runbook** should follow P24A because the runbook must reference the final migration command split, volume names, and network model.

Next phase status: **GO for P24A planning/implementation in a non-production branch**, but **NO-GO for production deployment**.
