# P5 第一階段安全盤點

更新日期：2026-05-29

## 範圍

本文件盤點本機 `nghcc-admin-platform`。本階段不部署、不修改、不重啟 `.240`，也不做 P2 權限重構或 P4 命名遷移。

## 安全設定盤點

| 項目 | 目前狀態 | 風險 |
| --- | --- | --- |
| DEBUG 設定來源 | `settings.py` 讀取 `DJANGO_DEBUG`，預設 `0` | 低；需補支援 `DEBUG` alias 並在 `.env.example` 明確標示 |
| ALLOWED_HOSTS 設定來源 | `settings.py` 讀取 `DJANGO_ALLOWED_HOSTS`，預設 `localhost,127.0.0.1` | 低；需補支援 `ALLOWED_HOSTS` alias |
| CSRF middleware 是否啟用 | `django.middleware.csrf.CsrfViewMiddleware` 目前註解，另有 `DisableCSRFMiddleware` 將 `_dont_enforce_csrf_checks=True` | 高；不能直接硬改，需先以文件與後續測試規劃處理 |
| 是否有 `csrf_exempt` | `modules.humnos.views` 有 import，但掃描未見 decorator 實際套用 | 低；建議清理未使用 import，但本階段不動業務邏輯 |
| `SESSION_COOKIE_SECURE` | 目前硬寫 `False` | 中；本機 HTTP 合理，production 應改 `True` |
| `CSRF_COOKIE_SECURE` | 目前硬寫 `False` | 中；本機 HTTP 合理，production 應改 `True` |
| `SESSION_COOKIE_HTTPONLY` | 未明確設定，Django 預設為 `True` | 低；建議明確環境變數化 |
| `CSRF_COOKIE_HTTPONLY` | 目前硬寫 `False` | 低；Django 常見預設為 `False`，方便前端送 CSRF token |
| `SECURE_BROWSER_XSS_FILTER` | 未設定；新版瀏覽器多已淘汰此 header | 低；不建議依賴 |
| `SECURE_CONTENT_TYPE_NOSNIFF` | 未設定 | 中；建議設為 `True` |
| `X_FRAME_OPTIONS` | 有 clickjacking middleware，但未明確設定 | 中；建議設為 `SAMEORIGIN` |
| 上傳檔案處理位置 | `modules.hymns.views.hymn_upload`、`modules.eureka.views.add_view`、CKEditor uploader | 中 |
| 上傳檔案是否限制 size | 未見統一限制 | 中 |
| 上傳檔案是否限制 MIME type | 未見統一檢查 | 中；MIME 容易偽造，第一階段先文件化 |
| 上傳檔名是否清理 | 詩歌 HTM 會清理 title；其他部分以原檔名或固定 id 命名 | 中 |

## 上傳入口

| 入口 | 路徑 | 現況 | 本階段處理 |
| --- | --- | --- | --- |
| 詩歌檔案上傳 | `POST /api/hymns/<id>/upload/` | 支援 `.mp3/.htm/.html/.pdf/.mid/.midi`，目前以副檔名分流 | 套用 size、副檔名與檔名清理 helper |
| 新朋友照片 | `POST /eureka/add/` | 固定存為 `<church_id>.jpg` | 先文件化，不硬改，避免影響新朋友流程 |
| CKEditor 上傳 | `/ckeditor/upload/` | 套件內建 uploader | 先文件化，後續評估套件設定與維護狀態 |

## 風險分級

| 風險 | 項目 | 建議 |
| --- | --- | --- |
| 高 | CSRF middleware 目前被停用 | P5 第二階段建立可開關的 CSRF 復原方案，先在本機測完整登入、admin、上傳與 API |
| 中 | Cookie secure 未 production 化、上傳未統一限制、缺 `nosniff` / `X_FRAME_OPTIONS` 明確設定 | 第一階段先環境變數化與補 helper |
| 低 | DEBUG / ALLOWED_HOSTS 已讀環境變數但 alias 不完整、`csrf_exempt` import 未使用 | 第一階段補 alias，未使用 import 可留待清理 |

## Production 前必查

1. `DEBUG=False` / `DJANGO_DEBUG=0`。
2. `ALLOWED_HOSTS` 或 `DJANGO_ALLOWED_HOSTS` 只允許正式網域與必要 IP。
3. `CSRF_TRUSTED_ORIGINS` 只允許正式 HTTPS origin。
4. `SESSION_COOKIE_SECURE=True`。
5. `CSRF_COOKIE_SECURE=True`。
6. 移除或關閉 `DisableCSRFMiddleware`，恢復標準 CSRF middleware。
7. 上傳目錄不可執行程式，media 應由 web server 安全提供。

## 第一階段已完成

| 項目 | 狀態 |
| --- | --- |
| `DEBUG` / `DJANGO_DEBUG` | 已支援環境變數 |
| `ALLOWED_HOSTS` / `DJANGO_ALLOWED_HOSTS` | 已支援環境變數 |
| `CSRF_TRUSTED_ORIGINS` | 已支援環境變數 |
| `SESSION_COOKIE_SECURE` | 已支援環境變數，本機預設 `False` |
| `CSRF_COOKIE_SECURE` | 已支援環境變數，本機預設 `False` |
| `SESSION_COOKIE_HTTPONLY` | 已支援環境變數，預設 `True` |
| `CSRF_COOKIE_HTTPONLY` | 已支援環境變數，預設 `False` |
| `SECURE_CONTENT_TYPE_NOSNIFF` | 已支援環境變數，預設 `True` |
| `X_FRAME_OPTIONS` | 已支援環境變數，預設 `SAMEORIGIN` |
| `UPLOAD_MAX_SIZE_MB` | 已支援環境變數，預設 `10` |
| `UPLOAD_ALLOWED_EXTENSIONS` | 已支援環境變數，供通用 helper 使用 |
| 詩歌上傳 | 已套用 size、副檔名與檔名基本清理 |
| Eureka 照片上傳 | 只盤點，未硬改 |
| CKEditor 上傳 | 只盤點，未硬改 |
| read-only API tests | 已新增 |

## 第一階段未修改項目

1. 尚未恢復標準 CSRF middleware，避免一次影響登入、admin、CKEditor、詩歌上傳與既有表單。
2. 尚未強制 MIME type 檢查；MIME 第一階段只記錄 TODO，後續應用檔案內容判斷。
3. 尚未變更 Eureka 新朋友照片上傳流程。
4. 尚未變更 CKEditor uploader 設定。

## CSRF 專章

### 掃描結果

| 項目 | 結果 |
| --- | --- |
| `csrf_exempt` | `modules.humnos.views` 有 import，但未見 `@csrf_exempt` 實際使用 |
| `CsrfViewMiddleware` | `settings.py` 中目前註解 |
| `DisableCSRFMiddleware` | 已啟用，會設定 `_dont_enforce_csrf_checks=True` |
| `CSRF_TRUSTED_ORIGINS` | 已環境變數化 |
| HTML 表單 csrf token | `base.html`、`eureka/add.html`、`eureka/neos.html` 可見 `{% csrf_token %}` |
| AJAX CSRF header | `hymns_page.html`、`humnos_page.html` 會送 `X-CSRFToken` |

### Endpoint 風險

| Endpoint | 寫入/敏感性 | 目前 CSRF 狀態 | 風險 | 復原注意事項 |
| --- | --- | --- | --- | --- |
| `/admin/` | 高 | 標準 middleware 被停用，但 Django admin 表單本身有 token | 高 | 第一個復原驗證對象 |
| `/users/create/`、`/users/<id>/...` | 高 | DRF API + 登入/superuser | 高 | 需補 CSRF 或改成 token API 策略 |
| `/api/hymns/` POST/PUT/DELETE/upload | 中高 | AJAX 已送 CSRF header，但 middleware 停用 | 中高 | 可先在本機用 smoke + 上傳測試驗證 |
| `/eureka/add/`、`/eureka/modify/delete/...` | 高 | 表單有 csrf token，但 middleware 停用 | 高 | 需測新朋友登記、刪除流程 |
| `/api/humnos/info/`、`/api/humnos/download/` | 中 | AJAX 已送 CSRF header | 中 | 影音下載依賴外部服務，需 mock 或人工測 |
| `/api/health/` | 低 | GET only | 低 | 不需 CSRF |

### 是否仍必要

目前沒有證據顯示 `DisableCSRFMiddleware` 必須長期保留。較可能是為了快速移植舊系統、讓 AJAX/表單在整合期間先可用。因為它影響所有寫入 endpoint，本階段不直接移除，避免破壞登入、admin、CKEditor、詩歌與 Eureka 表單。

### 建議復原順序

1. 新增環境變數開關，例如 `DISABLE_CSRF_CHECKS=True/False`。
2. 預設本機仍維持現況，新增一套 `CSRF_ENABLED=1` 測試設定。
3. 先讓 `/admin/`、`/api/hymns/`、`/eureka/add/` 的測試覆蓋 CSRF enabled 情境。
4. 確認 AJAX header 與表單 token 都正常後，在本機關閉 `DisableCSRFMiddleware`。
5. 正式部署前才移除或停用 `DisableCSRFMiddleware`。

## CKEditor / CMS / filer 上傳盤點

| 項目 | Endpoint / 來源 | 套件 | Size limit | Extension allowlist | MIME check | 可套 helper | 建議 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| CKEditor 上傳 | `/ckeditor/upload/` | `django-ckeditor` / `ckeditor_uploader` | 未在本 repo 明確設定 | 未在本 repo 明確設定 | 未在本 repo 明確設定 | 不建議直接改第三方內部流程 | 保留但限制使用權限，後續評估套件維護狀態與設定 |
| CMS tables | `cms_*` tables | 舊 Django CMS 殘留資料表 | 不明 | 不明 | 不明 | 不適用 | 多數 0 筆，先保留資料庫相容性，後續評估移除 |
| filer tables | `filer_*` tables | 舊 filer 殘留資料表 | 不明 | 不明 | 不明 | 不適用 | 多數 0 筆，先保留資料庫相容性，後續評估移除 |
| Page content upload | `RichTextUploadingField` | CKEditor uploader | 同 CKEditor | 同 CKEditor | 同 CKEditor | 不建議直接改第三方內部流程 | 先文件化 |

## 第二階段已完成

| 項目 | 狀態 |
| --- | --- |
| CSRF 掃描 | 已完成，未直接復原 middleware |
| Eureka 照片上傳 | 已套用 `upload_validation` helper，限制大小、副檔名與檔名安全；仍保留 `<church_id>.jpg` 儲存規則 |
| MIME 輔助檢查 | 已加入 `mimetypes` 輔助檢查，可用 `UPLOAD_STRICT_MIME_CHECK` 開關 |
| CKEditor/CMS/filer | 只盤點與文件化，未改第三方流程 |
| production env 樣板 | 已新增 `.env.production.example` |
| security tests | 已新增 `tests/security/test_upload_validation.py` 與 `tests/security/test_security_settings.py` |
