# P23B CSRF Enablement Remediation Report

## Scope

P23B stayed on branch `csrf-local-verification`.

Guardrails preserved:

- No merge.
- No PR.
- No deploy.
- No `.240` connection.
- No production env change.
- No production DB change.
- No API scope apply.
- No `API_PERMISSION_MODE=enforce`.

## Fixes

| Area | Change | Risk |
| --- | --- | --- |
| humnos token robustness | Added `getCSRFToken()` in `humnos_page.html`, matching the users/hymns strategy by accepting `cms26_csrftoken` first and `csrftoken` second. | Small |
| logout verification | Added CSRF positive-path test for `/admin/logout/`. | Small |
| CKEditor upload verification | Added a project-level `/ckeditor/upload/` route wrapped with `csrf_protect(staff_member_required(...))`, before the third-party include. Added tests proving missing token is rejected and valid token upload reaches the uploader. Upload test uses temporary `MEDIA_ROOT`. | Medium |

## Verification Results

Initial CSRF wrapper run found a CKEditor issue:

| Command | Result |
| --- | --- |
| `.\scripts\run-csrf-tests.ps1` before CKEditor URL remediation | 95 passed, 1 failed, 40 skipped |

The failed assertion showed `/ckeditor/upload/` accepted a staff upload without a CSRF token. This was remediated by adding an explicit project URL route that applies `csrf_protect`.

| Command | Result |
| --- | --- |
| resolver sanity check for `/ckeditor/upload/` | `nads26.urls.ckeditor_upload`, `csrf_exempt=False` |
| `.\scripts\run-csrf-tests.ps1` after remediation | 99 passed, 0 failed, 39 skipped |
| `.\scripts\run-smoke-tests.ps1` after remediation | 90 passed, 0 failed, 48 skipped |

## Functional Impact

| Flow | Status | Notes |
| --- | --- | --- |
| login | SAFE | Covered by existing P23A/P23B CSRF tests. |
| logout | SAFE | Positive-path logout POST with CSRF token now covered. |
| admin | SAFE | Admin remains protected by Django admin and existing smoke coverage. |
| users | SAFE | Existing users CSRF tests remain the baseline. |
| hymns | SAFE | Existing write API CSRF tests remain the baseline. |
| credentialed admin/users/hymns/humnos pages | SAFE | P23B force-login test covers all four core pages without depending on shell test credentials. |
| humnos | SAFE | Frontend token helper now supports both cookie names used elsewhere in the app; CSRF-enabled positive-path humnos info POST is covered with mocked `yt_dlp`. |
| CKEditor | SAFE | Upload endpoint is staff-only, POST-only, rejects missing token, and accepts valid CSRF token in local test. |
| eureka delete | BLOCKED | Not modified per P23B rules; remains GET-triggered destructive action. |

## Eureka Delete Remediation Plan

Recommended implementation:

1. Change `delete_view` to accept POST only, preferably with `@require_POST`.
2. Replace the delete `<a href>` in `eureka/modify.html` with a POST form containing `{% csrf_token %}`.
3. Keep the existing confirmation prompt client-side, but make the destructive request a form submit.
4. Add tests:
   - GET `/eureka/modify/delete/<church_id>/` returns 405 or non-destructive redirect.
   - POST without CSRF is 403 when CSRF is enabled.
   - POST with CSRF reaches the view.
   - A test fixture or disposable member is used so no restored production-like row is deleted.

Risk analysis:

- Current GET delete can be triggered by link prefetching, browser navigation, or cross-site image/link tricks.
- Enabling CSRF alone does not protect GET-based destructive actions.
- The fix is conceptually small but high-impact because it changes a destructive workflow and must avoid deleting restored local data during tests.

## Remaining Blockers

| Blocker | Status |
| --- | --- |
| Eureka GET delete method safety | Still blocking production. |
| Full credentialed browser/manual workflow | Still recommended before production CSRF enablement. |
| Static/media production serving | Outside P23B, still tracked from P21B. |

## Production Readiness Impact

CSRF wiring is no longer expected to be a production blocker after the humnos helper and CKEditor/logout tests pass.

Production CSRF enablement should wait for P23C decision and the separate Eureka delete method-safety remediation.

## Decision

Proceed to P23C CSRF Enablement Decision.
