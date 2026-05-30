# API Permission Report-only Local Test Result

Created: 2026-05-30

## Goal

Run a local-only `API_PERMISSION_MODE=report-only` sample against common `/api/hymns/*` and `/api/humnos/*` endpoints, export `reports/api-permission-review.csv`, and inspect `decision` / `reason` distribution before any scope storage or enforcement design.

## Constraints

- Did not deploy to `.240`.
- Did not connect to `.240`.
- Did not modify `.240`.
- Did not enable `API_PERMISSION_MODE=enforce`.
- Did not change default API behavior; default remains `off`.
- Did not add business features.
- Did not design scope storage.

## Local Check Script

Run from the repository root:

```powershell
.\scripts\run-api-permission-report-only-check.ps1
```

Git Bash / WSL2 / Linux equivalent:

```bash
scripts/run-api-permission-report-only-check.sh
```

The script runs a one-off local Docker Compose web container with `API_PERMISSION_MODE=report-only`, mounts `scripts/api_permission_report_only_check.py`, writes raw report-only log lines to `reports/api-permission-report-only.log`, and exports the safe review CSV to `reports/api-permission-review.csv`.

## Endpoint Sample

The local sample uses Django's test client with an active local user, plus a local superuser when available:

| Method | Endpoint | Safety behavior |
| --- | --- | --- |
| GET | `/api/hymns/?page=1&page_size=1` | Read-only list sample. |
| POST | `/api/hymns/` | Empty title returns validation error; no hymn is created. |
| GET | `/api/hymns/999999/` | Nonexistent id returns 404. |
| PUT | `/api/hymns/999999/` | Nonexistent id returns 404; no hymn is updated. |
| DELETE | `/api/hymns/999999/` | Nonexistent id returns 404; no hymn is deleted. |
| POST | `/api/hymns/999999/upload/` | Nonexistent id returns 404 before file handling. |
| POST | `/api/humnos/info/` | Empty URL returns validation error; no external metadata request is made. |
| POST | `/api/humnos/download/` | Empty URL returns validation error; no download is started. |

## Latest Local Result

Executed: 2026-05-30

Output artifacts:

- `reports/api-permission-report-only.log`
- `reports/api-permission-review.csv`

CSV rows: 16

Decision/reason distribution:

| decision | reason | count |
| --- | --- | ---: |
| allow | superuser | 8 |
| deny | missing_scope | 8 |

Endpoint coverage in the CSV:

| Endpoint | Methods |
| --- | --- |
| `/api/hymns/` | GET, POST |
| `/api/hymns/<pk>/` | GET, PUT, DELETE |
| `/api/hymns/<pk>/upload/` | POST |
| `/api/humnos/info/` | POST |
| `/api/humnos/download/` | POST |

Observed behavior:

- Normal active local user produced `deny/missing_scope` for all 8 sampled endpoint/method pairs.
- Local superuser produced `allow/superuser` for all 8 sampled endpoint/method pairs.
- The CSV contains only the safe review columns: `time`, `user_id`, `endpoint`, `method`, `scope`, `decision`, and `reason`.
- Default behavior was not changed; report-only mode was limited to the one-off local check container and the helper's local `override_settings` block.

## Validation

Executed locally on 2026-05-30:

| Command | Result |
| --- | --- |
| `.\scripts\check-local.ps1` | Passed |
| `.\scripts\run-smoke-tests.ps1` | 95 passed, 19 skipped |
| `.\scripts\run-csrf-tests.ps1` | 100 passed, 14 skipped |
| `docker-compose ... web pytest` | 95 passed, 19 skipped |
