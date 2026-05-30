# API Permission Report-only Log Review

Created: 2026-05-30

## Goal

Provide a local and staging-like way to review `API_PERMISSION_MODE=report-only` decisions without changing default API behavior, enabling `enforce`, deploying to `.240`, connecting to `.240`, or modifying production permission data.

This is a read-only log review workflow. It does not add dashboard UI and does not inspect request bodies, query strings, headers, cookies, session ids, CSRF tokens, passwords, bearer tokens, or other sensitive payload data.

## Query Fields

The review output is CSV with these columns:

| Field | Meaning |
| --- | --- |
| `time` | Docker log timestamp when available. Empty for local log lines without a timestamp. |
| `user_id` | Django user id from the report-only log line. |
| `endpoint` | Decorated API endpoint pattern, such as `/api/hymns/`. |
| `method` | HTTP method, such as `GET`, `POST`, `PUT`, or `DELETE`. |
| `scope` | Scope mapped to the endpoint and method, such as `api:hymns:write`. |
| `decision` | Report-only decision: `allow` or `deny`. |
| `reason` | Decision reason, such as `missing_scope`, `explicit_scope`, `superuser`, `anonymous_user`, or `missing_scope_mapping`. |

## Usage

Review Docker Compose logs from the local web service:

```bash
scripts/review-api-permission-logs.sh
```

Review a local log file:

```bash
LOG_FILE=reports/local-api.log scripts/review-api-permission-logs.sh
```

PowerShell equivalents:

```powershell
.\scripts\review-api-permission-logs.ps1
.\scripts\review-api-permission-logs.ps1 -LogFile reports\local-api.log
```

Optional environment variables for the shell script:

| Variable | Default | Purpose |
| --- | --- | --- |
| `COMPOSE` | `docker compose` | Compose command to run. |
| `COMPOSE_FILES` | `-f docker-compose.yml -f docker-compose.volume.yml` | Compose file arguments. |
| `SERVICE` | `web` | Compose service to read logs from. |
| `TAIL` | `1000` | Number of log lines to inspect. |
| `LOG_FILE` | empty | Read this local file instead of Docker logs. |

PowerShell exposes the same controls as parameters: `-ComposeCommand`, `-Service`, `-Tail`, and `-LogFile`.

## Example

Input:

```text
2026-05-30T08:12:44.123Z web-1 | api_permission_report mode=report-only endpoint=/api/hymns/ method=POST scope=api:hymns:write user_id=123 user_authenticated=True user_is_superuser=False decision=deny reason=missing_scope
```

Output:

```csv
time,user_id,endpoint,method,scope,decision,reason
2026-05-30T08:12:44.123Z,123,/api/hymns/,POST,api:hymns:write,deny,missing_scope
```

## Safety Notes

- The parser only emits `time`, `user_id`, `endpoint`, `method`, `scope`, `decision`, and `reason`.
- The parser ignores non-`api_permission_report` lines and ignores non-`report-only` modes.
- The workflow is local/staging-like only. Do not run it against `.240`.
- This review step does not enable `API_PERMISSION_MODE=enforce`.
- This review step does not change default API behavior.
