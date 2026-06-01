# P8/P9 Marker Coverage Review

Updated: 2026-06-01

## Scope

P8 was documentation-only. P9 adds pytest markers only to low-risk, clearly classified tests. It does not change test behavior, production application logic, permission behavior, production workflows, `API_PERMISSION_MODE`, database isolation, fixture behavior, assertions, or parallel execution.

The scan covers `tests/` on current `main`.

## Environment Notes

- `pytest.ini` registers `read_only`, `mutating`, `csrf`, and `api_scope`, sets `pythonpath = backend`, and sets `testpaths = tests`.
- `tests/conftest.py` has an autouse `allow_existing_database_access(django_db_blocker)` fixture. Every test can access the already-restored local database instead of a pytest-managed disposable test DB.
- P13 confirmed the previously observed repo-root directories `pytest.ini;C` and `tests;C` were empty and removed both. Pytest discovery now points at the real `pytest.ini` file and `tests/` directory.
- Because `testpaths = tests` depends on pytest running from the repo root, container or script working-directory drift could cause collection or marker registration surprises. No fix was made in this phase.
- Authentication helpers are conservative DB-write risks: `client.login()`, `client.force_login()`, `logged_in_client`, and `admin_client` may update `auth_user.last_login` through Django login signals. Files using them should not be marked `read_only` until verified or isolated.
- P16 records the marker policy explicitly: `read_only` is advisory only. It is not a transaction guarantee, a no-session-write guarantee, or a `pytest-xdist` / parallel-safety guarantee.
- Tests using `client.login()`, `force_login()`, `logged_in_client`, `admin_client`, or other login/session fixtures remain outside any truly parallel-safe read-only bucket unless later evidence proves they do not write session or auth state.
- Anonymous write-endpoint rejection tests are not automatically `read_only`; rejected write surfaces still require conservative review.
- Settings reload tests may remain `read_only` when they do not touch the DB, but they mutate process-global settings state rather than providing a parallel-safety guarantee.
- Global count assertions are not evidence of parallel safety when another process can write unrelated rows.

## Shared Fixtures

| File | Purpose | DB access | DB write | Fixture cleanup | Global count assertion | Initial classification | Next marker recommendation | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/conftest.py` | Unblocks DB; provides `client`, `logged_in_client`, `admin_client`. | Yes, globally unblocked; login fixtures authenticate against restored DB. | Possible via `client.login()` last-login updates. | No. | No. | unknown / needs review | Do not mark; document as shared DB-access source. | High |

## Test File Inventory

| File | DB access summary | DB write / mutation signal | Fixture cleanup | Global count assertion | Initial classification | Next marker recommendation | Risk |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `tests/integration/test_readonly_api.py` | GET `/api/health/`, `/api/hymns/`, `/users/routes/`; uses `logged_in_client` and `admin_client`. | Possible login last-login writes through fixtures. Endpoint calls appear read-only. | No. | No. | unknown / needs review | Split or verify auth write behavior before `read_only`; otherwise mark DB-auth cases `mutating` or keep serial. | Medium |
| `tests/smoke/test_admin.py` | GET `/admin/`; admin login fixture. | Possible admin login last-login write. | No. | No. | unknown / needs review | Anonymous GET may be `read_only`; logged-in case needs auth-write review. | Medium |
| `tests/smoke/test_health.py` | GET `/api/health/`; asserts DB reports ok. | No direct write seen. | No. | No. | read_only | P9 marked module `read_only`. | Low |
| `tests/smoke/test_hymns.py` | GET `/hymns/` with login; `Hymn.objects.count()`. | Possible login last-login write. | No. | Yes, restored-data threshold `Hymn.objects.count() >= 2958`. | unknown / needs review | Count-only test can be `read_only`; page test depends on auth-write review. | Medium |
| `tests/smoke/test_login.py` | Opens login page; calls `client.login()` for configured users. | Possible last-login writes. | No. | No. | unknown / needs review | Login page can be `read_only`; login cases should stay unmarked or `mutating` until verified. | Medium |
| `tests/smoke/test_media.py` | Reads `MEDIA_ROOT` and counts files. | No DB write; no DB access seen. File-system read only. | No. | Yes, global restored media count `>= 33827`. | read_only | P9 marked module `read_only`; still depends on restored media volume. | Low |
| `tests/smoke/test_members.py` | GET `/eureka/` with login; `Member.objects.count()`. | Possible login last-login write. | No. | Yes, restored-data threshold `Member.objects.count() >= 7895`. | unknown / needs review | Count-only test can be `read_only`; page test depends on auth-write review. | Medium |
| `tests/security/test_api_permission_feature_flag.py` | Reads users, exercises API permission mode and write API response preservation. | `force_login()` possible last-login writes; POST/PUT/DELETE write endpoints are intentionally reached but expected 400/404; report-only logs only. | No. | No. | api_scope / unknown / needs review | P9 marked only pure mode, scope-map, and RequestFactory report-log tests `read_only` + `api_scope`; write-endpoint response cases remain unmarked pending review. | High |
| `tests/security/test_api_permission_log_review.py` | Pure parser/CSV writer tests over strings and `StringIO`. | No DB access or write seen. | No. | No. | api_scope / read_only | P9 marked module `read_only` + `api_scope`. | Low |
| `tests/security/test_api_scope_storage.py` | Uses `ApiScope`, grant, audit, `User`, `Group`, management commands, CSV temp files. | Yes. Creates users/groups/grants/audit rows, toggles `ApiScope.active`, applies/rolls back confirmed plans. | Yes, namespace cleanup before/after test; resets canonical scope active state. | Scoped count assertions only after P7 Phase 4. | api_scope / mutating | Already module-marked `api_scope` and `mutating`; keep serial. | High |
| `tests/security/test_csrf_behavior.py` | Settings reload tests plus CSRF-mode client GET/POST login checks. | CSRF login POST with valid token may authenticate and update last-login. | No. | No. | csrf / unknown / needs review | P9 marked settings-only cases `read_only` where applicable and CSRF-specific cases `csrf`; valid login POST remains unmarked for `read_only`/`mutating` pending mutation review. | Medium |
| `tests/security/test_menu_permission_strategy.py` | Uses fake users and request factory; tests menu permission helpers and view wrapper. | No DB access or write seen. | No. | No. | read_only | P9 marked module `read_only`. | Low |
| `tests/security/test_permission_matrix.py` | Reads durable local test accounts and profiles; uses `force_login()` for HTTP matrix cases. | Possible last-login writes through `force_login()`. | No. | No. | unknown / needs review | Pure helper/matrix assertions may be `read_only`; HTTP `force_login` cases need auth-write review. | Medium |
| `tests/security/test_permission_visibility.py` | GET route visibility; queries active non-staff user; uses login fixture. | Possible login/force-login last-login writes. | No. | No. | unknown / needs review | Anonymous route checks may be `read_only`; logged-in cases need auth-write review. | Medium |
| `tests/security/test_read_only_api_permissions.py` | Static API permission matrix; queries durable account; GET/POST read-only API checks. | Possible `force_login()` last-login write; `humnos/info` POST is mocked to avoid download. | No. | No. | unknown / needs review | P9 marked only static matrix tests `read_only`; authenticated API cases remain unmarked pending auth-write review. | Medium |
| `tests/security/test_security_settings.py` | Settings/env reload tests. | No DB access or write seen. | No. | No. | read_only | P9 marked module `read_only`. | Low |
| `tests/security/test_upload_validation.py` | Pure upload validator plus `/eureka/add/` rejected upload using login fixture and `Member.objects.count()`. | Possible login last-login write; rejected upload asserts no member row is created. | No. | Yes, `Member.objects.count()` before/after. | unknown / needs review | P9 marked only pure validator tests `read_only`; rejected upload case remains unmarked pending write-path/auth review. | Medium |
| `tests/security/test_url_access_control.py` | Lists media hymn HTML files; GET protected resources/pages; uses login fixture. | Possible login last-login write. | No. | No. | unknown / needs review | Anonymous/media lookup pieces may be `read_only`; logged-in cases need auth-write review. | Medium |
| `tests/security/test_user_ajax_csrf.py` | GET user page for CSRF token/header; CSRF-mode user create POST checks. | Admin/superuser login may update last-login; CSRF valid POST reaches user create path but expects 400 duplicate/no write. | No. | No. | csrf / unknown / needs review | P9 marked CSRF token/header and CSRF-mode cases `csrf`; user create path remains unmarked for `read_only`/`mutating` pending write-path/auth review. | Medium |
| `tests/security/test_write_api_permissions.py` | Static write API matrix; anonymous and authenticated write endpoint checks. | Reads users; `force_login()` possible last-login writes; POST/PUT/DELETE write endpoints are exercised. | No. | No. | csrf / mutating / unknown / needs review | P9 marked static matrix tests `read_only` and CSRF-mode rejection test `csrf`; write endpoint tests remain unmarked for `mutating` pending durable-write review. | High |

## Classification Summary

| Bucket | Current candidates | Notes |
| --- | --- | --- |
| `read_only` | P9 marked `tests/smoke/test_health.py`, `tests/smoke/test_media.py`, `tests/security/test_api_permission_log_review.py`, `tests/security/test_menu_permission_strategy.py`, `tests/security/test_security_settings.py`, and static/pure test functions in `test_api_permission_feature_flag.py`, `test_read_only_api_permissions.py`, `test_upload_validation.py`, `test_write_api_permissions.py`, plus settings-only CSRF cases. | Mixed-file authenticated/write-path cases remain unmarked. |
| `mutating` | `tests/security/test_api_scope_storage.py`; likely write-path tests in `test_write_api_permissions.py`, `test_api_permission_feature_flag.py`, `test_upload_validation.py`, and CSRF/user create checks until proven otherwise. | Includes tests that intentionally reach POST/PUT/DELETE paths or rely on login/force-login write behavior. |
| `csrf` | P9 marked CSRF-specific tests in `test_csrf_behavior.py`, `test_user_ajax_csrf.py`, and `test_write_api_permissions.py`. | No `ENABLE_CSRF_PROTECTION=True` selection changes were made; smoke/CSRF wrappers remain serial. |
| `api_scope` | P9 preserved module markers on `test_api_scope_storage.py`, marked parser tests in `test_api_permission_log_review.py`, and marked pure mode/scope/log tests in `test_api_permission_feature_flag.py`. | Write/read API matrix docs remain unmarked as `api_scope` until marker intent is reviewed. |
| unknown / needs review | Most files using `logged_in_client`, `admin_client`, `client.login()`, or `force_login()`. | Main blocker is whether Django auth helpers are allowed to write `last_login` against the restored DB. |

## DB Write and Cleanup Observations

- Confirmed fixture cleanup exists only in `tests/security/test_api_scope_storage.py`, scoped by generated namespace and followed by canonical `ApiScope.active` reset.
- No other test file has durable cleanup for login metadata, write-path attempts, uploaded files, or user-management attempts.
- Global restored-state assertions remain in smoke/media/count tests:
  - `Hymn.objects.count() >= 2958`
  - `Member.objects.count() >= 7895`
  - restored media file count `>= 33827`
- Before/after global count assertions remain in `tests/security/test_upload_validation.py` for rejected member photo upload. This is safer than a loose global count check only if the suite stays serial and no other process writes members concurrently.

## Recommended Next Phase

1. Verify whether `client.login()` and `force_login()` update `last_login` in this project/runtime. Treat them as mutating until proven otherwise.
2. Mark at function granularity for mixed files instead of module granularity.
3. Start with obvious candidates:
   - `read_only`: parser, settings, fake-user menu permission, media read checks, health check.
   - `api_scope + mutating`: keep `test_api_scope_storage.py` as-is.
   - `csrf`: only tests that explicitly validate CSRF behavior or token/header behavior.
4. Keep write endpoint response-preservation tests serial and conservative until each endpoint is proven not to create rows/files on the exercised error path.
5. Do not change wrapper commands, workflow files, DB isolation, or parallel execution until marker accuracy is reviewed.

## P9 Marker Changes

P9 marked only low-risk or classification-clear tests:

- Module `read_only`: `tests/smoke/test_health.py`, `tests/smoke/test_media.py`, `tests/security/test_menu_permission_strategy.py`, `tests/security/test_security_settings.py`.
- Module `read_only` + `api_scope`: `tests/security/test_api_permission_log_review.py`.
- Function `read_only` + `api_scope`: pure mode, scope-map, and RequestFactory report-log tests in `tests/security/test_api_permission_feature_flag.py`.
- Function `read_only`: static matrix tests in `tests/security/test_read_only_api_permissions.py` and `tests/security/test_write_api_permissions.py`; pure validator tests in `tests/security/test_upload_validation.py`; settings-only CSRF mode tests in `tests/security/test_csrf_behavior.py`.
- Function `csrf`: CSRF-specific tests in `tests/security/test_csrf_behavior.py`, `tests/security/test_user_ajax_csrf.py`, and `tests/security/test_write_api_permissions.py`.

P9 intentionally did not mark unknown or needs-review cases involving `logged_in_client`, `admin_client`, `client.login()`, `force_login()`, or write endpoints as `read_only` or `mutating`.

## Verification for This Phase

Required verification is limited to:

```text
git status
git diff -- docs/test-marker-coverage-review.md
```

No full test run is required for this documentation-only review.
