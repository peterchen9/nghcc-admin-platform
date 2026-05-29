# Menu Permission Enforcement 設計提案

更新日期：2026-05-29

## 目標

釐清 menu permission 是否適合進入 view/API 層。本階段只做設計與 PoC，不改正式權限行為。

## 方案比較

| 方案 | 說明 | 優點 | 缺點 | 風險 | 遷移成本 |
| --- | --- | --- | --- | --- | --- |
| A. 維持現況 | menu permission 主要控制左側選單，現有 middleware 保留 | 風險最低；不影響使用者 | API 與部分 URL 權限仍不一致；規則分散 | 看不到選單但部分 API 可能仍可直接呼叫 | 低 |
| B. menu permission + login_required | 頁面 view 在登入後再檢查 `allowed_menu_items` | 符合 Portal 使用模型；容易理解；可逐頁導入 | 對 API、動態 URL、admin 仍需其他規則 | 若 route mapping 錯誤，可能擋到正常同工 | 中 |
| C. menu permission + Django permission | 頁面入口用 menu permission，資料操作用 Django permission | 層次較完整；可逐步收斂角色 | 需要建立 route-to-permission 對照與測試矩陣 | 遷移期間規則可能重疊或矛盾 | 中高 |
| D. 完全改用 Django permission | 移除 menu permission 授權角色，只保留選單顯示 | 最符合 Django 標準模型 | 需重建所有角色、選單與功能對照；現有 UI 需大改 | 高機率影響既有同工流程 | 高 |

## 建議方案

建議採用 **B 起步，逐步往 C 收斂**。

理由：

1. admin-platform 定位為 Portal + 核心行政查詢平台，menu permission 對頁面入口很直覺。
2. 現有資料已經有 `allowed_menu_items`，使用者管理頁也能維護。
3. 不適合一次把所有功能改成 Django permission，成本與風險都太高。
4. 對寫入 API 與高敏感資料，最終仍應搭配 Django permission 或自訂 DRF permission class。

## 建議遷移順序

1. 保持 `ENABLE_MENU_PERMISSION_ENFORCEMENT=False`。
2. 只在測試中驗證 `menu_permission_required(route)` 行為。
3. 選一個低風險 read-only 頁面建立人工測試清單。
4. 若要實際套用，先在本機針對單一路由打開，確認不影響 superuser、一般同工與缺權限使用者。
5. API 層不要直接套用頁面 route 規則，需另設計 `MenuPermissionAPIView` 或 route-to-api 對照。

## 不建議事項

- 不建議全面套用到 `/api/*`。
- 不建議把 `roles` 欄位當作正式授權來源，因目前多為 `*`。
- 不建議一次移除 `MenuPermissionMiddleware`。
- 不建議直接把 menu permission 視為 Django permission 的替代品。
