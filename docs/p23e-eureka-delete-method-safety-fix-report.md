# P23E Eureka Delete Method Safety Fix Report

## Problem

Eureka member deletion was reachable through a GET link at `/eureka/modify/delete/<church_id>/`.

That made a destructive action available through a safe HTTP method. CSRF protection does not make destructive GET safe, because browsers, crawlers, previews, or user clicks can still trigger GET requests without an intentional form submission.

## Root Cause

`delete_view` was protected by `login_required`, but it did not restrict the HTTP method. The `modify.html` template rendered deletion as an `<a href="...">` link with a client-side confirm dialog.

The confirm dialog improved UX, but it was not a server-side safety control.

## Code Changes

| File | Change |
| --- | --- |
| `backend/modules/eureka/views.py` | Added `require_POST` to `delete_view`, so GET now returns method-not-allowed and cannot delete. |
| `backend/templates/eureka/modify.html` | Replaced the delete anchor with a POST form, `{% csrf_token %}`, and a submit button that preserves the delete action UX. |

No DB schema changes were made.

## Test Changes

Added `tests/security/test_eureka_delete_method_safety.py` with coverage for:

- Anonymous POST cannot delete.
- Authenticated GET delete returns non-destructive method-not-allowed behavior.
- Authenticated POST without CSRF is rejected when CSRF checks are enforced.
- Authorized authenticated POST with a valid CSRF token deletes the target member.

The tests create a temporary local `Member` record and clean it up after each case.

## Test Results

| Command | Result |
| --- | --- |
| `docker compose -f docker-compose.yml -f docker-compose.volume.yml build web` | PASS |
| `.\scripts\run-csrf-tests.ps1` | 103 passed, 0 failed, 39 skipped |
| `.\scripts\run-smoke-tests.ps1` | 103 passed, 0 failed, 39 skipped |

Note: the first CSRF wrapper run before rebuilding the local web image failed because the container still had the old GET-delete code. After rebuilding `web`, the same suite passed.

## Remaining Blockers

Production remains NO-GO because the following items are still incomplete:

- Static/media serving when `DEBUG=False`.
- `SECRET_KEY` production handling.
- `ALLOWED_HOSTS` finalization.
- DB port exposure.
- Auto migration on startup.

## Production Readiness Impact

P23E removes the Eureka GET destructive-action blocker.

Local/staging CSRF default enablement remains GO. Production CSRF enablement is closer, but production deployment remains NO-GO until the remaining production environment and runtime blockers are closed.
