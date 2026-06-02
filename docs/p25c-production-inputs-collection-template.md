# P25C Production Inputs Collection Template

Scope: documentation-only template for collecting production inputs before P26
deploy planning.

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

## Instructions

Use this template to collect approvals, owners, paths, decisions, and evidence
locations before any P26 deploy planning.

Do not write secrets into this document. For secret values, record only owner,
storage location, last verified date, and whether the value passed policy.

Production deploy planning remains **NO-GO** until every required field is
completed, reviewed, and approved.

## 1. Approval Record

| Field | Required value |
| --- | --- |
| Collection date | `YYYY-MM-DD` |
| Requesting owner | TBD |
| Technical operator | TBD |
| Approval reference | TBD |
| Approved phase | P26 deploy planning inputs only |
| Allowed action scope | Inputs collection only unless separately approved |
| Explicit production deploy approval included? | NO |
| Explicit production DB modification approval included? | NO |
| Explicit production migration approval included? | NO |
| Explicit `.240` access approval included? | NO unless completed in section 2 |
| Explicit `API_PERMISSION_MODE=enforce` approval included? | NO |

## 2. `.240` Access Details

Access to `.240` is **NO-GO** until this section is explicitly completed and
approved.

| Field | Required value |
| --- | --- |
| Target host/IP | TBD |
| SSH/user identity | TBD |
| Approved access window | TBD |
| Access purpose | inspect only / backup / smoke / deploy / rollback / other |
| Allowed command scope | TBD |
| Approved target app path | TBD |
| Approved compose file path | TBD |
| Approved env file path | TBD |
| Write actions allowed? | NO unless explicitly approved |
| Service restart allowed? | NO unless explicitly approved |
| Backup command allowed? | NO unless explicitly approved |
| Migration command allowed? | NO unless explicitly approved |
| Restore command allowed? | NO unless explicitly approved |
| Production DB mutation allowed? | NO unless explicitly approved |
| Secret viewing allowed? | NO unless explicitly approved |
| Evidence capture location | TBD |

Prerequisites before any `.240` access:

- Current local git status is clean or exceptions are documented.
- Current commit hash is recorded.
- Access scope is narrower than or equal to the approved phase.
- No secrets will be pasted into chat or committed.
- No production DB write/migration/restore happens without separate approval.

## 3. Final Host, Domain, Origin, and TLS Decisions

| Decision | Required value |
| --- | --- |
| Final public URL | TBD |
| Raw IP browser access allowed? | yes/no; if yes, list IP and reason |
| Final `DJANGO_ALLOWED_HOSTS` | TBD |
| Final `CSRF_TRUSTED_ORIGINS` | TBD |
| HTTP-only temporary exception? | yes/no |
| HTTPS/TLS owner | TBD |
| TLS certificate source/path | TBD |
| TLS termination point | Nginx container / external proxy / other |
| Public port(s) | TBD |
| Internal-only ports | TBD |
| `SESSION_COOKIE_SECURE` decision | True for HTTPS; exception required for False |
| `CSRF_COOKIE_SECURE` decision | True for HTTPS; exception required for False |
| Cookie header verification owner | TBD |
| Bad-host rejection verification owner | TBD |

GO criteria:

- Hosts contain no wildcard values.
- Origins include exact scheme, host, and non-standard port where needed.
- HTTPS is approved, or HTTP-only exception is explicit and time-limited.
- Cookie settings match the final browser URL.

## 4. Production Env Values Needed

Do not record secret values here. Record only the status, owner, and storage
location for secret-managed values.

| Variable | Required policy | Owner/location/status |
| --- | --- | --- |
| `APP_NAME` | Production app name is explicit. | TBD |
| `APP_ENV` | `production`. | TBD |
| `APP_PORT` | Approved public HTTP port or internal exception. | TBD |
| `APP_TLS_PORT` | Required if TLS terminates in this compose stack. | TBD |
| `COMPOSE_PROJECT_NAME` | Production-specific project name. | TBD |
| `DJANGO_SECRET_KEY` | Secret-managed, high entropy, not shared with local/staging. | owner/location only |
| `DJANGO_DEBUG` | `False`. | TBD |
| `DEBUG` | `False`. | TBD |
| `DJANGO_ALLOWED_HOSTS` | Exact approved hosts only. | TBD |
| `CSRF_TRUSTED_ORIGINS` | Exact approved origins only. | TBD |
| `ENABLE_CSRF_PROTECTION` | `True`. | TBD |
| `ENABLE_MENU_PERMISSION_ENFORCEMENT` | `False` unless separately approved. | TBD |
| `API_PERMISSION_MODE` | `off` unless separately approved. | TBD |
| `SESSION_COOKIE_SECURE` | Match TLS decision. | TBD |
| `CSRF_COOKIE_SECURE` | Match TLS decision. | TBD |
| `SESSION_COOKIE_HTTPONLY` | `True`. | TBD |
| `CSRF_COOKIE_HTTPONLY` | Project default unless separately changed. | TBD |
| `SECURE_CONTENT_TYPE_NOSNIFF` | `True`. | TBD |
| `X_FRAME_OPTIONS` | `SAMEORIGIN` unless separately approved. | TBD |
| `DB_ENGINE` | `django.db.backends.mysql`. | TBD |
| `DB_HOST` | Internal compose DB service, normally `db`. | TBD |
| `DB_PORT` | Internal DB port, normally `3306`. | TBD |
| `DB_NAME` | Explicit production DB name. | owner/location only if sensitive |
| `DB_USER` | Explicit production DB user. | owner/location only if sensitive |
| `DB_PASSWORD` | Secret-managed. | owner/location only |
| `DB_ROOT_PASSWORD` | Secret-managed. | owner/location only |
| `UPLOAD_DIR` | `/app/media` unless approved otherwise. | TBD |
| `UPLOAD_MAX_SIZE_MB` | Explicit production limit. | TBD |
| `UPLOAD_ALLOWED_EXTENSIONS` | Explicit production list. | TBD |
| `UPLOAD_STRICT_MIME_CHECK` | Decision recorded before deploy. | TBD |

Hard NO-GO values:

- Any `UNUSABLE_REPLACE_ME_*` value.
- Empty required values.
- `change_me`.
- `local-dev-only-secret`.
- Wildcard hosts.
- Unapproved HTTP origins.
- `API_PERMISSION_MODE=enforce` without separate security approval.
- Published MySQL host port without explicit production exception.

## 5. DB and Media Backup Evidence

| Evidence | Required field |
| --- | --- |
| Release ID | TBD |
| Backup owner | TBD |
| Backup storage root | TBD |
| Retention period | TBD |
| DB backup command approved? | yes/no |
| DB backup file path | TBD |
| DB backup file size | TBD |
| DB backup exit code | TBD |
| DB backup checksum | TBD |
| Media backup command approved? | yes/no |
| Media backup file path | TBD |
| Media backup file size | TBD |
| Media backup checksum | TBD |
| Compose snapshot path | TBD |
| Env snapshot path | TBD; secret-handled, outside Git |
| Rendered compose config path | TBD |
| `SHA256SUMS` path | TBD |
| `sha256sum -c` result | TBD |
| Evidence reviewer | TBD |
| Evidence review decision | GO / NO-GO |

Missing backup file, missing checksum, failed checksum verification, or missing
reviewer decision is **NO-GO**.

## 6. Restore Drill Evidence

| Evidence | Required field |
| --- | --- |
| Drill environment | TBD |
| Drill data source | Production backup artifacts / other |
| DB restore drill command approved? | yes/no |
| DB restore drill result | PASS / FAIL / not run |
| Media restore drill command approved? | yes/no |
| Media restore drill result | PASS / FAIL / not run |
| Media integrity check result | PASS / FAIL / not run |
| Application smoke after restore | PASS / FAIL / not run |
| Restore drill logs path | TBD |
| Drill reviewer | TBD |
| Drill review decision | GO / NO-GO |

Production migration approval is **NO-GO** until restore drill evidence is
complete and reviewed.

## 7. Rollback Owner, Commands, and Evidence

| Field | Required value |
| --- | --- |
| Rollback owner | TBD |
| Rollback decision window | TBD |
| Incident communication channel | TBD |
| Preferred rollback strategy | forward fix / compose rollback / DB restore / media restore |
| Previous app commit/image | TBD |
| Previous compose snapshot | TBD |
| Previous env snapshot | TBD |
| DB restore command approved? | yes/no |
| Media restore command approved? | yes/no |
| Rollback smoke checklist owner | TBD |
| Rollback success criteria | TBD |
| Rollback evidence location | TBD |

Rollback command templates must be reviewed against the actual production paths
before use. Do not run DB or media restore without explicit incident approval.

## 8. Final Authenticated Smoke Account Requirements

Do not record passwords or tokens here.

| Requirement | Required value |
| --- | --- |
| Smoke account owner | TBD |
| Staff account username or identifier | owner-held; do not record password |
| Account has `is_active=1`? | yes/no |
| Account has `is_staff=1`? | yes/no |
| Account permission scope | admin / users / hymns / humnos / eureka / pages |
| Password/token storage location | owner-held secret location only |
| MFA/session requirement | TBD |
| Smoke execution owner | TBD |
| Smoke execution window | TBD |
| Credential rollback/disable plan | TBD |

Required authenticated final-URL checks:

- Login GET issues CSRF cookie.
- Login POST succeeds with CSRF token.
- Admin loads for approved staff account.
- Logout POST succeeds with CSRF token.
- CKEditor upload positive path is CSRF-protected and staff-only.
- `/hymns/` or approved hymns workflow behaves as expected.
- `/webav/` humnos workflow behaves as expected.
- `/eureka/` workflow behaves as expected.
- Eureka delete GET is non-destructive; POST requires CSRF.
- Static and media assets load through final URL.
- Bad Host header is rejected.
- Cookie headers match TLS/HTTP decision.

## 9. P26 Entry Decision

P26 deploy planning is **NO-GO** unless every item below is GO:

| Gate | Decision |
| --- | --- |
| `.240` access details approved and scoped | GO / NO-GO |
| Final host/domain/origin/TLS decisions approved | GO / NO-GO |
| Production env values collected without secrets in Git/chat | GO / NO-GO |
| Backup evidence requirements satisfied | GO / NO-GO |
| Restore drill evidence satisfied | GO / NO-GO |
| Rollback owner/commands/evidence approved | GO / NO-GO |
| Final authenticated smoke account requirements satisfied | GO / NO-GO |
| Production migration remains one-off and explicitly approved | GO / NO-GO |
| `API_PERMISSION_MODE=enforce` remains off unless separately approved | GO / NO-GO |

Final P25C decision: **NO-GO for P26 deploy planning until this template is
completed and reviewed.**

## 10. P25C Validation Results

Validation performed:

- Read back `AGENTS.md`.
- Reviewed P25B final-gate checklist.
- Reviewed P24D production migration, backup, restore, and rollback runbook.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml config`: PASS; production compose example rendered without starting containers.
- `docker compose --env-file .env.production.example -f docker-compose.production.example.yml --profile release config`: PASS; release-profile `migrate` and `collectstatic` services rendered without starting containers.
- Added this docs-only template.

No runtime tests were run because P25C is docs-only and does not change
application behavior, compose behavior, settings, or scripts.
