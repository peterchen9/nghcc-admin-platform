# 系統模組盤點

更新日期：2026-05-29

## 模組總覽

程式實作模組共 6 個：

| 模組 | 路徑 | 狀態 | 主要功能 |
| --- | --- | --- | --- |
| 使用者與權限 | `backend/modules/accounts/` | 已實作 | 使用者列表、新增、編輯、權限設定、可見選單 |
| 選單管理 | `backend/modules/menu/` | 已實作 | 左側選單、父子選單、排序、啟用狀態 |
| 頁面管理 | `backend/modules/pages/` | 已實作 | 首頁、內容頁、首頁內容編輯入口 |
| 關懷 / 會員 | `backend/modules/eureka/` | 已實作 | Eureka 找人、牧區小組、新朋友登記、搜名單、照片 |
| 詩歌資料庫 | `backend/modules/hymns/` | 已實作 | 詩歌查詢、明細、MP3/PDF/HTML/MIDI 檔案 |
| 網路影音下載 | `backend/modules/humnos/` | 已實作 | 影片資訊查詢與下載 |

## 左側選單盤點

正式資料還原後，`menu_menuitem` 共 23 筆，其中 22 筆啟用。依目前畫面與資料庫可歸納如下：

| 選單 | 子項目 / 路徑 | 實作狀態 |
| --- | --- | --- |
| 首頁 | `/` | 已實作 |
| 崇拜禮儀 | 詩歌資料庫 `/hymns/` | 已實作 |
| 聚會活動 | 無明確子頁 | 選單佔位 |
| 關懷 | Eureka!找人 `/eureka/` | 已實作 |
| 關懷 | 牧區小組 `/eureka/pastoral/` | 已實作 |
| 關懷 | 新朋友登記 `/eureka/add/` | 已實作 |
| 關懷 | 搜名單 `/eureka/modify/` | 已實作 |
| 同工 | 無明確路由 | 選單佔位 |
| 交通 | 無明確路由 | 選單佔位 |
| 教育 | 無明確路由，正式資料目前 inactive | 選單佔位 |
| 場地設施 | 無明確路由 | 選單佔位 |
| 工具 | 網路影音下載 `/webav/` | 已實作 |
| 資訊網路 | 無明確路由 | 選單佔位 |
| 報到系統 | 可能對應 `checkin_records`，未見完整 UI | 資料存在，功能需確認 |
| 管理員 | 首頁內容編輯 `/pages/edit-home/` | 已實作 |
| 管理員 | 使用者管理 `/users/` | 已實作 |
| 管理員 | 選單項目管理 `/admin/menu/menuitem/` | 已實作 |
| 財會 | 無明確路由 | 選單佔位 |
| 參考資料 | 無明確路由 | 選單佔位 |
| 奉獻 | 無明確路由 | 選單佔位 |

## 功能驗證狀態

| 功能 | 驗證方式 | 結果 |
| --- | --- | --- |
| 登入 | Django Client 以正式帳號登入 | `peter` 成功，`peterchen` 成功 |
| 首頁 | GET `/` | HTTP 200 |
| 管理後台 | GET `/admin/` | HTTP 200 |
| 使用者管理 | GET `/users/` | HTTP 200 |
| 權限路由 | GET `/users/routes/` | HTTP 200 |
| 詩歌資料庫 | GET `/hymns/`, `/api/hymns/` | HTTP 200 |
| 詩歌明細 | GET `/api/hymns/1/` | HTTP 200 |
| 詩歌上傳 | POST `/api/hymns/<id>/upload/` | HTTP 200，測試檔已清除 |
| 網路影音下載 | GET `/webav/` | HTTP 200 |
| Eureka 找人 | GET `/eureka/` | HTTP 200 |
| 牧區小組 | GET `/eureka/pastoral/` | HTTP 200 |
| 新朋友登記 | GET `/eureka/add/` | HTTP 200 |
| 搜名單 | GET `/eureka/modify/` | HTTP 200 |
| 重複名單 | GET `/eureka/modify/duplicates/` | HTTP 200 |
| 首頁內容編輯 | GET `/pages/edit-home/` | HTTP 302 至 Django admin |
| 選單管理 | GET `/admin/menu/menuitem/` | HTTP 200 |
| 健康檢查 | GET `/api/health/` | HTTP 200 |

## 未完整實作或待確認模組

| 模組 | 狀態 | 說明 |
| --- | --- | --- |
| 奉獻 | 未見對應 model/view/API | 目前只看到選單名稱，需確認是否在外部系統 |
| 課程 / 教育 | 未見對應 model/view/API | `教育` 選單在正式資料中為 inactive |
| 活動 | 未見完整活動模組 | 可能只存在報到紀錄或選單佔位 |
| 行政報表 | 未見獨立報表模組 | 可從資料推導，但沒有完整報表 UI |
| 財會 | 未見對應 model/view/API | 目前只看到選單名稱 |
| 場地設施 | 未見對應 model/view/API | 目前只看到選單名稱 |

## 模組盤點結論

目前可確認可運作的核心功能是會員關懷、詩歌資料庫、影音下載、使用者管理、選單管理與首頁內容管理。選單上顯示的部分行政類別尚未有程式實作，後續不應只依左側選單判定功能已完成。
