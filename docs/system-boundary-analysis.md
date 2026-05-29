# 系統邊界分析

更新日期：2026-05-29

## 分析範圍

本文件只分析本機 `nghcc-admin-platform`。本次沒有修改程式邏輯、沒有新增功能、沒有部署到 `.240`，也沒有連線或重啟 `.240` 服務。

## 分類定義

| 分類 | 定義 |
| --- | --- |
| A. 已完整實作 | 有 Django app / URL / template 或 API / model / table / 實際資料，並已通過本機 smoke test |
| B. 部分實作 | 有資料或局部程式使用，但缺少完整 app、URL、template 或操作流程 |
| C. 僅選單存在 | `menu_menuitem` 有項目，但沒有對應 app、URL、template、model 或資料表 |
| D. 外部系統 | 目前 repo 內沒有實作，應視為其他系統或待整合系統 |
| E. 已停用 | menu table 中 `is_active=0`，目前不應出現在一般使用者功能範圍 |

## 掃描摘要

### Django Apps

目前 `INSTALLED_APPS` 中的自訂 Django app：

| App | 用途 |
| --- | --- |
| `modules.accounts` | 使用者、權限與使用者選單 |
| `modules.menu` | 左側選單 |
| `modules.pages` | 首頁與內容頁 |
| `modules.humnos` | 網路影音下載 |
| `modules.hymns` | 詩歌資料庫 |
| `modules.eureka` | 會員、關懷、新朋友與名單 |

### URL Routing

主要自訂 URL：

| 路徑 | 對應功能 |
| --- | --- |
| `/`、`/p/<slug>/`、`/pages/edit-home/` | 首頁與內容頁 |
| `/users/`、`/users/routes/`、`/users/create/`、`/users/<pk>/...` | 使用者管理 |
| `/api/hymns/`、`/api/hymns/<pk>/`、`/api/hymns/<pk>/upload/` | 詩歌 API |
| `/hymns/`、`/worship/hymns/`、`/hymn_resources/htm/<filename>` | 詩歌頁面與檔案 |
| `/webav/`、`/api/humnos/info/`、`/api/humnos/download/` | 網路影音下載 |
| `/eureka/`、`/eureka/pastoral/`、`/eureka/add/`、`/eureka/modify/` | 會員與關懷 |
| `/admin/` | Django admin |
| `/api/health/` | 健康檢查 |

### 重要資料表與資料量

| Table | 精確筆數 | 邊界判斷 |
| --- | ---: | --- |
| `members` | 7895 | 會員 / 關懷核心資料 |
| `hymns` | 2958 | 詩歌核心資料 |
| `checkin_records` | 107285 | 報到資料存在，但缺完整 QR 報到 app |
| `menu_menuitem` | 23 | 左側選單 |
| `accounts_userprofile` | 5 | 使用者延伸資料 |
| `pages_page` | 1 | 首頁 / CMS 型內容 |

資料庫總表數：52。

### 權限關聯

| 權限資料 | 數量 |
| --- | ---: |
| Django permission definitions | 185 |
| User direct permission grants | 326 |
| Group permission grants | 161 |
| Menu permission grants | 44 |
| Users | 5 |
| Groups | 1 |

一般功能頁多以 `login_required` 或 DRF `IsAuthenticated` 保護；使用者管理與部分管理入口額外要求 `is_superuser`。

## 左側選單分類

| Menu ID | 選單 | Route | Active | 分類 | 判斷 |
| ---: | --- | --- | --- | --- | --- |
| 39 | 崇拜禮儀 | 空 | 是 | B | 父層分類，子項目詩歌已實作 |
| 40 | 詩歌資料庫 | `/hymns/` | 是 | A | app、URL、template、model、table、資料與 smoke test 皆存在 |
| 41 | 聚會活動 | 空 | 是 | C | 僅選單存在，未見 app / URL / table |
| 42 | 關懷 | 空 | 是 | B | 父層分類，子項目 eureka 已實作 |
| 43 | Eureka!找人 | `/eureka/` | 是 | A | 會員查詢已實作且可操作 |
| 44 | 牧區小組 | `/eureka/pastoral/` | 是 | A | 牧區小組頁面已實作且可操作 |
| 45 | 新朋友登記 | `/eureka/add/` | 是 | A | 新朋友登記頁面已實作且可操作 |
| 46 | 搜名單 | `/eureka/modify/` | 是 | A | 名單搜尋 / 修改頁面已實作且可操作 |
| 47 | 同工 | 空 | 是 | C | 僅選單存在 |
| 48 | 交通 | 空 | 是 | C | 僅選單存在 |
| 49 | 教育 | 空 | 否 | E | menu table 中停用 |
| 50 | 場地設施 | 空 | 是 | C | 僅選單存在 |
| 51 | 工具 | 空 | 是 | B | 父層分類，子項目影音已實作 |
| 52 | 網路影音下載 | `/webav/` | 是 | A | app、URL、template 與 API 皆存在 |
| 53 | 資訊網路 | 空 | 是 | C | 僅選單存在 |
| 54 | 報到系統 | 空 | 是 | B | 有 `checkin_records` 資料，但沒有完整 QR 報到 app / URL |
| 55 | 管理員 | 空 | 是 | B | 父層分類，子項目管理功能已實作 |
| 56 | 財會 | 空 | 是 | C | 僅選單存在 |
| 57 | 參考資料 | 空 | 是 | C | 僅選單存在 |
| 58 | 奉獻 | 空 | 是 | C | 僅選單存在 |
| 59 | 使用者管理 | `/users/` | 是 | A | 使用者與權限管理已實作 |
| 60 | 首頁內容編輯 | `/pages/edit-home/` | 是 | A | 內容管理入口已實作 |
| 61 | 選單項目管理 | `/admin/menu/menuitem/` | 是 | A | Django admin 選單管理已實作 |

## 指定模組邊界分析

| 模組 | 分類 | Django app | URL | Template | Model | 資料表 | 實際資料 | 可正常操作 | 說明 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 會員 | A | `modules.eureka` | 有，`/eureka/`、`/eureka/melos/<id>` | 有，`eureka/eureka.html` | 有，`Member` | `members` | 有，7895 筆 | 是 | 會員主檔是 eureka 的核心資料 |
| 關懷 | A | `modules.eureka` | 有，`/eureka/`、`/eureka/pastoral/`、`/eureka/add/`、`/eureka/modify/` | 有 | 有，`Member` | `members` | 有 | 是 | 包含找人、牧區小組、新朋友、搜名單 |
| 詩歌 | A | `modules.hymns` | 有，`/hymns/`、`/api/hymns/` | 有，`hymns/hymns_page.html` | 有，`Hymn` | `hymns` | 有，2958 筆 | 是 | 已驗證頁面、API 與 upload |
| 影音 | A | `modules.humnos` | 有，`/webav/`、`/api/humnos/info/`、`/api/humnos/download/` | 有，`humnos/humnos_page.html` | 無專屬 model | 無專屬 table | 不需本地資料表 | 頁面可開；外部下載需另測 | 屬工具型功能，依賴 `yt-dlp` / `ffmpeg` |
| 奉獻 | C | 無 | 無 | 無 | 無 | 未見 | 未見 | 否 | menu 有 `奉獻`，但 repo 內未見實作 |
| 課程教育 | E | 無 | 無 | 無 | 無 | 未見 | 未見 | 否 | `教育` 選單目前 inactive；未見課程 app |
| 財會 | C | 無 | 無 | 無 | 無 | 未見 | 未見 | 否 | menu 有 `財會`，但 repo 內未見實作 |
| 報表 | D | 無 | 無 | 無 | 無 | 未見專屬表 | 未見 | 否 | 未在 menu table 與程式碼中看到獨立報表模組，應另行確認是否為外部或待開發 |
| QR 報到 | B | 無獨立 app | 無獨立 URL | 無獨立 template | 無獨立 model | `checkin_records` | 有，107285 筆 | 否，僅被會員明細局部引用 | eureka 會查首次打卡，但完整 QR 報到流程不在本 repo |
| 折價券 | D | 無 | 無 | 無 | 無 | 未見 | 未見 | 否 | repo 內未見 coupon / 折價券實作，應視為外部系統或待開發 |
| 維修系統 | D | 無 | 無 | 無 | 無 | 未見 | 未見 | 否 | repo 內未見維修或 maintenance app，應視為外部系統 |

## A. 已完整實作

- 會員 / 關懷：`modules.eureka`
- 詩歌資料庫：`modules.hymns`
- 網路影音下載頁面與 API：`modules.humnos`
- 使用者管理：`modules.accounts`
- 首頁內容編輯：`modules.pages`
- 選單項目管理：`modules.menu` + Django admin

## B. 部分實作

- QR 報到：有 `checkin_records` 資料，會員明細會查首次打卡，但沒有獨立 QR 報到 app / URL / template。
- 聚會活動：menu 有父層，但未見實作；可能應與 QR 報到或外部活動系統釐清。
- 父層選單：崇拜禮儀、關懷、工具、管理員是分類容器，本身不代表完整業務模組。

## C. 僅選單存在

- 奉獻
- 財會
- 同工
- 交通
- 場地設施
- 資訊網路
- 參考資料
- 聚會活動目前也可視為僅選單父層，需決定是否開發或移除。

## D. 外部系統 / 待整合

- 報表：目前沒有 admin-platform 內部實作證據。
- 折價券系統：目前沒有 admin-platform 內部實作證據。
- 維修系統：目前沒有 admin-platform 內部實作證據。
- QR 報到若已有獨立系統，admin-platform 應只做資料查詢或入口連結。

## E. 已停用

- 教育：`menu_menuitem.id=49`，`is_active=0`。目前不應列入可操作功能。

## 結論

admin-platform 目前真正成熟的範圍是「行政入口、會員關懷、詩歌資料庫、影音工具、使用者/選單管理、首頁內容管理」。奉獻、財會、課程教育、報表、折價券、維修系統沒有在此 repo 內形成完整模組；QR 報到只有資料表與會員頁局部引用，尚未構成獨立功能。
