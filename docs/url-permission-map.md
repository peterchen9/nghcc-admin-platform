# URL 權限盤點

更新日期：2026-05-29

範圍：掃描本機 `urls.py`、`views.py`、decorators、DRF permission classes 與 middleware。未連線 `.240`，未修改資料庫。

| URL pattern | View | App | Login Required | Permission Required | Staff Required | CSRF 狀態 | 備註 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/api/health/` | `health_check` | `nads26` | 否 | 無 | 否 | GET，不需 CSRF | 公開 health check，低風險 |
| `/admin/` | Django admin | Django admin | 是 | Django admin permissions | middleware 限 superuser | Django admin 內建 CSRF；目前可用開關測試 | `MenuPermissionMiddleware` 會阻擋非 superuser 進 admin |
| `/users/` | `user_list` | accounts | 是 | 自訂 `is_superuser` | 實質限 superuser | 表單頁；AJAX header 待確認 | 使用者管理，高敏感 |
| `/users/routes/` | `app_routes` | accounts | 是 | DRF `IsAuthenticated` + `is_superuser` | 實質限 superuser | GET，不需 CSRF | 選單 API |
| `/users/create/` | `user_create` | accounts | 是 | DRF `IsAuthenticated` + `is_superuser` | 實質限 superuser | P5 已指出 AJAX CSRF header 待補 | POST，會建立使用者 |
| `/users/<int:pk>/` | `user_update` | accounts | 是 | DRF `IsAuthenticated` + `is_superuser` | 實質限 superuser | P5 已指出 AJAX CSRF header 待補 | PUT/POST，會修改使用者 |
| `/users/<int:pk>/permissions/` | `user_set_permissions` | accounts | 是 | DRF `IsAuthenticated` + `is_superuser` | 實質限 superuser | P5 已指出 AJAX CSRF header 待補 | POST，會修改 menu permission |
| `/users/<int:pk>/delete/` | `user_delete` | accounts | 是 | DRF `IsAuthenticated` + `is_superuser` | 實質限 superuser | P5 已指出 AJAX CSRF header 待補 | DELETE/POST，會刪除使用者 |
| `/ckeditor/upload/` | `ImageUploadView` | ckeditor | 是 | 套件內部檢查 | 未明確 | 需人工確認 | 第三方套件，不建議本階段硬改 |
| `/ckeditor/browse/` | `browse` | ckeditor | 是 | 套件內部檢查 | 未明確 | GET | 第三方套件 |
| `/api/humnos/info/` | `video_info` | humnos | 是 | DRF `IsAuthenticated` | 否 | AJAX 已送 `X-CSRFToken` | POST，取得外部影片資訊 |
| `/api/humnos/download/` | `video_download` | humnos | 是 | DRF `IsAuthenticated` | 否 | AJAX 已送 `X-CSRFToken` | POST，下載到暫存檔再回傳 |
| `/api/hymns/` | `hymn_list` | hymns | 是 | DRF `IsAuthenticated` | 否 | AJAX 寫入已送 `X-CSRFToken` | GET/POST；POST 可新增詩歌 |
| `/api/hymns/<int:pk>/` | `hymn_detail` | hymns | 是 | DRF `IsAuthenticated` | 否 | AJAX 寫入已送 `X-CSRFToken` | GET/PUT/DELETE |
| `/api/hymns/<int:pk>/upload/` | `hymn_upload` | hymns | 是 | DRF `IsAuthenticated` | 否 | AJAX 已送 `X-CSRFToken` | POST，上傳檔案 |
| `/hymn_resources/htm/<str:filename>` | `serve_htm_resource` | hymns | 是 | `@login_required` | 否 | GET，不需 CSRF | P2 第二階段已補登入限制；已登入詩歌功能不受影響 |
| `/worship/hymns/` | `hymns_page_view` | hymns | 是 | `@login_required` | 否 | GET | 與 `/hymns/` 相同頁 |
| `/hymns/` | `hymns_page_view` | hymns | 是 | `@login_required` | 否 | GET | 詩歌主頁 |
| `/webav/` | `humnos_page_view` | humnos | 是 | `@login_required` | 否 | GET | 影音工具頁 |
| `/eureka/` | `eureka_view` | eureka | 是 | `@login_required` | 否 | GET | 會員/關懷首頁 |
| `/eureka/photo/<str:filename>` | `serve_photo` | eureka | 是 | `@login_required` | 否 | GET | 照片讀取 |
| `/eureka/melos/<int:church_id>` | `melos_view` | eureka | 是 | `@login_required` | 否 | GET | 會員詳細資料 |
| `/eureka/neos` | `neos_view` | eureka | 是 | `@login_required` | 否 | form 有 `{% csrf_token %}` | POST 查詢新朋友 |
| `/eureka/pastoral/` | `pastoral_view` | eureka | 是 | `@login_required` | 否 | GET | 牧區小組 |
| `/eureka/add/` | `add_view` | eureka | 是 | `@login_required` | 否 | form 有 `{% csrf_token %}` | POST 新朋友照片上傳 |
| `/eureka/add/download/` | `download_add_view` | eureka | 是 | `@login_required` | 否 | form 有 `{% csrf_token %}` | POST 匯出 |
| `/eureka/modify/` | `modify_view` | eureka | 是 | `@login_required` | 否 | GET/POST 需人工確認 | 搜名單 |
| `/eureka/modify/download/` | `download_all_view` | eureka | 是 | `@login_required` | 否 | GET/POST 需人工確認 | 匯出 |
| `/eureka/modify/duplicates/` | `duplicates_view` | eureka | 是 | `@login_required` | 否 | GET | 重複資料 |
| `/eureka/modify/delete/<int:church_id>/` | `delete_view` | eureka | 是 | `@login_required` | 否 | POST/GET 需人工確認 | 高敏感：刪除會員資料 |
| `/` | `page_detail` | pages | 否 | 無 | 否 | GET | Portal 首頁，公開 |
| `/pages/edit-home/` | `edit_home` | pages | 是 | 自訂 `is_superuser` | 實質限 superuser | GET redirect，不需 CSRF | 導向 admin 編輯 |
| `/p/<slug:slug>/` | `page_detail` | pages | 否 | 無 | 否 | GET | 公開頁面 |
| `/media/<path>` | Django static serve | Django debug static | 否 | 無 | 否 | GET | 只在 `DEBUG=True` 時由 Django 提供 |

## 高風險標記

| 風險 | URL | 說明 | 建議 |
| --- | --- | --- | --- |
| 未登入可存取檔案 | `/hymn_resources/htm/<filename>` | 已補 `@login_required` | 後續只需評估是否再檢查 menu permission |
| POST endpoint 沒有細部 permission | `/api/hymns/*`, `/api/humnos/*`, `/eureka/*` | 多數只要求登入，未檢查 menu permission 或 Django permission | 不建議一次改，先補高風險寫入端點測試 |
| 只靠前端選單隱藏 | 詩歌、影音、Eureka | 左側選單不可見不等於 URL 不可存取 | 後續評估 view 層是否讀取 menu permission |
| AJAX endpoint 權限不明 | `/users/*` 前端 AJAX | 後端有 superuser 檢查，但 CSRF header 待補 | 建議 P5 CSRF/AJAX 小修補優先 |

## 本階段結論

目前沒有直接發現「未登入可讀大量會員資料」的 URL；會員、詩歌頁與影音頁皆需登入。P2 第二階段已先補上 `/hymn_resources/htm/<filename>` 登入限制。仍有多個「登入即可直接打 URL，不檢查選單授權」的情況，後續需小步評估是否將 menu permission 納入 view/API 層。
