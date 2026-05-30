# API Permission Report-only Reporting

更新日期：2026-05-30

## 範圍

本文件記錄 `API_PERMISSION_MODE=report-only` 的 log 格式。此階段只整理本機 report-only 記錄格式，不部署、不連線、不修改 `.240`，不修改正式權限資料，不啟用 `enforce`，也不改預設 API 行為。

## Log 格式

logger：`nads26.api_permissions`

message prefix：`api_permission_report`

欄位：

| 欄位 | 說明 |
| --- | --- |
| `mode` | API permission 模式，report-only 階段應為 `report-only` |
| `endpoint` | decorator 宣告的 endpoint pattern，例如 `/api/hymns/` |
| `method` | HTTP method，例如 `GET`、`POST`、`PUT`、`DELETE` |
| `scope` | 此 endpoint/method 對應的 scope，例如 `api:hymns:write` |
| `user_id` | Django user id；匿名或無 user 時為空值 |
| `user_authenticated` | request user 是否已登入 |
| `user_is_superuser` | request user 是否為 superuser |
| `decision` | 權限計算結果：`allow` 或 `deny` |
| `reason` | decision 原因 |

目前可能的 `reason`：

| reason | 說明 |
| --- | --- |
| `superuser` | superuser 會被未來 enforcement hook 視為允許 |
| `explicit_scope` | user 物件具備對應 `api_scopes` |
| `missing_scope` | 已登入但沒有對應 API scope |
| `anonymous_user` | 未登入或沒有 authenticated user |
| `missing_scope_mapping` | endpoint/method 沒有對應 scope |

範例：

```text
api_permission_report mode=report-only endpoint=/api/hymns/ method=POST scope=api:hymns:write user_id=123 user_authenticated=True user_is_superuser=False decision=deny reason=missing_scope
```

## 敏感資料原則

Report-only log 不記錄 request body、query string、headers、cookies、session id、CSRF token、password、token、檔案內容或原始 payload。可觀測性只依賴 endpoint pattern、method、scope 與 user id 等授權判斷必要欄位。

`tests/security/test_api_permission_feature_flag.py` 會驗證敏感 request data 不會出現在 report-only log message。

## 行為界線

- `API_PERMISSION_MODE=off` 仍為預設值，decorator 直接放行且不記錄 permission decision。
- `API_PERMISSION_MODE=report-only` 只記錄，不阻擋 request。
- `API_PERMISSION_MODE=enforce` 保留未來入口，本階段不啟用、不部署、不測正式阻擋流程。
