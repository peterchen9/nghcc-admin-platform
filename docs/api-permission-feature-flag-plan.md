# API Permission Report-only / Feature Flag Plan

建立日期：2026-05-30

## 目標與限制

本階段只建立 API scope feature flag 與 report-only 骨架，不部署、不連線、不修改 `.240`，不修改正式權限資料，不改預設 API 行為，也不新增業務功能。

`API_PERMISSION_MODE` 支援三種模式：

| Mode | 行為 |
| --- | --- |
| `off` | 完全不檢查、不記錄 permission decision。這是預設值。 |
| `report-only` | 計算 endpoint 需要的 scope 並寫入 log，但不阻擋 request。 |
| `enforce` | 未來才啟用。缺少 scope 時回傳 403。此階段不啟用。 |

## 環境變數

```env
API_PERMISSION_MODE=off
```

允許值為 `off`、`report-only`、`enforce`。未知值會保守回到 `off`，避免設定錯誤改變既有行為。

## Helper / Skeleton

新增 `nads26.api_permissions`：

- `get_api_permission_mode()`：讀取並驗證 `API_PERMISSION_MODE`。
- `api_permission_enabled()`：判斷是否進入 API permission skeleton。
- `api_permission_required(scope_by_method, endpoint)`：DRF function view decorator。
- `user_has_api_scope(user, scope)`：未來 enforcement 的 scope 判斷入口。
- `API_PERMISSION_SCOPE_MAP`：集中列出 `/api/hymns/*` 與 `/api/humnos/*` scope mapping。

在 `off` 模式 decorator 直接放行。在 `report-only` 模式只寫 log 後放行。在 `enforce` 模式的阻擋行為已保留為未來入口，但本階段不設定、不測為啟用狀態。

## Scope Mapping

| Endpoint | Method | Scope |
| --- | --- | --- |
| `/api/hymns/` | GET | `api:hymns:read` |
| `/api/hymns/` | POST | `api:hymns:write` |
| `/api/hymns/<pk>/` | GET | `api:hymns:read` |
| `/api/hymns/<pk>/` | PUT | `api:hymns:write` |
| `/api/hymns/<pk>/` | DELETE | `api:hymns:write` |
| `/api/hymns/<pk>/upload/` | POST | `api:hymns:upload` |
| `/api/humnos/info/` | POST | `api:humnos:read` |
| `/api/humnos/download/` | POST | `api:humnos:write` |

`api:humnos:download` 仍保留為未來可拆分 scope；本階段先以既有 write/side-effect 分類使用 `api:humnos:write`。

## Test Strategy

新增 `tests/security/test_api_permission_feature_flag.py`，驗證：

- 預設 mode 是 `off`。
- `report-only` 可被辨識且只進入記錄模式。
- 非法 mode 回到 `off`。
- hymns/humnos scope mapping 完整。
- `off` 不改 hymns write API 既有回應。
- `report-only` 不改 hymns write API 既有回應且會記錄 scope。
- `off` 與 `report-only` 不改 humnos API 既有錯誤回應。

## 下一步

1. 設計正式 scope 儲存來源，例如 user profile、group role、或獨立 API scope table。
2. 建立更完整的 report-only log dashboard 或 log query checklist。
3. 在本機與 staging-like 測試資料確認 report-only 無誤後，再另案討論 `enforce`。
