# P25 Staging-like Readiness Drill Report

Scope: local production-like Docker Compose drill only.

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

## Drill environment

| Item | Value |
| --- | --- |
| Date | 2026-06-02 |
| Host | Local Windows/Docker Desktop environment |
| Production-like compose | `docker-compose.production.example.yml` |
| Public test URL | `http://localhost:26001` |
| Drill env | Temporary ignored `.env.production` / `.env.p25-drill`, removed after validation |
| CSRF | `ENABLE_CSRF_PROTECTION=True` |
| API permission mode | `API_PERMISSION_MODE=off` |
| Cookie mode | Local HTTP drill with `SESSION_COOKIE_SECURE=False` and `CSRF_COOKIE_SECURE=False` |

The existing local compose stack used the same fixed container names as the
production example. It was stopped with `docker compose down` before the drill
and restored with `docker compose up -d` after the drill. Volumes were not
removed.

## Commands and results

| Check | Result |
| --- | --- |
| Local stack pre-check | Existing local `nghcc-admin-web` and `nghcc-admin-db` were running. |
| `docker compose down` | PASS; local containers removed, volumes preserved. |
| `docker compose -f docker-compose.production.example.yml --profile release run --rm collectstatic` | PASS; `1412 static files copied to '/app/staticfiles'`. |
| `docker compose -f docker-compose.production.example.yml --profile release run --rm migrate` | PASS; `No migrations to apply`. |
| `docker compose -f docker-compose.production.example.yml up -d --build` | PASS; DB, web, and Nginx started. |
| `docker compose -f docker-compose.production.example.yml ps` | PASS; DB healthy, web healthy, Nginx healthy; only Nginx published `26001`. |
| `GET /api/health/` through Nginx | PASS; `200 application/json`, body included `"database": "ok"`. |
| `GET /admin/login/` through Nginx | PASS; `200 text/html`. |
| `GET /static/admin/css/base.css` through Nginx | PASS; `200 text/css`. |
| `POST /admin/login/` without CSRF token | PASS; `403 text/html`, confirming CSRF middleware is active. |
| Media probe through Nginx | PASS; temporary `/media/p25-media-probe.txt` returned `200 text/plain` and expected content. |
| `GET /media/` directory probe | PASS; `404 text/html`, no directory listing exposed. |
| Bad Host header probe | PASS; `400`, confirming host policy rejection for `bad.example`. |
| Cookie/header probe | PASS for local HTTP drill; CSRF cookie issued with `SameSite=Lax`, no `Secure` flag under the approved local HTTP drill env. |
| Representative page `/` | PASS; `200 text/html`. |
| Representative page `/hymns/` | PASS; `302 text/html` login redirect. |
| Representative page `/webav/` | PASS; `302 text/html` login redirect. |
| Representative page `/eureka/` | PASS; `302 text/html` login redirect. |
| API `/api/hymns/` unauthenticated | PASS; `403 application/json`. |
| API `/api/humnos/info/` POST unauthenticated/no CSRF | PASS; `403 application/json`. |
| `GET /ckeditor/upload/` unauthenticated | PASS; `302 text/html` login redirect. |
| Probe cleanup | PASS; media probe removed and returned `404`. |
| Production-like stack shutdown | PASS; `docker compose -f docker-compose.production.example.yml down`, volumes preserved. |
| Local stack restore | PASS; `docker compose up -d`, DB healthy and web running. |

## Deployment runbook assumptions checked

| Assumption | Result |
| --- | --- |
| Web startup does not run migration in production example | PASS; web command was `gunicorn nads26.wsgi:application --bind 0.0.0.0:8000`. |
| Migration is a separate release-profile command | PASS; `migrate` ran as a one-off release service. |
| Static collection is a separate release-profile command | PASS; `collectstatic` ran as a one-off release service. |
| Static files are served by Nginx from a shared volume | PASS; admin CSS returned `200 text/css`. |
| Media files are served by Nginx from a shared volume | PASS; media probe returned `200 text/plain`. |
| DB is internal-only in production example | PASS; production-like `ps` showed DB exposed only on container ports, with no host-published DB port. |
| Nginx is the only public HTTP entrypoint | PASS; production-like `ps` showed only Nginx publishing `26001`. |
| CSRF is enabled in the production-like stack | PASS; missing-token POST returned `403`. |
| Host policy is active | PASS; bad host returned `400`. |

## Findings

1. **GO: production compose example can be brought up locally.**
   The production-like stack built and ran locally with DB, web, and Nginx
   healthy.

2. **GO: Nginx static/media flow works in the local drill.**
   Static files and a temporary media probe were served by Nginx. Directory
   listing was not exposed.

3. **GO: CSRF-enabled production-like stack works for negative-path checks.**
   Missing-token POSTs returned `403`. Full authenticated positive-path browser
   flows remain a production/staging-like credentialed verification item.

4. **GO: runbook separation assumptions are valid locally.**
   Migration and collectstatic ran as release-profile one-off services, while
   web startup ran Gunicorn only.

5. **Finding: existing named media volume warning.**
   Docker Compose warned that `nghcc-admin-media-data` already existed but was
   not created by this compose project. This matched the local environment and
   did not block the drill. Production should explicitly decide whether the
   media volume is pre-created/external or created by the production compose
   project.

6. **Finding: CKEditor upstream support warning.**
   The migration system check repeated the known `django-ckeditor` warning that
   CKEditor 4.22.1 is no longer supported. This did not block the drill, but it
   remains a security maintenance item.

7. **Finding: local Docker direct commands had access limitations.**
   Direct `docker ps` / `docker volume ls` attempts failed with access to
   `C:\Users\peter\.docker\config.json` denied, while `docker compose` commands
   used for the drill succeeded. This did not block the drill.

## Remaining production NO-GO blockers

Production remains **NO-GO** until:

- A real production `.env.production` exists outside Git and passes P24C policy.
- Final production host/domain is approved.
- Final `CSRF_TRUSTED_ORIGINS` is approved.
- HTTPS/TLS and secure-cookie decision is approved.
- Production backup destination and retention policy are approved.
- DB backup, media backup, compose/env snapshot, and checksums are executed for
  the approved production target.
- Restore drill is performed and recorded using production backup artifacts.
- Production static/media serving is verified through the final public URL.
- Authenticated smoke and CSRF positive-path checks are performed with approved
  production or staging-like credentials.
- Any production migration receives explicit approval.

## GO / NO-GO

| Question | Decision | Reason |
| --- | --- | --- |
| GO for P25 local staging-like readiness drill? | GO | Production-like stack, Nginx static/media, CSRF negative path, smoke probes, and runbook assumptions passed locally. |
| GO for production deploy planning? | NO-GO | Final production env, host/origin/TLS, production backup/restore evidence, and authenticated final-URL smoke remain open. |
| GO for production deploy? | NO-GO | P25 performed local validation only and does not approve production action. |
| GO for `.240` access? | NO-GO | No `.240` access was requested or performed. |
| GO for production DB change or migration? | NO-GO | No production DB action is approved. |
| GO for `API_PERMISSION_MODE=enforce`? | NO-GO | Enforcement remains a separate approval path. |
