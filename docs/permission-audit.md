# P2 第一階段權限模型盤點

更新日期：2026-05-29

## 範圍

本文件只盤點本機 `nghcc-admin-platform` 還原資料與程式碼，不部署、不連線、不修改 `.240`，也不調整任何使用者、群組、permission 或選單授權關聯。

實際含使用者識別資料的唯讀報表由 `scripts/audit-permissions.sh` / `scripts/audit-permissions.ps1` 產生於 `reports/`，該目錄不提交 Git。

## 權限模型總覽

目前系統同時存在三層權限概念：

1. Django 內建 `auth_permission`、`auth_group_permissions`、`auth_user_user_permissions`。
2. 使用者管理與首頁編輯以 `is_superuser` 做自訂檢查。
3. 左側選單可見性以 `UserProfile.allowed_menu_items` 控制，superuser 可看到所有啟用選單。

重要結論：左側選單可見性目前不是 URL/view 的完整授權規則。也就是「看不到選單」不必然代表不能直接輸入 URL；「看得到選單」也不必然代表有 Django model permission。

## 本機統計

| 項目 | 數量 |
| --- | ---: |
| users | 5 |
| active users | 5 |
| staff users | 5 |
| superusers | 3 |
| groups | 1 |
| Django permissions | 185 |
| user permissions | 326 |
| group permissions | 161 |
| menu permissions | 44 |
| menu items | 23 |
| active menu items | 22 |

## 使用者摘要

| 類型 | 摘要 |
| --- | --- |
| superuser 清單 | 本機報表含實際 id，文件不列出帳號名稱 |
| staff user 清單 | 5 位 active users 皆為 staff |
| active user 清單 | 5 位 active users |
| 非 staff 使用者 | 本機正式還原資料中未找到非 staff 使用者，因此非 staff admin 行為需用測試 fixture 或另建測試帳號驗證 |

## 群組清單

| 群組 | permission 數量 | 備註 |
| --- | ---: | --- |
| 管理員 | 161 | 包含 auth、admin、CMS、filer、thumbnail、session、site 等多數 Django/CMS 權限 |

## Django permission

目前 `auth_permission` 共 185 筆，包含：

- Django 內建 auth/admin/session/contenttypes/sites。
- Django CMS 相關 `cms.*`。
- filer / easy_thumbnails / djangocms_* 套件權限。
- 本系統自訂 app，例如 `accounts.*`。

風險：大量 CMS/filer 權限仍存在，但 P1 已確認 CMS/filer 多屬歷史相容或殘留功能。後續不建議一次刪除，應先確認是否仍被 admin 或 CKEditor 使用。

## Group Permission

目前 `auth_group_permissions` 共 161 筆，集中在 `管理員` 群組。這代表群組權限偏大，較像「全管理權限包」，不是細粒度角色模型。

## User Permission

目前 `auth_user_user_permissions` 共 326 筆。代表部分使用者直接綁定大量 permissions。後續 P2 第二階段應盤點直接 user permission 是否與 group permission 重複，但本階段不改資料。

## Menu Permission

目前 menu permission 以 `accounts_userprofile_allowed_menu_items` 表示，共 44 筆。這不是 Django permission，而是左側選單顯示控制。

| 選單控制來源 | 規則 |
| --- | --- |
| superuser | 顯示所有 `is_active=True` 的選單與子選單 |
| 非 superuser | 只顯示 `UserProfile.allowed_menu_items` 允許的 route 或含允許子選單的父層 |
| `roles` 欄位 | 目前資料多為 `*`，程式未見實際依 `roles` 做授權判斷 |

## 每個選單需要哪些 permissions

目前選單本身沒有綁定 Django permission codename，只綁定 `UserProfile.allowed_menu_items`。因此「選單需要哪些 permissions」目前只能視為 menu permission，而非 Django permission。

高風險差異：

- 使用者管理選單：menu permission 控制是否看見 `/users/`，實際 view 另外要求 superuser。
- 首頁內容編輯：menu permission 控制是否看見 `/pages/edit-home/`，實際 view 另外要求 superuser。
- 詩歌與影音：menu permission 控制是否看見入口，但 API 目前主要只要求登入，沒有檢查是否被授權看到該選單。
- Eureka/會員：menu permission 控制是否看見入口，但 URL view 主要只要求登入。

## URL/View 權限摘要

完整 URL 盤點請見 [url-permission-map.md](url-permission-map.md)。

初步結論：

1. `/api/health/` 公開，屬低風險 health check。
2. `/users/*` 有登入與 superuser 檢查，但 AJAX CSRF header 仍待 P5 後續修補。
3. `/api/hymns/*`、`/api/humnos/*` 主要以 DRF `IsAuthenticated` 控制，未檢查 menu permission。
4. `/eureka/*` 多數使用 `@login_required`，未檢查 menu permission。
5. `/hymn_resources/htm/<filename>` 已於 P2 第二階段補上 `@login_required`，避免未登入直接讀取 HTM 詩歌檔。
6. `/p/<slug>/` 與首頁內容公開，符合 Portal/CMS 定位，但需確認頁面內容不含敏感資訊。

## 高風險與待確認

| 風險 | 描述 | 建議 |
| --- | --- | --- |
| 看不到選單但可直接打 URL | 詩歌、影音、Eureka API/view 多只檢查登入，未檢查 menu permission | 後續階段再評估是否將 menu permission 納入 view 層檢查，不建議一次重構 |
| 使用者管理 AJAX | 需要 superuser，但前端 CSRF header 仍需補強 | 建議先做 P5 CSRF/AJAX 小修補 |
| 非 staff 測試缺口 | 本機資料全為 staff，無法用正式還原資料驗證非 staff admin 行為 | 建議建立去識別化測試 fixture |
| HTM resource 公開 | 已補 `@login_required` | 後續可評估是否需要進一步檢查 menu permission |
| Django permission 與 menu permission 分離 | 看得見選單不代表有 Django permission，反之亦然 | 建議先建立權限矩陣，再小步修補高風險 URL |

## P2 第二階段 URL 權限小修補

`/hymn_resources/htm/<filename>` 對應 `modules.hymns.views.serve_htm_resource`，用途是相容舊前端，直接提供 HTM 歌詞/投影檔。由於無法確認所有 HTM 檔都適合完全公開，本階段已補上 `@login_required`。

已驗證：

- 未登入使用者不可讀取 `/hymn_resources/htm/<filename>`。
- 已登入使用者仍可正常讀取既有 HTM 詩歌檔。
- `/hymns/`、`/webav/`、`/eureka/` 未登入仍不可進入。

仍保留到後續階段：

- 詩歌、影音、Eureka 等核心功能目前多只要求登入，未檢查左側選單 `allowed_menu_items`。
- 是否將 menu permission 套入 view/API 層，需另行設計與人工驗證，避免一次改壞既有同工流程。

## 本階段不做的事

- 不調整任何 user/group/permission/menu 資料。
- 不移除 permission。
- 不改 URL 授權邏輯。
- 不建立新業務功能。
