# View/API Enforcement Matrix

更新日期：2026-05-30

## 範圍與原則

本文件整理目前 middleware、`login_required`、staff/superuser、menu permission helper、URL access tests 的重疊邊界，作為 P2 後續小步補強依據。

本階段只整理 enforcement matrix，不部署、不連線、不修改 `.240`，不修改正式權限資料，不全面套用 menu permission，也不新增業務功能。

## 現況邊界摘要

| 機制 | 目前用途 | 涵蓋範圍 | 邊界 |
| --- | --- | --- | --- |
| anonymous/public | Portal 首頁、公開頁、health check | `/`, `/p/<slug>/`, `/api/health/` | 不應放入會員資料、詩歌檔案、管理資料 |
| `login_required` | 頁面與資源 URL 的最低登入門檻 | `/hymns/`, `/webav/`, `/eureka/*`, `/hymn_resources/htm/*` | 只確認已登入，不代表有功能選單或資料操作權限 |
| DRF `IsAuthenticated` | API 的最低登入門檻 | `/api/hymns/*`, `/api/humnos/*`, `/users/*` API 起點 | 詩歌/影音 API 尚未做細部 menu/Django permission |
| staff/superuser | Django admin 與高敏感管理功能 | `/admin/`, `/users/*`, `/pages/edit-home/` | 與 menu permission 分離，menu 可見不代表 superuser |
| `MenuPermissionMiddleware` | 對部分登入後 app path 做 route 比對 | 非 `/api/*`、非 `/users/*`、非 admin/static/media 等排除路徑 | 不是一致 view/API 授權模型；動態 API 與高敏感管理需另有規則 |
| `menu_permission_required(route)` | 實驗性 helper | 目前僅 PoC，預設由 `ENABLE_MENU_PERMISSION_ENFORCEMENT=False` 關閉 | 不應直接全面套用；需逐 route 測試 |
| Django permission | Django admin/CMS/filer 既有 permission | admin 與套件模型層 | 目前未與 menu item 建立一對一對照 |
| CSRF | POST/form/AJAX 防護 | 測試模式可啟用 Django `CsrfViewMiddleware`；部分 AJAX 已補 header | 正式啟用前仍需全流程人工測試 |

## 建議 Enforcement Matrix

狀態標記：

- 已符合：目前程式或測試已覆蓋此階段建議。
- 待補強：後續可小步補測試、人工驗證或設計細部規則。
- 暫不處理：本階段不建議套用，避免改壞既有流程。

| 分類 | 代表 URL | anonymous | login_required | staff/superuser | menu permission | Django permission | CSRF | 目前狀態 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Page View | `/hymns/`, `/webav/`, `/eureka/` | 應拒絕 | 建議必要 | 一般不需要，除管理頁 | 建議採 B：登入後逐頁評估；先從低風險 read-only 頁面試行 | 暫不作為頁面入口主要規則 | GET 不需；頁面內 POST/form 需 token | `login_required` 已符合；menu permission 逐頁試行待補強 |
| Read-only API | `/api/hymns/` GET、`/users/routes/` GET | 應拒絕，health check 例外 | 建議必要 | 使用者管理 API 需 superuser | 一般 API 不直接套 page route；需另設 route-to-api 對照 | 待評估是否需要 model/read permission | GET 不需 CSRF | `IsAuthenticated` 已符合最低門檻；細部 API 權限待補強 |
| Write API | `/api/hymns/` POST、`/api/hymns/<id>/` PUT/DELETE、`/api/humnos/download/` | 應拒絕 | 建議必要 | 視資料敏感度；使用者管理必須 superuser | 不建議直接沿用 page route；需設計 API 專用規則 | 建議逐步往 Django permission 或自訂 DRF permission 收斂 | 必須有 CSRF token 或等效 API 防護 | 登入與部分 AJAX header 已符合；細部權限與 CSRF 正式啟用待補強 |
| Resource URL | `/hymn_resources/htm/*`, `/eureka/photo/*`, `/media/*` | 詩歌 HTM 與會員照片應拒絕；公開 media 需依用途 | 建議必要，除明確公開資源 | 一般不需要 | 待評估是否與所屬功能選單綁定 | 暫不處理，除資源轉入模型授權 | GET 不需 CSRF | HTM resource 已補登入限制；menu 綁定暫不處理 |
| Admin/User Management | `/admin/`, `/users/*`, `/pages/edit-home/` | 應拒絕 | 建議必要 | 必須 staff 或 superuser；使用者管理實質限 superuser | 只能作為 UI 可見性，不可取代 superuser | Django admin 保留內建 permission；使用者管理目前用自訂 superuser | 寫入必須有 CSRF token | superuser/staff 邊界已符合；正式 CSRF 開關與人工測試待補強 |

## 分類細節

### Page View

建議規則：

- anonymous：核心功能頁應 redirect 或 forbidden。
- `login_required`：作為所有核心 page view 的最低門檻。
- staff/superuser：僅用於管理頁或高敏感頁，不套到一般詩歌、影音、Eureka 入口。
- menu permission：適合採「B. menu permission + login_required」逐頁試行，不全面套用。
- Django permission：暫不作為頁面入口主規則。
- CSRF：GET 頁不需；頁面內表單與 AJAX POST 需 token。

目前狀態：

- 已符合：`/hymns/`、`/webav/`、`/eureka/` 皆有登入門檻，URL access tests 已覆蓋匿名拒絕與登入可用。
- 待補強：低風險 read-only page route 可用人工清單驗證 menu permission 試行。
- 暫不處理：不全面把 menu permission 套到全部 page view。

### Read-only API

建議規則：

- anonymous：除 `/api/health/` 外應拒絕。
- `login_required` / `IsAuthenticated`：作為最低門檻。
- staff/superuser：只套高敏感管理 API，例如 `/users/routes/`。
- menu permission：不要直接套 page route；若需要，先建立 API route 對照。
- Django permission：後續可評估 read-only model permission，但本階段不改。
- CSRF：GET 不需。

目前狀態：

- 已符合：`/api/hymns/` 匿名拒絕、登入可讀；`/users/routes/` 需 superuser。
- 待補強：詩歌與影音 read-only API 尚未形成細部 menu/Django permission 對照。
- 暫不處理：本階段不將 menu permission 全面套入 `/api/*`。

### Write API

建議規則：

- anonymous：必須拒絕。
- `login_required` / `IsAuthenticated`：必須。
- staff/superuser：使用者管理必須；詩歌、影音、Eureka 寫入需另評估資料敏感度。
- menu permission：不可直接用左側選單可見性取代資料操作權限。
- Django permission：較適合作為未來寫入權限收斂方向，或建立自訂 DRF permission class。
- CSRF：在 session auth/AJAX 模式下必須送 `X-CSRFToken` 或表單 token。

目前狀態：

- 已符合：主要寫入 API 至少要求登入；使用者管理 API 後端實質限 superuser；部分 AJAX 已補 `X-CSRFToken`。
- 待補強：正式啟用 CSRF middleware 前需完成 smoke、CSRF tests 與人工測試；詩歌/影音/Eureka 寫入仍需細部權限策略。
- 暫不處理：不新增業務權限，不修改既有資料操作流程。

### Resource URL

建議規則：

- anonymous：只允許明確公開資源。
- `login_required`：詩歌 HTM resource、Eureka photo 等相容資源應至少登入。
- staff/superuser：通常不需要，除資源屬管理資料。
- menu permission：是否綁所屬功能選單需後續人工驗證，避免擋到既有連結或嵌入頁。
- Django permission：資源 URL 目前多非模型授權入口，本階段暫不導入。
- CSRF：GET resource 不需。

目前狀態：

- 已符合：`/hymn_resources/htm/<filename>` 已補 `@login_required`。
- 待補強：Eureka photo 與其他資源 URL 需保持登入檢查與人工測試。
- 暫不處理：不把所有 resource URL 一次改成 menu permission 或 Django permission。

### Admin/User Management

建議規則：

- anonymous：必須拒絕。
- `login_required`：必須。
- staff/superuser：Django admin 需 staff/admin permission；本系統使用者管理與首頁編輯實質限 superuser。
- menu permission：只作為 UI 可見性或輔助，不可取代 superuser。
- Django permission：admin 保留內建 permission；自訂使用者管理若要細分，需另設計，不在本階段。
- CSRF：所有寫入必須 token。

目前狀態：

- 已符合：`/users/*` 後端檢查 superuser，`/admin/` 有 staff/admin permission 且 middleware 會阻擋非 superuser 進 admin。
- 待補強：正式 CSRF 開關啟用前需完整人工測使用者新增、修改、刪除與權限更新。
- 暫不處理：不改正式使用者、群組、Django permission 或 menu permission 資料。

## 測試對照

| 測試 | 覆蓋內容 |
| --- | --- |
| `tests/security/test_permission_visibility.py` | 匿名不可進核心頁與使用者管理 URL；登入可進核心頁 |
| `tests/security/test_permission_matrix.py` | superuser、staff、一般使用者、anonymous 的 login/menu/staff/superuser 邊界 |
| `tests/security/test_menu_permission_strategy.py` | `menu_permission_required()` 預設關閉與開啟後的 PoC 行為 |
| `tests/security/test_user_ajax_csrf.py` | 使用者管理頁與 AJAX CSRF header |
| `tests/security/test_csrf_behavior.py` | `ENABLE_CSRF_PROTECTION` 開關與 CSRF middleware 行為 |

## 後續建議

1. 維持 `ENABLE_MENU_PERMISSION_ENFORCEMENT=False`，不要全面套用 menu permission。
2. 先用 `/webav/` 或另一個低風險 read-only page route 做人工驗證清單。
3. 針對 `/api/hymns/*`、`/api/humnos/*` 分開設計 read/write API permission，不直接沿用 page route。
4. 使用者管理維持 superuser 為主，menu permission 只控制可見性。
5. CSRF 正式啟用前，先完成 scripts 與人工流程驗證。
