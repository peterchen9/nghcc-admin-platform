# P23A Local CSRF Verification Report

## Environment

| Item | Value |
| --- | --- |
| Branch | `csrf-local-verification` |
| Base commit | `692677b` |
| CSRF setting | `ENABLE_CSRF_PROTECTION=True` for CSRF wrapper only |
| Production env changed | No |
| Production DB changed | No |
| `.240` access | No |
| Deploy | No |
| API permission mode | `API_PERMISSION_MODE=enforce` was not enabled |

## Automated Test Results

| Command | CSRF mode | Passed | Failed | Skipped | Result |
| --- | --- | ---: | ---: | ---: | --- |
| `.\scripts\run-csrf-tests.ps1` | `ENABLE_CSRF_PROTECTION=True` inside test container | 93 | 0 | 39 | PASS |
| `.\scripts\run-smoke-tests.ps1` | Default local smoke mode | 88 | 0 | 44 | PASS |

The first direct container pytest attempt did not run because the image did not include the local `tests/` directory without the wrapper's bind mounts. The existing wrapper was then used successfully.

Skipped tests were caused by missing local test credentials or missing optional local test accounts such as `test_staff_nomenu` and `test_user`. No skipped item was caused by a CSRF failure.

## Functional Impact

| Flow | Status | Evidence |
| --- | --- | --- |
| login | SAFE | CSRF-enabled tests verified admin login GET is available, login POST without token is rejected, and token-based login path is covered when credentials are available. Credentialed login test was skipped because `TEST_USERNAME` / `TEST_PASSWORD` were not set. |
| logout | BLOCKED | Code has a POST logout form with `{% csrf_token %}`, but no automated functional logout test ran in this phase. |
| admin | SAFE | Smoke/admin and CSRF login checks passed for available coverage. Credentialed admin checks were partly skipped because test credentials were not set. |
| users | SAFE | CSRF-enabled tests verified write endpoints reject missing token and accept a token far enough to reach view validation. User page token/header inspection tests were skipped due credential fixture requirements. |
| eureka | SAFE | Existing CSRF-enabled suite passed and eureka GET smoke/read checks did not regress. Eureka form positive paths were not fully exercised because credentialed smoke tests were skipped. The existing GET delete method-safety issue remains recorded but was not modified. |
| hymns | SAFE | CSRF-enabled write API checks passed for missing-token rejection; smoke/read checks passed where local data allowed. Positive create/update/delete/upload with token still needs a later credentialed/manual pass. |
| humnos | SAFE | CSRF-enabled write API missing-token rejection passed. Existing AJAX code sends `X-CSRFToken`; positive external workflow remains best verified manually or with a mocked `yt_dlp` test. |
| CKEditor | BLOCKED | No automated CKEditor upload verification was executed. Third-party uploader CSRF behavior remains a manual verification item. |

## Root Cause Analysis

No CSRF-related test failure was observed.

Observed non-failure environment limitations:

| Area | Summary | Inferred cause |
| --- | --- | --- |
| Direct pytest container command | `ERROR: file or directory not found: tests/security/test_csrf_behavior.py` | The container image does not include local tests unless mounted by wrapper scripts. |
| Credentialed tests | Several login/admin/page tests skipped | Required `TEST_USERNAME`, `TEST_PASSWORD`, `TEST_ADMIN_USERNAME`, or related variables were not set in the local shell. |
| Permission matrix tests | Several tests skipped | Local test accounts such as `test_staff_nomenu` and `test_user` were not present. |
| CKEditor | Not verified | No existing automated CKEditor upload CSRF test in the executed suite. |

## Required Fixes

| Size | Item |
| --- | --- |
| Small | Add or run credentialed local checks with `TEST_USERNAME`, `TEST_PASSWORD`, `TEST_ADMIN_USERNAME`, and `TEST_ADMIN_PASSWORD` set. |
| Small | Add humnos token helper fallback for `cms26_csrftoken` if the project keeps multiple CSRF cookie names. |
| Medium | Add positive-path CSRF tests for hymns create/update/delete/upload and humnos info/download with mocked external calls. |
| Medium | Add or perform CKEditor upload CSRF verification from the admin/editor context. |
| High Risk | Eureka delete method safety remains a production blocker, but it was intentionally not changed in P23A. |

## Production Readiness Impact

CSRF itself is less likely to be a wiring blocker after this phase: the CSRF-enabled wrapper passed with 0 failures, and write endpoints correctly reject missing tokens.

CSRF should still remain a production blocker until credentialed positive-path testing and CKEditor upload verification are completed. The system is suitable to enter the formal CSRF fix/enablement phase, but not suitable for production CSRF enablement without the remaining manual/positive-path checks.

## Decision

GO for formal local CSRF enablement/fix work.

NO-GO for production enablement today because CKEditor, logout, and credentialed positive-path flows remain unverified, and Eureka GET delete method safety remains a separate critical blocker.
