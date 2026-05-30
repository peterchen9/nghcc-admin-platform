# Menu Permission 單一路由人工測試清單

更新日期：2026-05-30

## 範圍

本清單只驗證 `/webav/` page route 的 menu permission 試行。不測 `/api/humnos/*`，不修改 DB 權限資料，不部署、不連線、不修改 `.240`。

## 前置條件

- 本機服務已啟動，且使用本機還原資料。
- `.env` 預設保持 `ENABLE_MENU_PERMISSION_ENFORCEMENT=False`。
- 測試帳號至少包含：
  - superuser
  - 有 `/webav/` allowed menu item 的一般登入使用者
  - 沒有 `/webav/` allowed menu item 的一般登入使用者

若本機資料缺少其中一種帳號，不直接改 DB。請先記錄缺口，等後續建立測試 fixture 或由管理介面準備可回復的測試帳號。

## 預設關閉驗證

| 步驟 | 帳號 | 操作 | 預期結果 |
| --- | --- | --- | --- |
| 1 | 未登入 | 開啟 `/webav/` | 導向登入或被拒絕 |
| 2 | superuser | 開啟 `/webav/` | HTTP 200，頁面可開 |
| 3 | 有 `/webav/` menu permission 的一般使用者 | 開啟 `/webav/` | HTTP 200，頁面可開 |
| 4 | 沒有 `/webav/` menu permission 的一般使用者 | 開啟 `/webav/` | 因旗標關閉，維持既有登入後可開行為 |

## 本機試行開啟驗證

只在本機暫時設定：

```bash
ENABLE_MENU_PERMISSION_ENFORCEMENT=True
```

| 步驟 | 帳號 | 操作 | 預期結果 |
| --- | --- | --- | --- |
| 1 | 未登入 | 開啟 `/webav/` | 導向登入或被拒絕 |
| 2 | superuser | 開啟 `/webav/` | HTTP 200，頁面可開 |
| 3 | 有 `/webav/` menu permission 的一般使用者 | 開啟 `/webav/` | HTTP 200，頁面可開 |
| 4 | 沒有 `/webav/` menu permission 的一般使用者 | 開啟 `/webav/` | HTTP 403 或 permission denied |
| 5 | 任一登入使用者 | 開啟 `/hymns/` | 不因本試行改動而改變既有行為 |
| 6 | 任一登入使用者 | 開啟 `/eureka/` | 不因本試行改動而改變既有行為 |

## 回復確認

測試完成後恢復：

```bash
ENABLE_MENU_PERMISSION_ENFORCEMENT=False
```

重新開啟 `/webav/`，確認登入後頁面行為回到既有狀態。

## 通過標準

- 旗標關閉時，所有既有 smoke test 與 security test 通過。
- 旗標開啟時，只有 `/webav/` page route 受到 menu permission 影響。
- `/api/humnos/*`、`/hymns/`、`/eureka/` 未被本次試行擴大套用。
