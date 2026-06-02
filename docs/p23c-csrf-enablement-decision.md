# P23C CSRF Enablement Decision

## 1. Current Evidence

| Evidence | Result |
| --- | --- |
| Branch | `csrf-local-verification` |
| Current commit | `d4c466817e6e8f6fb2747e561b90669f254b73c5` |
| P23A CSRF wrapper | 93 passed, 0 failed, 39 skipped |
| P23A smoke wrapper | 88 passed, 0 failed, 44 skipped |
| P23B pre-remediation CKEditor finding | `/ckeditor/upload/` accepted staff upload without CSRF token; 95 passed, 1 failed, 40 skipped |
| P23B CKEditor remediation | Added project-level `/ckeditor/upload/` route protected by `csrf_protect(staff_member_required(...))`; resolver check shows `csrf_exempt=False` |
| P23B humnos remediation | Added `getCSRFToken()` fallback for `cms26_csrftoken` then `csrftoken` |
| P23B logout verification | Added positive-path `/admin/logout/` POST with CSRF token test |
| P23B credentialed page verification | Added force-login coverage for admin, users, hymns, and humnos pages |
| P23B humnos positive-path verification | Added mocked `yt_dlp` `/api/humnos/info/` POST with CSRF token |
| P23B final CSRF wrapper | 99 passed, 0 failed, 39 skipped |
| P23B final smoke wrapper | 90 passed, 0 failed, 48 skipped |
| Production env changed | No |
| Production DB changed | No |
| `.240` access / deploy / PR / merge | No |
| API permission mode | `API_PERMISSION_MODE=enforce` was not enabled |

## 2. CSRF Readiness Decision

| Target | Decision | Rationale |
| --- | --- | --- |
| Local | GO | CSRF wiring has passed wrapper coverage after remediation. Local default enablement is appropriate if rollback remains available and local users know Eureka delete is a separate blocker. |
| Staging | GO | Staging/default-like enablement is appropriate after the same image/config path is rebuilt with the P23B changes and the CSRF wrapper plus smoke wrapper pass in that environment. |
| Production | NO-GO for immediate enablement | CSRF wiring is ready enough technically, but production enablement should not proceed while Eureka delete remains GET-destructive and other production blockers remain open. |

Answers:

- CSRF wiring is sufficient to enter local default enablement.
- `ENABLE_CSRF_PROTECTION=True` is recommended as the local/staging default after a controlled default-change phase.
- `ENABLE_CSRF_PROTECTION=True` is not recommended for immediate production enablement until production blockers are cleared.

## 3. Remaining Production Blockers

| Blocker | Status | Impact |
| --- | --- | --- |
| Eureka GET delete method safety | Open | CSRF does not protect GET-based destructive actions. This remains the nearest security blocker before production CSRF enablement. |
| Static/media serving when `DEBUG=False` | Open | Production static, media, admin assets, CKEditor uploads, hymn resources, and eureka media must be served by a production-safe layer. |
| `SECRET_KEY` handling | Open | Production must use a unique high-entropy `DJANGO_SECRET_KEY`, not fallback or placeholder values. |
| `ALLOWED_HOSTS` finalization | Open | Production must restrict hosts to approved IP/domain values. |
| DB port exposure | Open | MySQL must not be exposed beyond the required network boundary. |
| Auto migration on startup | Open | Production web startup must not mutate the DB with automatic `migrate`. |
| Secure cookie / HTTPS policy | Open | Production cookie settings must align with the final transport model. |
| API/menu authorization governance | Deferred | Not a CSRF blocker, but still relevant to production readiness. |

## 4. Required Next Actions

### Before changing default

1. Create a local/staging default-change phase that flips the non-production default to `ENABLE_CSRF_PROTECTION=True`.
2. Keep an explicit rollback path to `ENABLE_CSRF_PROTECTION=False` during the default-change phase.
3. Rebuild the local/staging image after the default change.
4. Run `.\scripts\run-csrf-tests.ps1`.
5. Run `.\scripts\run-smoke-tests.ps1`.
6. Confirm `/ckeditor/upload/` still resolves to `csrf_exempt=False`.

### Before production enablement

1. Fix Eureka delete method safety so delete is POST-only and CSRF-protected.
2. Verify production static/media serving with `DEBUG=False`.
3. Set and verify production `DJANGO_SECRET_KEY`.
4. Finalize production `DJANGO_ALLOWED_HOSTS`.
5. Close or firewall DB port exposure.
6. Remove automatic migration from production web startup, or move migrations to an explicit controlled runbook.
7. Confirm secure cookie and HTTPS policy.
8. Run production-like CSRF and smoke validation without touching production DB unexpectedly.

### Deferred

| Item | Reason |
| --- | --- |
| API scope apply/enforce | Separate governance and assignment phase; do not couple to CSRF default change. |
| P22 menu/view permission policy | Important authorization policy work, but not required before local/staging CSRF default change. |
| Naming migration | Separate data/schema risk. |
| pytest-xdist / parallel testing | Still requires DB/media isolation review. |

## 5. Go / No-Go

| Question | Decision | Reason |
| --- | --- | --- |
| GO for local/staging CSRF default enablement? | GO | P23B closed CKEditor, humnos, logout, and credentialed page coverage gaps; final CSRF wrapper passed 99/0/39 and smoke wrapper passed 90/0/48. |
| GO for production CSRF enablement? | NO-GO | Eureka GET delete remains destructive and unprotected by CSRF. Production infrastructure blockers also remain. |
| GO for production deploy? | NO-GO | Production blockers remain across method safety, static/media serving, secret handling, host policy, DB exposure, and startup migration. |

## 6. Recommended Next Phase

Selected phase: **P23D Local/Staging CSRF Default Change**

Why this phase:

- CSRF wiring is now locally remediated and tested.
- The next smallest controlled move is to make CSRF the local/staging default, then prove wrappers still pass without one-off override assumptions.
- This keeps production untouched while converting CSRF from test-only mode to the non-production baseline.

Why not the other options:

| Option | Reason not selected now |
| --- | --- |
| P23E Eureka Delete Method Safety Fix | This is the next production blocker, but first the CSRF default should be proven in local/staging so the delete fix can be tested against the intended default security mode. |
| Production Static/Media Runbook | Important for production readiness, but it does not validate the CSRF default-change path that P23A/P23B just prepared. |
| P22 Menu/View Permission Policy Review | Important authorization governance, but separate from CSRF enablement and not the shortest continuation of P23. |
