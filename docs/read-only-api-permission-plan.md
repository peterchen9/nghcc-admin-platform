# Read-only API Permission Plan

更新日期：2026-05-30

## 目標與限制

本階段只針對 `/api/hymns/*` 與 `/api/humnos/*` 設計 read-only API 權限策略，並補上測試與可讀的矩陣資料。限制如下：

- 不部署、不連線、不修改 `.240`。
- 不修改正式 user/group/permission/menu 資料。
- 不全面套用 menu permission。
- 不改 write API 行為。
- 不新增業務功能。

## 設計原則

1. Read-only API 的最低門檻是登入，也就是目前 DRF `IsAuthenticated` 的行為。
2. Read-only API 不直接沿用 page route 的 menu permission。`/hymns/` 與 `/webav/` 的選單可見性只代表 UI 入口，不等於 `/api/*` 的 API 授權。
3. 若未來要加強 read-only API，應建立 API 專用規則，例如 `api:hymns:read`、`api:humnos:read`，或再評估 Django `view_*` permission；不要把 page route 字串直接映射成 API 權限。
4. Write API 在本階段維持現狀，只盤點風險，不變更行為。
5. `/api/humnos/info/` 雖然使用 POST，但以本機業務資料效果分類為 read-only lookup；它會查詢外部影音資訊，但不寫入本機正式資料。

## Endpoint 盤點

| Endpoint | Method | 分類 | 目前用途 | 需要登入 | 需要 menu permission | 需要 Django permission | 本階段決策 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `/api/hymns/` | GET | read-only | 詩歌列表、搜尋、分頁 | 是，`IsAuthenticated` | 否 | 否 | 維持登入即可；未來可另設 API read permission |
| `/api/hymns/<pk>/` | GET | read-only | 詩歌明細 | 是，`IsAuthenticated` | 否 | 否 | 維持登入即可；未來可另設 API read permission |
| `/api/humnos/info/` | POST | read-only | 查詢外部影音 metadata | 是，`IsAuthenticated` | 否 | 否 | 視為 read-only API；不沿用 `/webav/` menu permission |
| `/api/hymns/` | POST | write | 新增詩歌 | 是，`IsAuthenticated` | 否 | 暫不新增 | 本階段不改 |
| `/api/hymns/<pk>/` | PUT | write | 編輯詩歌 | 是，`IsAuthenticated` | 否 | 暫不新增 | 本階段不改 |
| `/api/hymns/<pk>/` | DELETE | write | 刪除詩歌 | 是，`IsAuthenticated` | 否 | 暫不新增 | 本階段不改 |
| `/api/hymns/<pk>/upload/` | POST | write | 上傳詩歌相關檔案並更新資料 | 是，`IsAuthenticated` | 否 | 暫不新增 | 本階段不改 |
| `/api/humnos/download/` | POST | write/side-effect | 下載外部影音並產生暫存檔回傳 | 是，`IsAuthenticated` | 否 | 暫不新增 | 本階段不改 |

## 建議 Enforcement 規則

### Phase A：目前可安全落地的規則

- 所有 `/api/hymns/*` 與 `/api/humnos/*` endpoint 皆維持 `IsAuthenticated`。
- Read-only API 不檢查 page route menu permission。
- Write API 不在本階段改授權、不加 Django permission、不改 CSRF 或 request 行為。
- 以 `tests/security/test_read_only_api_permissions.py` 固定目前邊界：anonymous 不可讀；登入者即使沒有 page menu permission，仍可讀 read-only API。

### Phase B：後續加強選項

若 read-only API 要進一步細分授權，建議使用 API 專用 permission，而非 page route menu permission：

| API scope | 適用 endpoint | 可選實作 |
| --- | --- | --- |
| `api:hymns:read` | `/api/hymns/` GET、`/api/hymns/<pk>/` GET | 自訂 DRF permission 或群組/設定表 |
| `api:humnos:read` | `/api/humnos/info/` POST | 自訂 DRF permission 或群組/設定表 |

Django model permission 可作為第二候選，但需先確認 legacy `hymns` model 權限資料是否完整且能表達 read-only API 語意。menu permission 保留為 UI visibility，不作為 API 授權來源。

## 本階段程式碼範圍

新增 `tests/security/test_read_only_api_permissions.py` 內的設計矩陣 helper，只提供測試與文件可引用的靜態資料，不接入 view、middleware、settings 或正式 request path，因此不改預設正式行為。

## 測試策略

新增 `tests/security/test_read_only_api_permissions.py`：

- 驗證 helper 矩陣完整列出 hymns/humnos read/write endpoint。
- 驗證 read-only endpoint 都要求登入，且不要求 menu permission 或 Django permission。
- 驗證 anonymous 不能讀 `/api/hymns/`。
- 驗證沒有 `/hymns/` menu permission 的測試帳號仍可讀 `/api/hymns/`，固定「read-only API 不直接沿用 page route menu permission」。
- 以 monkeypatch 隔離 `yt_dlp`，驗證登入者可呼叫 `/api/humnos/info/`，anonymous 不可呼叫；不連外、不下載、不寫正式資料。

## 下一步建議

1. 先人工確認 `api:hymns:read` 與 `api:humnos:read` 是否需要比「登入即可」更嚴。
2. 若需要加強，先做 feature flag 或 DRF permission helper，預設關閉。
3. 針對 write API 另開階段盤點 create/update/delete/upload/download 的角色與 CSRF/session 行為，不與 read-only API 混在同一次變更。
