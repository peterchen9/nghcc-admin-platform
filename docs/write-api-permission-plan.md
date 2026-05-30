# Write API Permission / CSRF Plan

更新日期：2026-05-30

## 範圍與限制

本階段只盤點與補測試，不部署、不連線、不修改 `.240`，不修改正式權限資料，不改 write API 預設行為，也不新增業務功能。

盤點範圍：

- `/api/hymns/*`
- `/api/humnos/*`
- `/users/*`
- create / update / delete / upload / download 類 API

## 現況摘要

目前 write API 的主要保護邊界是 session 登入與 Django/DRF view 內檢查：

- `/api/hymns/*` write endpoints 使用 DRF `IsAuthenticated`，目前不要求 staff/superuser，也沒有 API 專用 write scope。
- `/api/humnos/download/` 使用 DRF `IsAuthenticated`，目前不要求 staff/superuser，也沒有 API 專用 download scope。
- `/users/*` write endpoints 使用 DRF `IsAuthenticated`，並在 view 內要求 `request.user.is_superuser`。
- CSRF 行為由全站 `ENABLE_CSRF_PROTECTION` 決定；啟用時，session-based POST/PUT/DELETE/upload/download 會受 Django CSRF middleware 影響。
- 前端 AJAX 已在 hymns、humnos、users 頁面帶 `X-CSRFToken`，但目前測試仍應把「無 token 會被拒絕」列為未來移除 compatibility middleware 前的必要證據。

## Write API 盤點矩陣

| Endpoint | Method | 類型 | 是否要求登入 | 是否要求 superuser/staff | CSRF/session 行為 | 建議 API write scope |
| --- | --- | --- | --- | --- | --- | --- |
| `/api/hymns/` | POST | create hymn | 是，`IsAuthenticated` | 否 | Session auth；CSRF 啟用時需 token | `api:hymns:write` |
| `/api/hymns/<pk>/` | PUT | update hymn | 是，`IsAuthenticated` | 否 | Session auth；CSRF 啟用時需 token | `api:hymns:write` |
| `/api/hymns/<pk>/` | DELETE | delete hymn | 是，`IsAuthenticated` | 否 | Session auth；CSRF 啟用時需 token | `api:hymns:write` |
| `/api/hymns/<pk>/upload/` | POST | upload hymn file | 是，`IsAuthenticated` | 否 | Session auth；CSRF 啟用時需 token；另受 upload validation | `api:hymns:upload` |
| `/api/humnos/download/` | POST | download/transcode media | 是，`IsAuthenticated` | 否 | Session auth；CSRF 啟用時需 token；會觸發外部下載與暫存檔 | `api:humnos:write` 或 `api:humnos:download` |
| `/users/create/` | POST | create user | 是，`IsAuthenticated` | 是，superuser | Session auth；CSRF 啟用時需 token | `api:users:write` |
| `/users/<pk>/` | PUT/POST | update user | 是，`IsAuthenticated` | 是，superuser | Session auth；CSRF 啟用時需 token | `api:users:write` |
| `/users/<pk>/permissions/` | POST | update user menu permissions | 是，`IsAuthenticated` | 是，superuser | Session auth；CSRF 啟用時需 token | `api:users:write` |
| `/users/<pk>/delete/` | DELETE/POST | delete user | 是，`IsAuthenticated` | 是，superuser | Session auth；CSRF 啟用時需 token | `api:users:write` |

## 風險摘要

- Hymns write API 目前只要登入即可 create/update/delete/upload；若一般登入帳號不應維護詩歌資料，風險偏高。
- Hymns upload 會寫入 media 檔案並更新 hymn 欄位，應和一般文字 write 分開成 upload scope。
- Humnos download 會觸發 yt-dlp/ffmpeg、暫存檔與串流回應，雖不是業務資料寫入，但屬於高成本 side effect，建議納入 write/download scope。
- Users write API 已要求 superuser，是目前最嚴格的 write API；未來若導入 API scope，應保持 superuser 或等價管理權限。
- CSRF 目前可由 compatibility middleware 關閉；移除前要保留測試證明 session write API 在 CSRF enabled 模式會拒絕無 token request。

## 建議 Scopes

第一階段建議先設計 scope 名稱與對應，不立即改行為：

- `api:hymns:write`：建立、更新、刪除 hymn metadata。
- `api:hymns:upload`：上傳 hymn mp3/html/pdf/midi 檔案；可隱含或要求 `api:hymns:write`。
- `api:humnos:write`：查詢以外的 humnos side-effect API。
- `api:humnos:download`：若要把高成本下載獨立控管，使用此 scope；否則先併入 `api:humnos:write`。
- `api:users:write`：建立、更新、刪除使用者與更新使用者 menu permissions。

## 未來導入順序

1. 新增只讀的 scope 設定與測試資料，不掛上 enforcement。
2. 設計 DRF permission helper，先支援 report-only 或 feature flag。
3. 在 staging/local 以 feature flag 驗證 hymns/humnos/users write scope。
4. 確認 CSRF enabled 測試、smoke tests、write API tests 都通過後，再規劃正式切換。
5. 切換前保留 rollback：關閉 feature flag 即回復目前 session login 行為。

## 本階段測試策略

本階段新增 `tests/security/test_write_api_permissions.py`，只檢查目前行為與未來 scope 設計：

- 確認矩陣涵蓋 create/update/delete/upload/download。
- 確認目前 hymns/humnos write API 仍只要求登入，不新增 superuser/staff enforcement。
- 確認 users write API 仍要求 superuser。
- 確認建議 scope 對應穩定。
- 在 CSRF enabled 模式下，以不會成功寫入的 payload 驗證無 token request 會被拒絕。

本階段不修改正式程式行為。
