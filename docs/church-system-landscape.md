# 教會系統版圖盤點

更新日期：2026-05-29

## 本文件目的

本文件整理北門行政作業平台在教會系統中的定位，並標示目前已確認、推論與待確認的系統邊界。此文件只根據本機還原後程式碼、正式資料庫與既有 `.240` 盤點資訊撰寫，沒有修改正式主機。

## 系統清冊

目前只有北門行政作業平台已完成本機正式資料還原與 Docker 盤點。其他教會系統先列為待盤點，避免在未查證前誤填 repo、port 或 database。

| 系統 | Repo | Docker / container | Port | DB | 用途 | 狀態 |
| --- | --- | --- | --- | --- | --- | --- |
| 北門行政作業平台 | `peterchen9/nghcc-admin-platform` | 本機 `nghcc-admin-platform` / `nghcc-admin-web` / `nghcc-admin-db`；正式 `.240` 為 `nads26` / `nads26-web` / `nads26db` | 本機 `26001`；正式 `26001`；DB 本機 `26003` | 本機 `nghcc_admin`；正式來源 `nads26db` | 北門行政、會員關懷、詩歌、影音下載、使用者與選單管理 | 已盤點並完成本機還原 |
| 教會軟硬體維護系統 | 待盤點 | 待盤點 | 待盤點 | 待盤點 | 軟硬體設備、維護案件或資訊資產管理 | 待確認 |
| 重修舊好維修系統 | 待盤點 | 待盤點 | 待盤點 | 待盤點 | 維修案件、追蹤與處理紀錄 | 待確認 |
| QR 報到系統 | 待盤點 | 待盤點 | 待盤點 | 待盤點；可能與 `checkin_records` 有資料關聯 | 聚會或課程 QR 報到 | 待確認 |
| 折價券系統 | 待盤點 | 待盤點 | 待盤點 | 待盤點 | 折價券、兌換或活動優惠管理 | 待確認 |

## 已確認環境

| 系統 | 位置 | 狀態 | 說明 |
| --- | --- | --- | --- |
| 北門行政作業平台 | `http://192.168.16.240:26001` | 正式執行中 | Docker Compose project `nads26`，Web container `nads26-web` |
| 本機重建專案 | `http://localhost:26001` | 已還原正式 DB 與 media | Docker Compose project `nghcc-admin-platform` |

## 北門行政作業平台的角色

此平台目前主要扮演「內部行政與資料查詢平台」：

1. 會員與關懷資料查詢。
2. 牧區小組與新朋友資料整理。
3. 詩歌資料庫查詢與檔案管理。
4. 網路影音下載工具。
5. 使用者、權限與選單管理。
6. 首頁內容編輯與 Django admin 管理。

## 與其他系統的可能關聯

| 關聯方向 | 目前證據 | 待確認事項 |
| --- | --- | --- |
| 報到資料 | `checkin_records` 有大量資料 | 來源系統、同步方式、是否仍在使用 |
| 會員資料 | `members` 由 `managed = False` model 使用 | 會員主檔是否還有上游系統 |
| 影音工具 | `humnos` 呼叫外部影音查詢/下載能力 | 是否依賴外部 CLI 或第三方服務 |
| 詩歌媒體 | media 內含詩歌 HTML、MP3、PDF、MIDI | 檔案來源、版權與維護流程 |
| 首頁內容 | `pages` 與 CKEditor 上傳 | 是否需要整合教會官網或其他內容系統 |

## 目前不應混用的資源

依照專案原則，本系統應保持獨立：

| 資源 | 命名 |
| --- | --- |
| GitHub repository | `nghcc-admin-platform` |
| Docker Compose project | `nghcc-admin-platform` |
| Web container | `nghcc-admin-web` |
| DB container | `nghcc-admin-db` |
| Database | `nghcc_admin` |
| Local web port | `26001` |
| Local DB port | `26003` |

不可共用其他教會系統的 Docker compose、volume、container name 或 database。

## 功能成熟度

| 領域 | 成熟度 | 說明 |
| --- | --- | --- |
| 會員 / 關懷 | 高 | 資料量完整，頁面可運作 |
| 詩歌資料庫 | 高 | 查詢、明細與上傳已驗證 |
| 使用者與權限 | 中 | 可運作，但權限模型混合，需要整理 |
| 選單管理 | 中 | 可運作，但選單與實作功能不完全一致 |
| 影音下載 | 中 | 頁面可開啟，需再確認外部下載依賴 |
| 報到 / 活動 | 低至中 | 資料存在，但未見完整 UI/API |
| 奉獻 / 財會 | 低 | 目前只看到選單或名稱，未見完整實作 |
| 課程 / 教育 | 低 | `教育` 選單目前 inactive，未見完整實作 |
| 報表 | 低 | 未見獨立報表模組 |

## 後續系統治理建議

1. 建立「系統清冊」，明確列出每個教會系統的 repo、port、container、database、volume 與負責人。
2. 將北門行政作業平台的正式備份流程固定化，至少包含 DB dump、media、compose、env 範本與 checksum。
3. 將會員、報到、奉獻、課程、活動資料來源畫成資料流圖，避免資料重複或手動覆蓋。
4. 將目前選單佔位項目分類為「待開發」、「外部系統」、「暫停使用」三種狀態。
5. 將 `.240` 正式服務維持原狀，所有重構先在本機與 GitHub repo `nghcc-admin-platform` 完成。
