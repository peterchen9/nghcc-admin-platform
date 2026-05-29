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
