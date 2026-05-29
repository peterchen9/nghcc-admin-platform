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

## 後續保留風險

| 風險 | 說明 | 建議階段 |
| --- | --- | --- |
| 看不到選單但可直接打 URL | 詩歌、影音、Eureka 目前多以登入為界線，未檢查 `allowed_menu_items` | P2 後續小步評估 |
| API 細部權限不足 | `/api/hymns/*`、`/api/humnos/*` 主要依 `IsAuthenticated` | P2 後續搭配人工驗證 |
| 第三方上傳入口 | CKEditor uploader 仍需人工確認 | P5 後續 |
| 非 staff 測試缺口 | 本機正式還原資料沒有非 staff 使用者 | 測試 fixture 階段 |

## 下一步建議

先設計「menu permission 是否要進入 view/API 層」的最小策略，不建議直接全面套用。建議從 read-only 頁面開始建立測試矩陣，再挑一個低風險 URL 試行。
