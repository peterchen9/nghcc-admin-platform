# 權限測試帳號矩陣

更新日期：2026-05-30

## 目的

本矩陣定義 P2 第五階段使用的本機測試帳號。這些帳號只用於 `nghcc-admin-platform` 本機 Docker Compose 環境，可重複建立與刪除，不得套用到 `.240`、正式帳號或正式權限資料。

## 安全邊界

- 只操作本機 Docker Compose 的 `web` / `db` service。
- 不連線、不部署、不修改 `.240`。
- 不修改正式帳號、正式權限資料或正式業務資料。
- 只管理固定測試帳號名稱：`test_superuser`、`test_staff_menu`、`test_staff_nomenu`、`test_user`。
- 刪除腳本只刪除上述固定測試帳號。

## 帳號矩陣

| 矩陣角色 | 本機帳號 | Django flags | Menu permission | 預期可做 | 預期不可做 |
| --- | --- | --- | --- | --- | --- |
| superuser | `test_superuser` | `is_active=True`, `is_staff=True`, `is_superuser=True` | 視為全部允許 | 進入 `/admin/`、讀取 `/users/routes/`、進入 `/users/`、通過 `/webav/` menu permission | 無本階段限制案例 |
| staff_with_menu | `test_staff_menu` | `is_active=True`, `is_staff=True`, `is_superuser=False` | 指派全部 active menu items | 通過本機核心選單頁面、在 menu enforcement 開啟時進入 `/webav/` | 讀取 `/users/routes/`、進入 `/users/` |
| staff_without_menu | `test_staff_nomenu` | `is_active=True`, `is_staff=True`, `is_superuser=False` | 不指派 menu item | 進入 `/admin/` | 在 menu enforcement 開啟時進入 `/webav/`、讀取 `/users/routes/`、進入 `/users/` |
| normal_user | `test_user` | `is_active=True`, `is_staff=False`, `is_superuser=False` | 不指派 menu item | 通過一般 `login_required` API 登入檢查，例如 `/api/hymns/` | 進入 `/admin/`、讀取 `/users/routes/`、進入 `/users/`、在 menu enforcement 開啟時進入 `/webav/` |
| anonymous | 不建立帳號 | 未登入 | 無 | 讀取公開 endpoint，例如 `/api/health/` | 進入 `login_required` 頁面、staff-only、superuser-only、menu-protected 頁面 |

## 建立與刪除

Linux / Git Bash / WSL2：

```bash
scripts/create-test-accounts.sh
scripts/remove-test-accounts.sh
```

PowerShell：

```powershell
.\scripts\create-test-accounts.ps1
.\scripts\remove-test-accounts.ps1
```

預設密碼為 `local-test-password-12345`，可用 `TEST_ACCOUNT_PASSWORD` 覆蓋。建立腳本會重設上述測試帳號的密碼與 flags，並重新套用 menu permission，使結果可重複。

## 測試覆蓋

`tests/security/test_permission_matrix.py` 驗證：

- `/webav/` menu permission enforcement。
- `login_required` 對匿名與登入帳號的差異。
- `/admin/` staff required。
- `/users/` 與 `/users/routes/` superuser required。
