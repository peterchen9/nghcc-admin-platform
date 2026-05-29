# 權限矩陣草案

更新日期：2026-05-29

本文件是設計盤點文件，不列出正式使用者姓名、email 或帳號。`Django Permission` 指 Django `auth_permission`；`Menu Permission` 指 `UserProfile.allowed_menu_items`。

| 功能 | 選單 | URL | Django Permission | Menu Permission | 目前狀態 | 風險 |
| --- | --- | --- | --- | --- | --- | --- |
| 會員/關懷 | 關懷、Eureka!找人、牧區小組、新朋友登記、搜名單 | `/eureka/`, `/eureka/*` | 未見明確 permission_required | 以 `allowed_menu_items` 控制可見性 | 已實作，需登入 | 看不到選單仍可能直接打 URL |
| 詩歌 | 崇拜禮儀 / 詩歌資料庫 | `/hymns/`, `/api/hymns/*`, `/hymn_resources/htm/<filename>` | 頁面與 HTM resource 需登入；API 使用 DRF `IsAuthenticated`，未見細部 Django permission | 以 `allowed_menu_items` 控制可見性 | 已實作，含上傳；HTM resource 已於 P2 第二階段補登入限制 | API 未檢查 menu permission |
| 影音 | 工具 / 網路影音下載 | `/webav/`, `/api/humnos/*` | DRF `IsAuthenticated`，未見細部 Django permission | 以 `allowed_menu_items` 控制可見性 | 已實作 | 下載 endpoint 寫入暫存檔，權限僅登入 |
| 使用者管理 | 管理員 / 使用者管理 | `/users/`, `/users/*` | view 以 `is_superuser` 自訂檢查 | 以 `allowed_menu_items` 控制可見性 | 已實作 | AJAX CSRF header 待補；menu 與 superuser 規則分離 |
| 首頁內容編輯 | 管理員 / 首頁內容編輯 | `/pages/edit-home/` | view 以 `is_superuser` 自訂檢查 | 以 `allowed_menu_items` 控制可見性 | 已實作，導到 Django admin | menu 與 superuser 規則分離 |
| 選單管理 | 管理員 / 選單項目管理 | `/admin/menu/menuitem/` | Django admin 權限 + middleware 限 superuser | 以 `allowed_menu_items` 控制可見性 | 已實作 | 主要依 superuser，不依 menu permission |
| QR 報到 | 報到系統 | 未見本系統 URL | 未見 | 目前有選單父層 | 外部或待開發 | 僅選單存在，需確認系統邊界 |
| 奉獻 | 奉獻 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位或外部 | 看得到父層但無功能，需分類 |
| 財會 | 財會 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位或外部 | 權限需求未定義 |
| 同工 | 同工 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位 | 權限需求未定義 |
| 交通 | 交通 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位 | 權限需求未定義 |
| 場地設施 | 場地設施 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位 | 權限需求未定義 |
| 資訊網路 | 資訊網路 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位 | 權限需求未定義 |
| 參考資料 | 參考資料 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位 | 權限需求未定義 |
| 報表 | 報表 | 未見本系統 URL | 未見 | 目前有選單父層 | 選單佔位或外部 | 權限需求未定義 |
| 折價券 | 無本機選單 | 外部系統 | 外部 | 外部 | 外部系統 | 需在系統景觀圖維護整合點 |
| 維修系統 | 無本機選單 | 外部系統 | 外部 | 外部 | 外部系統 | 需在系統景觀圖維護整合點 |

## 初步建議

1. 不建議一次性重建權限模型。
2. 先保留 menu permission 作為左側選單可見性控制。
3. 對高風險 URL 小步補後端授權測試，再決定是否將 menu permission 納入 view 層檢查。
4. 使用者管理與首頁內容編輯應維持 superuser 限制，後續才評估是否改成具體 Django permission。
5. `/hymn_resources/htm/<filename>` 已先補 `login_required`；是否再綁定詩歌選單權限留待後續階段。
