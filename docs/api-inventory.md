# API 與 URL 盤點

更新日期：2026-05-29

## 統計口徑

本系統是 Django 單體式網站，許多資料操作端點不是 REST API，而是 Django view。為避免誤判，本文件分三種口徑：

| 口徑 | 數量 | 說明 |
| --- | ---: | --- |
| 自訂 API / 資料操作端點 | 15 | 含 `/api/*`、使用者管理操作、上傳、下載與刪除 |
| 自訂 URL 總數 | 29 | 含頁面、檔案服務、匯出、刪除與 API |
| Django admin 內建 URL | 多數由 admin 自動產生 | 不列入自訂 API 數量 |

## 自訂 API / 資料操作端點

| 方法 | 路徑 | 模組 | 權限需求 | Smoke test | 說明 |
| --- | --- | --- | --- | --- | --- |
| GET | `/api/health/` | health | 不需登入 | 已測 HTTP 200 | 健康檢查 |
| GET | `/users/routes/` | accounts | 登入且 superuser | 已測 HTTP 200 | 回傳可用路由或選單資訊 |
| POST | `/users/create/` | accounts | 登入且 superuser | 未做資料異動測試 | 新增使用者 |
| PUT/POST | `/users/<int:pk>/` | accounts | 登入且 superuser | 未做資料異動測試 | 編輯使用者 |
| POST | `/users/<int:pk>/permissions/` | accounts | 登入且 superuser | 未做資料異動測試 | 設定使用者權限 |
| DELETE/POST | `/users/<int:pk>/delete/` | accounts | 登入且 superuser | 未做刪除測試 | 刪除使用者 |
| POST | `/api/humnos/info/` | humnos | 登入 | 頁面已測；外部影音查詢待測 | 查詢影片資訊 |
| POST | `/api/humnos/download/` | humnos | 登入 | 未做下載測試 | 下載影片 |
| GET/POST | `/api/hymns/` | hymns | 登入 | GET 已測 HTTP 200；POST 未測 | 詩歌列表與新增 |
| GET/PUT/DELETE | `/api/hymns/<int:pk>/` | hymns | 登入 | GET 已測 HTTP 200；PUT/DELETE 未測 | 詩歌明細、編輯、刪除 |
| POST | `/api/hymns/<int:pk>/upload/` | hymns | 登入 | 已測 HTTP 200，測試檔已清除 | 詩歌檔案上傳 |
| GET | `/eureka/add/download/` | eureka | 登入 | 未做匯出檔下載測試 | 新朋友資料匯出 |
| GET | `/eureka/modify/download/` | eureka | 登入 | 未做匯出檔下載測試 | 名單資料匯出 |
| POST | `/eureka/modify/delete/<int:church_id>/` | eureka | 登入 | 未做刪除測試 | 刪除名單資料 |
| POST | `/ckeditor/upload/` | ckeditor | 登入 / admin 情境待確認 | 未做上傳測試 | 編輯器檔案上傳 |

## 自訂頁面與檔案 URL

| 路徑 | 模組 | 權限需求 | Smoke test | 說明 |
| --- | --- | --- | --- | --- |
| `/` | pages | 登入 | 已測 HTTP 200 | 首頁 |
| `/p/<slug:slug>/` | pages | 登入 | 未逐頁測試 | 內容頁 |
| `/pages/edit-home/` | pages | 登入且 superuser | 已測 HTTP 302 至 admin | 首頁內容編輯入口 |
| `/admin/` | Django admin | staff/superuser；非 superuser 會被 middleware 擋下 | 已測 HTTP 200 | 後台管理 |
| `/users/` | accounts | 登入且 superuser | 已測 HTTP 200 | 使用者管理列表 |
| `/hymns/` | hymns | 登入 | 已測 HTTP 200 | 詩歌資料庫頁面 |
| `/worship/hymns/` | hymns | 登入 | 未測，與 `/hymns/` 共用 view | 詩歌資料庫別名 |
| `/hymn_resources/htm/<str:filename>` | hymns | 檔案存在即可，未加 login decorator | 未測 | HTML 詩歌檔服務 |
| `/webav/` | humnos | 登入 | 已測 HTTP 200 | 網路影音下載頁面 |
| `/eureka/` | eureka | 登入 | 已測 HTTP 200 | Eureka 找人 |
| `/eureka/photo/<str:filename>` | eureka | 登入 | 未逐檔測試 | 會員照片檔案 |
| `/eureka/melos/<int:church_id>` | eureka | 登入 | 未逐筆測試 | 會員明細 |
| `/eureka/neos` | eureka | 登入 | 未測 | 新朋友相關頁面 |
| `/eureka/pastoral/` | eureka | 登入 | 已測 HTTP 200 | 牧區小組 |
| `/eureka/add/` | eureka | 登入 | 已測 HTTP 200 | 新朋友登記 |
| `/eureka/modify/` | eureka | 登入 | 已測 HTTP 200 | 搜名單 |
| `/eureka/modify/duplicates/` | eureka | 登入 | 已測 HTTP 200 | 重複名單 |
| `/media/<path>` | Django static helper | `DEBUG=True` 時由 Django 提供 | 間接驗證 media 掛載 | Debug 模式下提供 media |

## Admin URL

Django admin 自動產生下列模型管理入口：

| 模型 | Admin 路徑 |
| --- | --- |
| User / Group | `/admin/auth/` |
| UserProfile / SystemSetting | `/admin/accounts/` |
| MenuItem | `/admin/menu/menuitem/` |
| Page | `/admin/pages/page/` |
| Hymn | `/admin/hymns/hymn/` |
| Member | `/admin/eureka/member/` |

## API 風險與建議

1. 使用者管理端點混合 HTML form 與資料操作，建議後續分清楚頁面與 API。
2. `hymn_upload` 接受多種檔案類型，需補上大小限制、檔名清理、MIME 驗證與掃毒策略。
3. `eureka` 匯出與刪除功能需確認權限檢查是否足夠。
4. `/media/<path>` 在 `DEBUG=True` 時由 Django 提供，正式環境應改由 Nginx 或等效靜態檔服務處理。
5. CKEditor 4 相關上傳路徑需檢查套件維護狀態與安全修補。
