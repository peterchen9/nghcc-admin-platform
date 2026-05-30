# P3 Smoke Test 策略

更新日期：2026-05-29

## 為什麼先做 Smoke Test

目前 `nghcc-admin-platform` 已定位為「Portal + 核心行政查詢平台」。這類系統最重要的是在修改 Docker、Django、套件版本、資料庫設定、media volume 或權限規則時，能快速知道核心入口是否壞掉。

本階段不追求高覆蓋率，也不測複雜業務流程。先建立最小但有效的保護網，確保系統可啟動、可登入、可讀核心資料、可讀 media、admin 可進入。

## 納入 Smoke Test 的功能

| 測試檔 | 驗證內容 |
| --- | --- |
| `tests/smoke/test_health.py` | `/api/health/` 回傳 HTTP 200 且 database 為 ok |
| `tests/smoke/test_login.py` | `/admin/login/` 可開啟，主要與次要測試帳號可登入 |
| `tests/smoke/test_members.py` | `/eureka/` 可開啟，`members` table 至少有 7895 筆 |
| `tests/smoke/test_hymns.py` | `/hymns/` 可開啟，`hymns` table 至少有 2958 筆 |
| `tests/smoke/test_media.py` | `MEDIA_ROOT` 可讀，檔案數至少 33827 |
| `tests/smoke/test_admin.py` | `/admin/` 可開啟或導向登入，登入後 admin index HTTP 200 |

## 納入唯讀 Integration Test 的功能

| 測試檔 | 驗證內容 |
| --- | --- |
| `tests/integration/test_readonly_api.py` | `/api/health/`、`/api/hymns/`、`/users/routes/` 的唯讀行為 |

## 納入 Security Test 的功能

| 測試檔 | 驗證內容 |
| --- | --- |
| `tests/security/test_upload_validation.py` | 上傳副檔名、大小、檔名清理、MIME strict mode、Eureka 不合法照片不建立資料 |
| `tests/security/test_security_settings.py` | DEBUG、ALLOWED_HOSTS、cookie/security settings 可由環境變數控制 |
| `tests/security/test_csrf_behavior.py` | `ENABLE_CSRF_PROTECTION` 開關、CSRF middleware 切換、未帶 token 的 POST 拒絕、帶 token 的 POST 不因 CSRF 被拒絕 |
| `tests/security/test_user_ajax_csrf.py` | 使用者管理頁面含 CSRF token、AJAX 含 `X-CSRFToken`、CSRF 模式下 `/users/*` POST 未帶 token 會被拒絕、帶 token 可通過 CSRF 檢查到達 view |
| `tests/security/test_url_access_control.py` | `/hymn_resources/htm/<filename>` 未登入不可讀、已登入可讀，核心頁面未登入不可進入、已登入可用 |
| `tests/security/test_menu_permission_strategy.py` | `ENABLE_MENU_PERMISSION_ENFORCEMENT` 關閉時維持現況，開啟時 PoC decorator 依 menu permission 放行或拒絕 |

## 尚未測試的功能

- 奉獻、財會、課程教育、報表：目前未在 admin-platform 內完整實作。
- QR 報到完整流程：目前只有 `checkin_records` 資料與會員頁局部引用。
- 影音下載外部實際下載：會牽涉第三方網站、網路與 ffmpeg/yt-dlp 行為，暫不放入最小 smoke test。
- 檔案上傳破壞性測試：目前先不寫入資料，後續可用自動清除策略補 integration test。
- CSRF 正式啟用情境：目前已建立 `ENABLE_CSRF_PROTECTION=True` 測試模式，且使用者管理 AJAX 已補 `X-CSRFToken`；正式環境尚未啟用，仍需人工驗證登入、上傳、admin、會員、詩歌與使用者管理新增/更新/刪除/權限更新。
- Menu permission view/API 層正式套用測試：目前已完成 PoC helper 測試，但尚未把 `allowed_menu_items` 全面套到正式 view/API。

## 執行方式

本機需先完成 P0 正式資料與 media named volume 還原，並啟動：

```bash
docker compose -f docker-compose.yml -f docker-compose.volume.yml up -d --build
```

設定測試帳密環境變數，不要寫進 Git：

```bash
export TEST_USERNAME=<username>
export TEST_PASSWORD=<password>
export TEST_USERNAME_SECONDARY=<username>
export TEST_PASSWORD_SECONDARY=<password>
export TEST_ADMIN_USERNAME=<username>
export TEST_ADMIN_PASSWORD=<password>
```

Git Bash / WSL2 / Linux：

```bash
scripts/run-smoke-tests.sh
```

PowerShell：

```powershell
.\scripts\run-smoke-tests.ps1
```

腳本會同時執行 `tests/smoke`、`tests/integration` 與 `tests/security`，且不連線 `.240`。

## CSRF 測試模式

P5 第三階段新增 CSRF 可開關測試。一般模式維持：

```bash
ENABLE_CSRF_PROTECTION=False
```

CSRF 復原測試模式使用：

```bash
ENABLE_CSRF_PROTECTION=True
```

Git Bash / WSL2 / Linux：

```bash
scripts/run-csrf-tests.sh
```

PowerShell：

```powershell
.\scripts\run-csrf-tests.ps1
```

此腳本只在測試容器內覆寫 `ENABLE_CSRF_PROTECTION=True`，不修改本機 `.env`，不連線 `.240`。`accounts/user_list.html` AJAX CSRF header 已補齊；正式啟用前仍需人工驗證使用者新增、更新、刪除與權限更新流程。

## 未來如何擴充

1. 擴充 API integration tests，先維持 read-only API。
2. 加入可自動清理的檔案上傳測試。
3. 為 QR 報到資料查詢補 fixture 或 read-only 檢查。
4. 為使用者權限與選單可見性補角色矩陣測試。
5. 建立匿名使用者、一般同工、superuser 三種角色的行為測試。

## CI 規劃

已建立 `.github/workflows/smoke-tests.yml` 作為 CI 基礎架構。由於目前 smoke test 依賴正式資料還原後的本機 DB 與 media volume，GitHub Actions 暫時只保留 build 與 scaffold。

後續要讓 CI 完整跑通，需要準備：

1. 去識別化的最小 MySQL fixture。
2. 小型 media fixture。
3. CI 專用 `.env.test`。
4. 不含正式密碼的測試帳號。
5. 可在 CI 中還原 DB 與 media 的腳本。
- Write API Permission / CSRF tests：新增 `tests/security/test_write_api_permissions.py`，盤點 `/api/hymns/*`、`/api/humnos/*`、`/users/*` 的 create/update/delete/upload/download 權限與 CSRF/session 行為。測試只固定目前行為與未來 scope 建議，不建立有效業務資料、不刪除既有資料、不連線 `.240`。建議 scopes：`api:hymns:write`、`api:hymns:upload`、`api:humnos:write`、`api:users:write`。
## API Permission Feature Flag Tests

新增 `tests/security/test_api_permission_feature_flag.py`。此測試只驗證 `API_PERMISSION_MODE=off|report-only` 的相容性與 `/api/hymns/*`、`/api/humnos/*` scope mapping，不啟用 `enforce`，不修改正式權限資料，不連線 `.240`。

測試重點：
- `off` 是預設值，完全不改現有 API 回應。
- `report-only` 只記錄 scope decision，不阻擋 request。
- 非法 mode 保守回到 `off`。
- mapping 覆蓋 `api:hymns:read`、`api:hymns:write`、`api:hymns:upload`、`api:humnos:read`、`api:humnos:write`。
## API Permission Report-only Log Tests

本階段補強 `tests/security/test_api_permission_feature_flag.py`，驗證 `report-only` log 具備追蹤欄位：`mode`、`endpoint`、`method`、`scope`、`user_id`、`user_authenticated`、`user_is_superuser`、`decision`、`reason`。

同時驗證 log 不包含 request body 中的 `password`、`token`、`csrfmiddlewaretoken` 或其值。此測試只檢查本機 log 格式，不啟用 `enforce`，不改預設 API 行為，不連線 `.240`。
## API Permission Report-only Log Review Tests

Added `tests/security/test_api_permission_log_review.py` for the local/staging-like log review workflow.

Coverage:
- Parses `api_permission_report mode=report-only` lines into the review fields `time`, `user_id`, `endpoint`, `method`, `scope`, `decision`, and `reason`.
- Ignores unrelated logs and non-report-only modes.
- Verifies the CSV output exposes only the safe review columns and does not forward request payload secrets.

Validation commands:
- `scripts/review-api-permission-logs.sh` or `.\scripts\review-api-permission-logs.ps1` for local Docker logs.
- `LOG_FILE=... scripts/review-api-permission-logs.sh` or `.\scripts\review-api-permission-logs.ps1 -LogFile ...` for local log files.

## API Scope Grant Assignment Review Tests

Added coverage for the read-only grant assignment planning phase in `tests/security/test_api_scope_storage.py`.

Coverage:
- `report_api_effective_scopes` remains report-only and lists stored effective scopes without writing grants.
- `plan_api_scope_grants` combines current effective scopes with optional report-only CSV observations.
- The plan command emits endpoint mapping, group grant recommendations, user review rows, and superuser bypass rows.
- The plan command does not create, update, or delete `UserApiScopeGrant` or `GroupApiScopeGrant` rows.
- Staff users are not treated as having default API scopes; they must be covered by group grants or reviewed as exceptions.
- Superuser activity remains grant-free and visible as bypass activity.

Validation command:
```bash
pytest tests/security/test_api_scope_storage.py
```

This review phase remains local/report-only. It must not deploy, connect to, or modify `.240`, must not enable `API_PERMISSION_MODE=enforce`, and must not change default API behavior.

## API Scope Reviewed Apply Dry-run Tests

Added coverage for the reviewed apply/backfill design phase in `tests/security/test_api_scope_storage.py`.

Coverage:
- `apply_api_scope_reviewed_plan` accepts a manually reviewed CSV plan.
- The command emits dry-run audit-preview rows for `create_group`, `create_group_grant`, `assign_user_to_group`, and `create_user_grant`.
- Dry-run does not create Django groups.
- Dry-run does not create `GroupApiScopeGrant` or `UserApiScopeGrant` rows.
- Dry-run does not assign users to groups.
- `--apply` is intentionally disabled in this phase and writes nothing.

Validation command:
```bash
pytest tests/security/test_api_scope_storage.py
```

This phase remains local/dry-run only. It must not deploy, connect to, or modify `.240`, must not enable `API_PERMISSION_MODE=enforce`, must not change default API behavior, and must not automatically backfill grants.

## API Scope Transactional Apply / Audit Tests

Added coverage for the transactional apply design phase in `tests/security/test_api_scope_storage.py`.

Coverage:
- `apply_api_scope_reviewed_plan` requires reviewed plan version metadata.
- The command computes a SHA-256 plan checksum and emits stable audit-preview event ids.
- Dry-run still does not create Django groups.
- Dry-run still does not create `GroupApiScopeGrant` or `UserApiScopeGrant` rows.
- Dry-run still does not assign users to groups.
- Dry-run does not write `ApiScopeGrantAudit` rows in this phase.
- `--apply` remains intentionally disabled and writes nothing.
- Malformed reviewed plans are blocked during validation before preview output is accepted.

Validation command:
```bash
pytest tests/security/test_api_scope_storage.py
```

This phase adds audit storage only; grant/group/user mutations remain out of scope until a later explicitly approved transactional apply phase.

## API Scope Transactional Apply Tests

Updated: 2026-05-30

Added coverage for the explicitly confirmed transactional apply phase in `tests/security/test_api_scope_storage.py`.

Coverage:
- Dry-run remains the default and writes no groups, grants, memberships, or audit rows.
- `--apply` without `--confirm-apply` is rejected and writes nothing.
- `--apply --confirm-apply` writes reviewed local test data for `create_group`, `create_group_grant`, `assign_user_to_group`, and `create_user_grant`.
- Applied rows write `ApiScopeGrantAudit` records with `dry_run=False`, status, result, previous state, planned state, checksum, row number, reviewer, and ticket metadata.
- Injected transaction failure rolls back groups, memberships, grants, and audit rows.
- Rollback action rows remain dry-run/preview-only for this phase.

Validation command:
```bash
docker-compose -f docker-compose.yml -f docker-compose.volume.yml exec -T web sh -lc "cd /tmp && PYTHONPATH=/app DJANGO_SETTINGS_MODULE=nads26.settings pytest tests/security/test_api_scope_storage.py"
```

This phase remains local only. It must not deploy, connect to, or modify `.240`, must not enable `API_PERMISSION_MODE=enforce`, must not change default API behavior, and must not automatically backfill grants.

## API Scope Reviewed Rollback Tests

Added coverage for the independent reviewed rollback command path in `tests/security/test_api_scope_storage.py`.

Coverage:
- `rollback_api_scope_reviewed_plan` defaults to dry-run and writes no groups, grants, memberships, or audit rows.
- `--apply` without `--confirm-rollback` is rejected and writes nothing.
- `--apply --confirm-rollback` can remove reviewed user/group memberships and disable reviewed user/group grants in disposable local test data.
- Confirmed rollback writes `ApiScopeGrantAudit` records with `dry_run=False`, `rollback_of`, status, result, previous state, planned state, checksum, row number, reviewer, and ticket metadata.
- Injected transaction failure rolls back membership/grant changes and audit rows.
- Groups are not deleted by default. Optional empty-group deletion is guarded by `--delete-empty-groups`.

Validation command:
```bash
docker cp tests nghcc-admin-web:/tmp/tests
docker-compose -f docker-compose.yml -f docker-compose.volume.yml exec -T web sh -lc "cd /tmp && PYTHONPATH=/app DJANGO_SETTINGS_MODULE=nads26.settings pytest tests/security/test_api_scope_storage.py"
```

This phase remains local only. It must not deploy, connect to, or modify `.240`, must not enable `API_PERMISSION_MODE=enforce`, must not change default API behavior, and must not infer rollback from audit output.
