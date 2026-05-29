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

- 檢查 CSRF middleware。
- 檢查 upload MIME type。
- 檢查檔名清理。
- 檢查檔案大小限制。
- 檢查登入與 session 設定。
- 檢查 `DEBUG`、`ALLOWED_HOSTS`、`CSRF_TRUSTED_ORIGINS` 的正式設定。
- 檢查 CKEditor 4 與相關上傳套件的維護狀態。

驗收條件：

- 正式環境不使用弱化 CSRF 的設定。
- 上傳端點有副檔名、MIME、大小與路徑穿越防護。
- secrets 只存在 `.env` 或主機環境，不進 Git。
