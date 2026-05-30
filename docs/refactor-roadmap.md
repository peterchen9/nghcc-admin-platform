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
