# 下一階段改善規劃

更新日期：2026-05-29

## 原則

1. 不部署到 `.240`。
2. 不修改 `.240`。
3. 不重啟遠端服務。
4. 先在本機與 GitHub repository `nghcc-admin-platform` 完成文件、測試與小步改善。
5. 不一次大改程式，所有重構需先有備份、測試與回復方案。

## P0：安全與資料完整性

目標：先確保本機重建資料與正式備份可以完整、可重複地還原。

- 使用 Linux/WSL2 或 Docker named volume 完整還原 media。
- 補齊 Windows bind mount 缺漏的 15 個中文檔名照片。
- 確認 DB dump / media / uploads checksum。
- 確認備份與還原流程可重複執行。
- 將缺漏 media 清單固定記錄，避免後續誤判為正式資料遺失。
- 將還原流程整理成可重跑腳本，並保留執行紀錄。
- 新增 `docker-compose.volume.yml`，讓本機可選擇 `nghcc-admin-media-data` named volume。
- 新增 `scripts/restore-media-to-volume.sh`，使用 temporary container 在 Linux filesystem 內解壓 media。
- 新增 `scripts/restore-db.sh`，依 `.env` 匯入本機 DB 並檢查 52 tables。
- 新增 `scripts/verify-backup-checksum.sh`，驗證備份資料夾內 checksum。
- 新增 `scripts/check-media-integrity.sh`，支援 bind mount 與 named volume 檔案數檢查。

驗收條件：

- media 檔案數與 tar 內檔案數一致。
- DB 匯入後 tables、users、menus、permissions 數量一致。
- `scripts/check-local.ps1` 與 `scripts/check-local.sh` 均可通過。
- named volume media 檔案數達到 `33827`。
- Windows bind mount 若仍缺 15 個中文檔名照片，需保留為已知限制並改用 volume 作為完整還原結果。

P0 操作順序：

```bash
BACKUP_TS=20260529-134006
BACKUP_DIR=backups/192.168.16.240/$BACKUP_TS

scripts/verify-backup-checksum.sh "$BACKUP_DIR"
YES=1 scripts/restore-db.sh "$BACKUP_DIR/nads26db-$BACKUP_TS.sql.gz"
scripts/restore-media-to-volume.sh "$BACKUP_DIR/nads26-media-$BACKUP_TS.tar.gz"
scripts/check-media-integrity.sh volume nghcc-admin-media-data
docker compose -f docker-compose.yml -f docker-compose.volume.yml up -d --build
scripts/check-local.sh
```

## P1：系統邊界釐清

目標：分清楚哪些功能屬於北門行政作業平台，哪些屬於其他教會系統或未來功能。

- 確認奉獻功能是否屬於本系統。
- 確認課程/教育是否屬於本系統。
- 確認報表/財會是否屬於本系統。
- 把選單佔位分類為：待開發 / 外部系統 / 停用。
- 盤點教會軟硬體維護系統、重修舊好維修系統、QR 報到系統、折價券系統的 repo、Docker、port、DB 與用途。

驗收條件：

- `docs/module-inventory.md` 的每個選單都有明確狀態。
- `docs/church-system-landscape.md` 不再有未確認的 repo / port / DB 欄位。

## P2：權限模型整理

目標：讓登入權限、功能權限與左側選單可見性一致。

- 第一階段已完成權限模型盤點文件 `docs/permission-audit.md`。
- 第一階段已完成權限矩陣草案 `docs/permission-matrix.md`。
- 第一階段已完成 URL 權限地圖 `docs/url-permission-map.md`。
- 第一階段已新增唯讀盤點腳本 `scripts/audit-permissions.sh` / `scripts/audit-permissions.ps1`。
- 第一階段已新增 permission visibility tests。
- 第一階段尚未做任何權限重構。
- 第二階段已補強 `/hymn_resources/htm/<filename>` 登入限制。
- 第二階段已新增 URL access control tests。
- 第三階段已完成 menu permission 使用方式分析。
- 第三階段已建立 `ENABLE_MENU_PERMISSION_ENFORCEMENT` PoC 開關與實驗性 helper。
- 第三階段只新增設計驗證測試，未套用正式 view/API，未做權限重構。
- 下一階段已整理 [view-api-enforcement-matrix.md](view-api-enforcement-matrix.md)，明確區分 Page View、Read-only API、Write API、Resource URL、Admin/User Management 的建議 enforcement。
- 下一階段只更新文件，未修改正式權限行為，未全面套用 menu permission。
- 盤點 Django permission。
- 盤點 group permission。
- 盤點 user permission。
- 盤點 menu permission。
- 建立一致的權限規則。
- 明確定義 superuser、staff、一般同工帳號的使用邊界。
- 檢查 `peter` 與 `peterchen` 的權限差異是否符合預期。

驗收條件：

- 每個自訂 URL 都有明確權限需求。
- 選單可見不代表可操作的風險被消除或記錄。
- P5 後續小修補已補上使用者管理 AJAX CSRF header；P2 第二階段已處理公開 HTM resource。P2 第三階段建議採用 B 起步、逐步往 C 收斂；後續 matrix 已確認 API 層需獨立設計 read/write permission，不直接沿用 page route。
- 不建議一次性重建權限模型，避免影響登入、左側選單、admin 與既有資料。

## P3：測試補強

目標：讓每次本機還原或小改版後，都能快速確認核心功能沒有壞。

- 登入 smoke test。
- 會員 smoke test。
- 詩歌 smoke test。
- 檔案上傳 smoke test。
- admin smoke test。
- health check test。
- 補上匯出功能與影音功能的非破壞性測試。

驗收條件：

- 本機可一鍵執行 smoke test。
- 測試不會修改正式資料；若修改本機測試資料，需自動清除。

## P4：命名遷移

目標：逐步把舊系統命名整理成 `nghcc-admin-platform`，同時避免一次大改造成風險。

- 評估 `nads26` 改名為 `nghcc-admin-platform` 的影響。
- 不要一次大改。
- 先整理 import / setting / container / DB / 文件命名。
- 逐步改名並保留相容性。
- 把 Docker 命名、資料庫命名、Django project 命名與文件命名分階段處理。

驗收條件：

- 每一階段改名都有可回復 commit。
- 舊路徑或舊設定仍有相容或遷移說明。

## P5：安全改善

目標：降低上線後常見 Web 風險，尤其是 CSRF、上傳與 session。

- 第一階段已建立 `docs/security-audit.md`。
- 第一階段已將 `DEBUG` / `ALLOWED_HOSTS` alias、cookie、安全標頭、上傳大小與副檔名設定環境變數化。
- 第一階段已建立 `nads26.upload_validation` helper。
- 第一階段只套用到詩歌上傳；Eureka 照片與 CKEditor 上傳先盤點未硬改。
- 第一階段已新增 read-only API integration tests。
- 第二階段已完成 CSRF 盤點與復原策略文件。
- 第二階段已將 Eureka 照片上傳套用共用 upload validation helper。
- 第二階段已加入 `UPLOAD_STRICT_MIME_CHECK` MIME 輔助檢查開關。
- 第二階段已建立 `.env.production.example`。
- 第二階段已新增 security tests。
- 第三階段已建立 `ENABLE_CSRF_PROTECTION` 開關。
- 第三階段已保留 `DisableCSRFMiddleware` 作為相容模式，並可在測試模式啟用 Django `CsrfViewMiddleware`。
- 第三階段已新增 `tests/security/test_csrf_behavior.py` 與 `scripts/run-csrf-tests.sh` / `scripts/run-csrf-tests.ps1`。
- 第三階段已完成表單與 AJAX CSRF 盤點。
- 後續小修補已補強 `accounts/user_list.html` 使用者管理 AJAX 的 `X-CSRFToken`，後端 superuser 檢查未變。
- 後續仍需在所有人工測試通過後，才正式啟用 CSRF middleware。
- 後續仍需評估 CKEditor / CMS / filer 上傳套件是否保留、停用或升級。
- 後續仍需檢查登入與 session 設定。

驗收條件：

- 正式環境不使用弱化 CSRF 的設定。
- 上傳端點有副檔名、MIME、大小與路徑穿越防護。
- secrets 只存在 `.env` 或主機環境，不進 Git。
- production 部署前必須確認 HTTPS、`SESSION_COOKIE_SECURE=True`、`CSRF_COOKIE_SECURE=True`、正式 `ALLOWED_HOSTS`、正式 `CSRF_TRUSTED_ORIGINS`。
- 移除或停用 `DisableCSRFMiddleware` 前，需通過 CSRF tests、smoke tests、POST/AJAX token 全盤點、登入/上傳/admin/會員/詩歌人工測試，並完成 DB/media 備份與 rollback 方法。
- Write API Permission / CSRF 盤點：新增 `docs/write-api-permission-plan.md`，針對 `/api/hymns/*`、`/api/humnos/*`、`/users/*` 的 create/update/delete/upload/download 類 API 建立矩陣。此階段只盤點與補測試，不部署、不連線、不修改 `.240`，不修改正式權限資料，不改 write API 預設行為。建議後續 scope：`api:hymns:write`、`api:hymns:upload`、`api:humnos:write`、`api:users:write`。
## API Permission Report-only / Feature Flag

本階段新增 `docs/api-permission-feature-flag-plan.md`，建立 `API_PERMISSION_MODE=off|report-only|enforce` 設計與 `nads26.api_permissions` skeleton。預設 `off`，`report-only` 只記錄不阻擋，`enforce` 保留未來啟用入口但本階段不使用。

已先針對 `/api/hymns/*` 與 `/api/humnos/*` 建立 scope mapping：`api:hymns:read`、`api:hymns:write`、`api:hymns:upload`、`api:humnos:read`、`api:humnos:write`。新增 `tests/security/test_api_permission_feature_flag.py` 驗證 `off` 與 `report-only` 不改變既有回應。
## API Permission Report-only Log Format

本階段新增 `docs/api-permission-reporting.md`，整理 report-only log 格式。`nads26.api_permissions` 現在以 `api_permission_report` 記錄 `mode`、`endpoint`、`method`、`scope`、`user_id`、`user_authenticated`、`user_is_superuser`、`decision`、`reason`，且不記錄 request body、query string、headers、cookies、token、password 或原始 payload。

已補強 `tests/security/test_api_permission_feature_flag.py` 驗證 report-only log 欄位與敏感資料排除。此階段仍不部署、不連線 `.240`、不改正式權限資料、不啟用 `enforce`、不改預設 API 行為。
## API Permission Report-only Log Review

Added `docs/api-permission-log-review.md`, `scripts/api_permission_log_review.py`, `scripts/review-api-permission-logs.sh`, and `scripts/review-api-permission-logs.ps1`.

Scope:
- Local/staging-like review only; do not deploy, connect to, or modify `.240`.
- No production permission data changes.
- No `enforce` enablement.
- No dashboard UI.
- No default API behavior changes.

Review fields are fixed to `time`, `user_id`, `endpoint`, `method`, `scope`, `decision`, and `reason`. The scripts filter Docker or local logs for `api_permission_report mode=report-only` and emit CSV for common API request decision/reason review.

Next recommended step: collect a local report-only sample from common `/api/hymns/*` and `/api/humnos/*` requests, review deny reasons, then decide whether scope storage design is ready before any future enforce planning.

## API Permission Report-only Local Sample

Added local-only report-only sampling for common `/api/hymns/*` and `/api/humnos/*` endpoints:

- `docs/api-permission-report-only-test-result.md`
- `scripts/api_permission_report_only_check.py`
- `scripts/run-api-permission-report-only-check.sh`
- `scripts/run-api-permission-report-only-check.ps1`

Scope:
- Runs only against local Docker Compose using one-off `API_PERMISSION_MODE=report-only`.
- Exports `reports/api-permission-review.csv` from safe log review fields.
- Exercises read/write/upload/download paths with validation failures or nonexistent ids so formal data is not created, changed, uploaded, deleted, or downloaded.
- Does not deploy, connect to, or modify `.240`.
- Does not enable `enforce`, change default API behavior, add business features, or design scope storage.

Latest local sample on 2026-05-30 generated `reports/api-permission-review.csv` with 16 rows: `allow/superuser=8` and `deny/missing_scope=8`.

## API Permission Report-only CSV Review

Added `docs/api-permission-scope-review.md` to review the local `reports/api-permission-review.csv` output without committing the CSV.

Review result:

- `allow/superuser=8`: expected; superuser bypass is explicit in the current skeleton.
- `deny/missing_scope=8`: expected; the sampled active non-superuser has no durable API scope storage or explicit `api_scopes` assignment.
- Covered endpoints remain `/api/hymns/`, `/api/hymns/<pk>/`, `/api/hymns/<pk>/upload/`, `/api/humnos/info/`, and `/api/humnos/download/`.
- Current required scopes are `api:hymns:read`, `api:hymns:write`, `api:hymns:upload`, `api:humnos:read`, and `api:humnos:write`.
- Read/write/upload/download categories are documented per endpoint, including the note that `/api/humnos/download/` is classified as download/write because it has side effects and resource cost.

Next recommended step: design scope storage requirements before any enforce planning. The storage design should cover user and role/group grants, effective-scope calculation, conservative staff defaults, visible superuser bypass, migration/backfill, audit output, and tests for explicit scope, inherited scope, missing scope, staff default behavior, and superuser bypass.

## API Permission Scope Storage Proposal

Added `docs/api-permission-scope-storage-proposal.md` as a design-only next phase.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No default API behavior change; default remains `off`.
- No new tables, migrations, model changes, or business features.
- No implementation; storage is proposed only.

Compared options:
- A. New API scope model.
- B. Reuse Django permission.
- C. Reuse menu permission.

Recommendation: adopt A, a dedicated API scope model, in a future implementation phase. It cleanly separates endpoint/method authorization from page menu visibility and Django model CRUD semantics, supports direct user grants and group grants, keeps staff defaults conservative, and keeps superuser bypass explicit in audit output.

Effective-scope rule summary:
- Superuser remains an audited bypass with `reason=superuser`.
- Non-superuser effective scopes are the union of enabled group grants and enabled direct user grants.
- Staff receives no API scopes by default.
- No deny grants or wildcards in the first implementation.

Migration/backfill recommendation:
- Add canonical scopes and storage behind the existing feature flag in a later phase.
- Backfill no grants for normal users or staff by default.
- Backfill no grants for superusers; rely on audited bypass.
- Create any role groups only after local/report-only review.
- Use `API_PERMISSION_MODE=off` as the primary rollback lever.

Next recommended step: review the proposal, then implement Option A with models, migrations, effective-scope tests, and an effective-scope report command while keeping default mode `off` and postponing `enforce`.

## API Permission Scope Storage Option A Phase 1

Added the first implementation phase for Option A.

Scope:
- Added `ApiScope`, `UserApiScopeGrant`, and `GroupApiScopeGrant` in `modules.accounts`.
- Added a migration that creates canonical scope rows for `api:hymns:read`, `api:hymns:write`, `api:hymns:upload`, `api:humnos:read`, and `api:humnos:write`.
- Added effective-scope helpers for report/review use.
- Added `report_api_effective_scopes` management command for local review.
- Added `tests/security/test_api_scope_storage.py`.

Constraints preserved:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- Default `API_PERMISSION_MODE=off` remains unchanged.
- Existing API blocking/default behavior is not changed.
- No formal grants are backfilled.

Next recommended step: run local report-only comparisons using the stored effective-scope report, review which users/groups should receive explicit grants, and document a grant assignment plan before any future enforcement work.

## API Scope Grant Assignment Review

Added `docs/api-scope-grant-assignment-review.md` and the read-only `plan_api_scope_grants` management command.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No default API behavior change; default remains `off`.
- No automatic grant backfill.
- No business features.

Grant policy:
- Superusers remain an audited bypass and should not receive backfilled grants.
- Group grants are the preferred assignment path.
- Direct user grants are exceptions only.
- `is_staff=True` does not grant API scopes.
- API scopes must not be inferred from page/menu visibility.

Recommended initial role groups:
- `api_hymns_readers`: `api:hymns:read`
- `api_hymns_editors`: `api:hymns:read`, `api:hymns:write`
- `api_hymns_uploaders`: `api:hymns:read`, `api:hymns:upload`
- `api_humnos_readers`: `api:humnos:read`
- `api_humnos_operators`: `api:humnos:read`, `api:humnos:write`

Added command:
```bash
python backend/manage.py plan_api_scope_grants --report-csv reports/api-permission-review.csv --active-only
```

The command emits endpoint mapping, recommended group grant rows, user review rows, and superuser bypass summary rows. It reads current effective scopes and optional report-only CSV input, but does not create groups, create grants, assign users, or update any permission data.

Next recommended step: run the read-only grant plan against a fresh local/report-only CSV, manually review actual users and groups, then prepare a separate reviewed apply/backfill proposal. Do not enable enforcement until grant data, tests, rollback, and audit output are reviewed.

## API Scope Reviewed Apply / Backfill Design

Added `docs/api-scope-reviewed-apply-plan.md` and the dry-run-only `apply_api_scope_reviewed_plan` management command skeleton.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No default API behavior change; default remains `off`.
- No direct grant writes.
- No automatic backfill.
- No business features.

Reviewed plan format:
- Executable CSV with required `action`, `group`, `username`, `scope`, `reason`, `reviewed_by`, `reviewed_at`, and `ticket` columns.
- YAML is documented as a future human-friendly format, but the skeleton currently accepts CSV only.

Supported reviewed action names:
- `create_group`
- `create_group_grant`
- `assign_user_to_group`
- `create_user_grant`
- `rollback_group_grant`
- `rollback_user_grant`
- `rollback_user_group_assignment`

Added command:
```bash
python backend/manage.py apply_api_scope_reviewed_plan --plan-file reviewed-api-scope-plan.csv
```

The command validates reviewed rows and emits dry-run audit-preview CSV rows. It reads current users, groups, scopes, and grants only to describe what would happen. It does not create groups, create grants, assign users, remove grants, or perform rollback. `--apply` is intentionally disabled and raises an error in this phase.

Next recommended step: after human review of this apply contract, add a separate transactional apply implementation with durable audit logging and rollback execution tests. Keep `API_PERMISSION_MODE=off` as the default rollback lever and do not consider enforcement until apply, rollback, and audit behavior are verified.

## API Scope Transactional Apply / Audit Design

Added `docs/api-scope-transactional-apply-plan.md`, `ApiScopeGrantAudit`, migration `0005_api_scope_grant_audit`, and stricter dry-run validation in `apply_api_scope_reviewed_plan`.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No default API behavior change; default remains `off`.
- No grant, group, or user assignment writes.
- No automatic backfill.
- No business features.

Transactional apply design:
- Future mutating apply must validate the full plan before writes.
- Future mutating apply must run under `transaction.atomic()`.
- Future mutating apply must write durable `ApiScopeGrantAudit` rows with previous state, planned state, result, plan version, checksum, reviewer, and ticket metadata.
- Rollback must be explicit reviewed rows with `rollback_of`.
- Incident rollback can still use `API_PERMISSION_MODE=off` without deleting grant data.

Current command behavior:
- Dry-run remains the default and only supported behavior.
- `--apply` remains intentionally disabled.
- Reviewed CSV plans require `plan_version`, `reason`, `reviewed_by`, `reviewed_at`, and `ticket`.
- The command computes a SHA-256 plan checksum and emits audit-preview rows.
- Optional `--expected-checksum`, `--expected-plan-version`, `--reviewed-by`, and `--ticket` checks can pin the reviewed artifact to a ticket.

Next recommended step: review this audit/rollback design, then add a separate explicitly approved transactional apply implementation that writes audit rows and grants only after expanded rollback tests pass.

## API Scope Transactional Apply Implementation

Added the explicitly approved transactional apply implementation for reviewed API scope plans.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No default API behavior change; default remains `off`.
- No automatic backfill.
- Mutating writes require both `--apply` and `--confirm-apply`.

Implemented actions:
- `create_group`
- `create_group_grant`
- `assign_user_to_group`
- `create_user_grant`

Safety behavior:
- Dry-run remains the default and writes nothing.
- `--apply` without `--confirm-apply` writes nothing.
- Mutating apply runs in one `transaction.atomic()` block.
- Each applied row writes `ApiScopeGrantAudit` with checksum, row number, reviewer, ticket, previous state, planned state, and result metadata.
- Transaction failure rolls back all rows, including audit rows.
- Rollback rows remain dry-run only; rollback execution should be implemented as a separately reviewed explicit command path.

Next recommended step: run a local reviewed apply against disposable test data, inspect the audit CSV/database rows, then design the explicit rollback command path before any production-like use.

## API Scope Reviewed Rollback Command

Added `docs/api-scope-reviewed-rollback-plan.md` and the independent `rollback_api_scope_reviewed_plan` management command.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No default API behavior change; default remains `off`.
- No rollback inference from audit rows or report-only logs.
- Rollback input must be a human-reviewed CSV rollback plan.
- Dry-run remains the default.
- Mutating rollback requires both `--apply` and `--confirm-rollback`.

Reviewed rollback CSV fields:
- `action`
- `group`
- `username`
- `scope`
- `rollback_of`
- `reason`
- `reviewed_by`
- `reviewed_at`
- `ticket`
- `notes`

Implemented rollback actions:
- `remove_user_from_group`
- `disable_user_grant`
- `disable_group_grant`
- `delete_empty_group` only when `--delete-empty-groups` is explicitly provided; groups are not deleted by default.

Safety behavior:
- Dry-run writes nothing.
- `--apply` without `--confirm-rollback` writes nothing.
- Confirmed rollback runs inside `transaction.atomic()`.
- Confirmed rollback writes `ApiScopeGrantAudit` rows with `rollback_of`, previous state, planned state, result, reviewer, ticket, row number, and checksum.
- Transaction failure rolls back all data changes and audit rows.

Next recommended step: run a disposable local reviewed apply and rollback pair, inspect the resulting audit chain by `rollback_of`, and keep enforcement disabled until operational review accepts the apply/rollback/audit workflow.

## Staging-like API Permission Report-only Recheck

Added `docs/api-permission-staging-like-recheck-plan.md` and `scripts/run-api-permission-staging-like-recheck.ps1`.

Scope:
- Local staging-like planning and verification only.
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- Default `API_PERMISSION_MODE=off` remains unchanged.
- No default API behavior change.
- No business features.

Required local preconditions:
- Latest `main`.
- Docker named volume media via `nghcc-admin-media-data`.
- Restored local DB.
- Refreshed `test_*` account matrix.
- One-off `API_PERMISSION_MODE=report-only` only for request sampling.

Verification order:
1. `check-local`.
2. Report-only requests.
3. CSV review.
4. Grant plan dry-run.
5. Disposable apply/rollback drill.
6. Smoke, CSRF, and full local pytest recheck.

The new script defaults to checklist output and requires `-ExecuteLocal` before it runs local commands. It contains no `.240` host, SSH, deploy, remote mutation, or enforce step.

Next recommended step: run the staging-like recheck locally, review the generated CSV and dry-run grant plan, then decide whether a separately reviewed grant apply proposal is ready. Enforcement remains out of scope.

## API Scope Reviewed Grant Backfill Plan

Added `docs/api-scope-reviewed-backfill-plan.md` plus proposal-only sample CSV artifacts:

- `docs/samples/api-scope-reviewed-backfill-sample.csv`
- `docs/samples/api-scope-reviewed-backfill-rollback-sample.csv`

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- Default `API_PERMISSION_MODE=off` remains unchanged.
- No default API behavior change.
- No direct grant apply.
- No automatic backfill.
- No business features.

Review result from the latest local report-only CSV and `plan_api_scope_grants` dry-run:
- Suggested groups: `api_hymns_readers`, `api_hymns_editors`, `api_hymns_uploaders`, `api_humnos_readers`, and `api_humnos_operators`.
- Suggested group grants: eight role-to-scope grants covering hymn read/write/upload and humnos read/write scopes.
- Direct user grants: none suggested.
- User assignments: candidate assignments for `peterchen` require human review before they can be included in an executable reviewed apply CSV.
- Rollback: disable applied grants and remove applied memberships through an explicit reviewed rollback CSV; keep groups by default.

Next recommended step: have an operational reviewer approve or remove each candidate user assignment, then generate final checksum-pinned apply and rollback CSVs. Do not run `--apply` or consider enforcement until the reviewed artifacts and local verification results are accepted.

## API Scope Final CSV Dry-run Review

Added `docs/api-scope-final-apply-dry-run-review.md` and final reviewed CSV artifacts:

- `docs/reviewed/api-scope-final-reviewed-apply.csv`
- `docs/reviewed/api-scope-final-reviewed-apply.csv.sha256`
- `docs/reviewed/api-scope-final-reviewed-rollback.csv`
- `docs/reviewed/api-scope-final-reviewed-rollback.csv.sha256`

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No `--apply`.
- No default API behavior change.
- No business features.

Review result:
- Final apply CSV contains five role group rows and eight group grant rows.
- Final rollback CSV contains eight explicit `disable_group_grant` rows.
- `peterchen` candidate assignments remain pending and were intentionally excluded from the applyable CSV artifacts.
- Apply dry-run passed with checksum, reviewer, ticket, and plan version pinning.
- Rollback dry-run passed with checksum, reviewer, and ticket pinning.

Next recommended step: have an operational reviewer approve or reject each pending `peterchen` assignment. Any approved assignment should be handled in a separate reviewed assignment CSV with a new checksum and another dry-run review before any local apply is considered.

## API Scope Operational Review Package

Added `docs/api-scope-operational-review.md` as a permission-manager review package.

Scope:
- No deployment, connection, or modification to `.240`.
- No `API_PERMISSION_MODE=enforce`.
- No `--apply`.
- No grants, groups, or users modified.
- No default API behavior change.

Review package contents:
- Scope design and effective-scope rules.
- Role group design for hymn and humnos API scopes.
- Explicit rollback flow and rollback mapping.
- Audit flow for reviewed apply and rollback commands.
- Pending `peterchen` assignments that remain excluded from the final reviewed apply CSV.
- Approval Checklist.
- Reject Checklist.
- Apply Prerequisites for a later separately approved local apply phase.

Current status:
- Final group and group-grant CSV artifacts remain dry-run reviewed only.
- `peterchen` assignments remain pending and require explicit approve/reject decisions.
- Enforcement remains out of scope.

Next recommended step: permission manager approval or rejection of role groups, group grants, and the three pending `peterchen` assignments. Any approved assignment should be handled in a separate checksum-pinned assignment package before any local apply is considered.
