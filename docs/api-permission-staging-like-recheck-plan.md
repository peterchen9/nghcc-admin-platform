# Staging-like API Permission Report-only Recheck Plan

Created: 2026-05-31

## Goal

Plan the next local staging-like recheck for API permission report-only coverage, CSV review, reviewed grant dry-run, and disposable apply/rollback drill verification.

This is a planning and local verification phase only. It does not deploy to `.240`, connect to `.240`, modify `.240`, enable `API_PERMISSION_MODE=enforce`, change the default `API_PERMISSION_MODE=off`, change default API behavior, or add business features.

## Staging-like Preconditions

Before running the recheck, confirm all of the following locally:

| Requirement | Local verification |
| --- | --- |
| Latest `main` | Work on branch `main`; fetch `origin/main`; verify the worktree is clean before starting and local `main` is not behind `origin/main`. |
| Named volume media | Use `docker-compose.yml` plus `docker-compose.volume.yml` with `nghcc-admin-media-data`, not the incomplete Windows bind-mounted media directory. |
| Restored DB | Restore the local DB from the reviewed backup using `scripts/restore-db.sh` or the documented PowerShell equivalent; confirm `scripts/check-local.ps1` passes. |
| `test_*` account matrix | Create or refresh `test_superuser`, `test_staff_menu`, `test_staff_nomenu`, and `test_user` with `scripts/create-test-accounts.ps1`. These accounts must remain local-only. |
| Report-only mode | Run report-only checks with a one-off `API_PERMISSION_MODE=report-only` environment override. Do not change `.env` defaults; default mode remains `off`. |

Recommended service startup:

```powershell
docker compose -f docker-compose.yml -f docker-compose.volume.yml up -d --build
```

## Verification Order

Run the recheck in this order so early environment problems stop later grant/audit checks:

1. Local health check:

```powershell
.\scripts\check-local.ps1
```

2. Refresh local test account matrix:

```powershell
.\scripts\create-test-accounts.ps1
```

3. Report-only request sample:

```powershell
.\scripts\run-api-permission-report-only-check.ps1
```

Expected behavior:
- Runs only against local Docker Compose.
- Uses one-off `API_PERMISSION_MODE=report-only`.
- Writes safe review output to `reports/api-permission-review.csv`.
- Does not change the default `API_PERMISSION_MODE=off`.

4. Review CSV:

```powershell
Import-Csv reports\api-permission-review.csv |
  Group-Object decision, reason |
  Sort-Object Name |
  Select-Object Name, Count
```

Review expectations:
- `allow/superuser` rows remain visible as audited bypass behavior.
- `deny/missing_scope` rows remain expected for non-superuser `test_*` users unless a reviewed local grant exists.
- No request body, query string, headers, cookies, CSRF token, password, token, file content, or raw payload appears in the CSV.

5. Grant plan dry-run:

```powershell
$reportPath = (Resolve-Path "reports").Path
docker compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
  -v "${reportPath}:/app/reports" `
  web `
  python manage.py plan_api_scope_grants `
  --report-csv reports/api-permission-review.csv `
  --active-only
```

Expected behavior:
- Reads report-only CSV and stored effective scopes.
- Emits endpoint mapping, recommended role grant rows, user review rows, and superuser bypass rows.
- Does not create groups, create grants, assign users, or update permission data.

6. Disposable apply/rollback drill:

```powershell
.\scripts\run-api-scope-apply-rollback-drill.ps1
```

Expected behavior:
- Uses only `test_user`, `test_staff_nomenu`, and `test_api_scope_drill_readers`.
- Runs apply dry-run, confirmed local apply, verification, rollback dry-run, confirmed local rollback, and rollback verification.
- Leaves no enabled drill grants or drill membership after rollback.
- Keeps disabled grant rows and audit rows for audit continuity.

7. Regression tests:

```powershell
.\scripts\run-smoke-tests.ps1
.\scripts\run-csrf-tests.ps1
$testsPath = (Resolve-Path "tests").Path
$pytestIniPath = (Resolve-Path "pytest.ini").Path
$apiPermissionLogReviewPath = (Resolve-Path "scripts/api_permission_log_review.py").Path
docker compose -f docker-compose.yml -f docker-compose.volume.yml run --rm `
  -v "${testsPath}:/app/tests:ro" `
  -v "${pytestIniPath}:/app/pytest.ini:ro" `
  -v "${apiPermissionLogReviewPath}:/app/scripts/api_permission_log_review.py:ro" `
  web pytest tests/smoke tests/integration tests/security
```

## Orchestration Checklist Script

Use the local checklist/orchestration script:

```powershell
.\scripts\run-api-permission-staging-like-recheck.ps1
```

Default mode prints the ordered checklist and commands only. To execute the local sequence explicitly:

```powershell
.\scripts\run-api-permission-staging-like-recheck.ps1 -ExecuteLocal
```

The script is local-only:
- It contains no `.240` host, SSH, deploy, or remote modification step.
- It uses `docker compose -f docker-compose.yml -f docker-compose.volume.yml`.
- It never enables `enforce`.
- It does not edit `.env`.
- It leaves default API behavior unchanged.

## Acceptance Criteria

- `scripts/check-local.ps1` passes.
- Report-only sample generates `reports/api-permission-review.csv`.
- CSV review confirms only safe review fields are exported.
- Grant plan runs as dry-run/read-only.
- Disposable apply/rollback drill verifies rollback state and `rollback_of` audit chain.
- Smoke, CSRF, and full local pytest suites pass with expected skip counts.
- No default mode, API behavior, deployment target, or business feature changes are introduced.

## Next Step After Recheck

If the local staging-like recheck passes, review the latest CSV and grant plan output manually. Any real grant backfill should still require a separate reviewed apply plan and a fresh rollback plan before enforcement is considered.
