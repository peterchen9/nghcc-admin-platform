# Menu Permission 使用方式分析

更新日期：2026-05-29

## 範圍

本文件分析本機 `nghcc-admin-platform` 的 menu permission 使用方式，不修改 `.240`，不改 DB 權限資料，不做權限重構。

## 資料模型

| 項目 | 位置 | 說明 |
| --- | --- | --- |
| 選單項目 | `modules.menu.models.MenuItem` / `menu_menuitem` | 左側選單節點，包含 `title`、`route`、`parent`、`roles`、`is_active` |
| 使用者選單授權 | `UserProfile.allowed_menu_items` / `accounts_userprofile_allowed_menu_items` | 使用者可看見的選單項目 |
| Django permission | `auth_permission` | Django model/action 權限，與 `MenuItem` 沒有直接欄位關聯 |
| 群組權限 | `auth_group_permissions` | 目前主要是 `管理員` 群組的大包權限 |
| 使用者直接權限 | `auth_user_user_permissions` | 部分使用者直接綁定大量 Django permissions |

## 現有使用方式

### 1. menu permission 現在只是控制選單嗎？

不完全是。左側選單顯示確實由 `modules.menu.context_processors.menu_processor` 依 `UserProfile.allowed_menu_items` 控制；但系統同時有 `nads26.middleware.MenuPermissionMiddleware`，會對部分登入後的頁面路徑做 menu permission 檢查。

現況可分為：

- 左側選單：依 `allowed_menu_items` 控制可見性。
- middleware：對部分 app page route 做檢查，例如 `/hymns/`、`/webav/`、`/eureka/` 這類有對應 `MenuItem.route` 的路徑。
- API：多數 `/api/*` 不會被目前 route matching 覆蓋。
- `/users/*`：middleware 明確跳過，交由 view 內 superuser 檢查。

### 2. 是否已被 view 使用？

沒有看到 view function 或 decorator 直接讀取 `allowed_menu_items`。目前 view 層常見的是：

- `@login_required`
- DRF `IsAuthenticated`
- 自訂 `is_superuser` 檢查

本階段新增的 `nads26.menu_permissions.menu_permission_required()` 是實驗性 helper，預設關閉，未套用到正式 view。

### 3. 是否已被 API 使用？

沒有。`/api/hymns/*`、`/api/humnos/*` 主要使用 DRF `IsAuthenticated`。目前 menu permission 沒有在 API permission class 中被一致套用。

### 4. 是否適合作為存取控制？

適合做「輔助存取控制」，但不適合直接取代 Django permission。

適合的原因：

- 已有資料表與管理 UI。
- 使用者管理頁已可設定 `allowed_menu_items`。
- 對 Portal 型系統，選單與頁面入口高度相關。

限制：

- `MenuItem.route` 是字串比對，對 API、動態 URL、同一路徑多方法不夠精確。
- `roles` 欄位目前多為 `*`，未實際作為授權規則。
- Django admin、使用者管理、CMS/CKEditor 等功能不適合只靠 menu permission。
- 若直接全面套用，可能造成同工看不到或打不開原本可用的功能。

### 5. 與 Django permission 是否重疊？

部分重疊，但不是同一層概念。

| 權限類型 | 粒度 | 適用範圍 |
| --- | --- | --- |
| Menu permission | 頁面/功能入口 | Portal 左側選單、前台功能頁 |
| Django permission | model/action | Django admin、資料模型 CRUD、套件權限 |
| superuser/staff | 管理身份 | 使用者管理、admin、系統設定 |

結論：menu permission 不應直接取代 Django permission；較合理做法是先在低風險頁面作為 `login_required` 後的第二層檢查。

## 本階段 PoC

新增：

- `ENABLE_MENU_PERMISSION_ENFORCEMENT=False`
- `nads26.menu_permissions.user_has_menu_route()`
- `nads26.menu_permissions.menu_permission_required()`
- `tests/security/test_menu_permission_strategy.py`

PoC 預設關閉，不套用正式 view，不改現有行為。測試用假使用者與假 view 驗證：

- enforcement 關閉時維持現況。
- enforcement 開啟時，有 menu permission 才能通過。
- superuser 可通過。
- 不存在的 route 不允許一般使用者。
