# 權限補強計畫

更新日期：2026-05-29

## 原則

- 不一次性重建權限模型。
- 不直接修改正式或本機還原的 user/group/permission/menu 資料。
- 優先處理「未登入即可讀取」的低風險明確缺口。
- `allowed_menu_items` 目前仍只代表左側選單可見性，不等於後端 URL 授權。

## P2 第二階段已完成

| 項目 | 狀態 |
| --- | --- |
| `/hymn_resources/htm/<filename>` | 已補 `@login_required` |
| 未登入讀取 HTM resource | 已由測試確認會被 redirect/forbidden |
| 已登入讀取 HTM resource | 已由測試確認仍可 HTTP 200 |
| 核心頁面 `/hymns/`、`/webav/`、`/eureka/` | 已由測試確認未登入不可進入、已登入可用 |

## P2 第三階段已完成

| 項目 | 狀態 |
| --- | --- |
| menu permission 使用方式分析 | 已建立 `docs/menu-permission-analysis.md` |
| enforcement 設計比較 | 已建立 `docs/menu-permission-enforcement-proposal.md` |
| PoC 開關 | 已新增 `ENABLE_MENU_PERMISSION_ENFORCEMENT=False` |
| 實驗性 helper | 已新增 `nads26.menu_permissions.menu_permission_required()` |
| 測試 | 已新增 `tests/security/test_menu_permission_strategy.py` |

本階段未套用正式 view/API，未改現有 `MenuPermissionMiddleware` 行為。

## P2 View/API Enforcement Matrix 已完成

| 項目 | 狀態 |
| --- | --- |
| Page View enforcement | 已整理於 `docs/view-api-enforcement-matrix.md` |
| Read-only API enforcement | 已整理於 `docs/view-api-enforcement-matrix.md` |
| Write API enforcement | 已整理於 `docs/view-api-enforcement-matrix.md` |
| Resource URL enforcement | 已整理於 `docs/view-api-enforcement-matrix.md` |
| Admin/User Management enforcement | 已整理於 `docs/view-api-enforcement-matrix.md` |

本階段只整理文件與後續判斷邊界，未修改正式行為。結論是 page view 可採 `login_required` 後逐頁評估 menu permission；API 層需另設 read/write 對照，不建議直接把 page route 的 menu permission 全面套到 `/api/*`。

## 後續保留風險

| 風險 | 說明 | 建議階段 |
| --- | --- | --- |
| 看不到選單但可直接打 URL | 現有 middleware 已涵蓋部分 app page route，但 API 與部分路徑仍未形成一致 view/API 層規則 | P2 後續小步評估 |
| API 細部權限不足 | `/api/hymns/*`、`/api/humnos/*` 主要依 `IsAuthenticated` | P2 後續搭配人工驗證 |
| 第三方上傳入口 | CKEditor uploader 仍需人工確認 | P5 後續 |
| 非 staff 測試缺口 | 本機正式還原資料沒有非 staff 使用者 | 測試 fixture 階段 |

## 下一步建議

維持 `ENABLE_MENU_PERMISSION_ENFORCEMENT=False`。先用低風險 read-only page route 完成人工驗證，再針對 `/api/hymns/*`、`/api/humnos/*` 分開設計 read/write API permission；使用者管理維持 superuser 為主，menu permission 只作為 UI 可見性。
