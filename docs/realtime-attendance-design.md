# 通訊錄即時出席計算設計紀錄

日期：2026-06-06

## 背景

通訊錄原本顯示的出席狀態直接讀取 `members` 表內的預先彙總欄位：

- `members.data_str`
- `members.percent_year`
- `members.percent_12_month`
- `members.first_daka`

這些欄位由 `backend/scripts/sync_attendance_from_datacenter.py` 從外部 `datacenter.daka_by_person` 同步而來。`daka_by_person` 已經是彙總結果，不是原始每週報到資料，因此當彙總邏輯錯誤或同步延遲時，通訊錄畫面會顯示錯誤百分比。

## 新設計

通訊錄出席狀態改為以本機 `checkin_records` 原始報到紀錄即時計算。

目前採用的源頭資料：

- 表：`checkin_records`
- 欄位：`church_id`, `timestamp`, `raw_id`, `device_id`
- 一人同一天多次報到只算一次。
- 只將週日且當天至少 50 位不同會員報到的日期視為主日聚會週。

## 計算規則

- 每週方塊：取最近 52 個有效主日聚會週。
- 年度百分比：該會員在該年度有效主日聚會週的出席週數 / 該年度有效主日聚會週總數。
- 搜尋列表摘要：顯示最近 3 個有資料年份的年度百分比。
- 詳細頁年度圖：顯示所有有資料年份。
- 舊欄位 `members.percent_year`, `members.percent_12_month`, `members.data_str` 不再作為畫面出席狀態來源。

## 目前邊界

`checkin_records` 目前沒有聚會類型欄位，因此先以「週日 + 人數門檻」識別主日聚會。若活石條碼系統可提供更完整源頭資料，建議後續直接同步或查詢以下原始欄位：

- 會員編號
- 報到時間
- 聚會或活動類型
- 報到來源或設備
- 是否補登
- 原始掃碼紀錄 ID

有了聚會類型後，可移除週日與人數門檻推斷，改用明確的主日聚會資料。

## 相關程式

- `backend/modules/eureka/attendance.py`
- `backend/modules/eureka/models.py`：`CheckinRecord` 對應既有 `checkin_records` 表，`managed = False`
- `backend/modules/eureka/views.py`
- `backend/templates/eureka/eureka.html`
- `tests/smoke/test_members.py`

## 2026-06-06 後續調整

已新增 `CheckinRecord` unmanaged Django model，讓即時計算服務透過 ORM 讀取 `checkin_records`。資料表仍由既有 DB 管理，不由 Django migration 建表或改 schema。

`checkin_records.timestamp` 目前按資料庫原始本地時間解讀。ORM 查詢刻意使用 MySQL `DATE(timestamp)`、`YEAR(timestamp)`、`DAYOFWEEK(timestamp)`，避免 Django timezone conversion 將週日晚間報到轉成週一凌晨而排除有效主日。

## 後續核對

第 1、2 項抽樣核對與活石條碼/Datacenter 源頭盤點紀錄於 `docs/attendance-source-audit-2026-06-06.md`。
