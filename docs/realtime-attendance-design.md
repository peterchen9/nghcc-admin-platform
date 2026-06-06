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

即時計算服務加入 5 分鐘 in-process cache，只快取有效主日日期清單。會員個別出席日期仍即時從 `checkin_records` 查詢，避免搜尋不同會員時拿到過期個人資料。

已在 2026-06-06 取得 schema 變更窗口後新增出席查詢索引：

```sql
CREATE INDEX idx_checkin_timestamp_church_id ON checkin_records (timestamp, church_id);
CREATE INDEX idx_checkin_church_id_timestamp ON checkin_records (church_id, timestamp);
```

同步工具也會在 `--apply` 時確認上述索引與 `checkin_records_raw_id_idx` 存在，避免大量同步或即時計算退回全表掃描。

## 後續核對

第 1、2 項抽樣核對與活石條碼/Datacenter 源頭盤點紀錄於 `docs/attendance-source-audit-2026-06-06.md`。

## 活石條碼 SQLite 源頭

後續已確認活石條碼使用 SQLite，不使用 MySQL。真正報到源頭為 `/home/peterchen/living_stone_barcode/nghc_daka/db.sqlite3` 的 `check_in_checkinrecord` 表。

admin-platform 本機 `checkin_records.raw_id` 可對應活石條碼 `check_in_checkinrecord.id`，但本機既有 `timestamp` 比活石條碼 `t_check_in` 多 16 小時。這代表目前本機資料仍有舊匯入偏移問題；必須先備份 MySQL，再用 `scripts/sync_checkins_from_living_stone_sqlite.py --apply` 修正既有資料並補入 2026 報到紀錄。
## 2026-06-06 required fix completion

Attendance data is now synced from Living Stone Barcode SQLite into local `checkin_records`.

Applied source:

- Remote SQLite: `/home/peterchen/living_stone_barcode/nghc_daka/db.sqlite3`
- Table: `check_in_checkinrecord`
- Mapping: source `id` -> local `checkin_records.raw_id`
- Mapping: source `t_check_in` -> local `checkin_records.timestamp`

Local database state after apply:

```text
checkin_records total=130306
first_ts=2020-12-04 06:06:44
last_ts=2026-05-21 08:13:59
raw_ids=130306
```

Attendance summary verification examples:

```text
7    2024:94% 2025:71% 2026:50% latest=2026-05-17 blocks=52
9    2024:85% 2025:83% 2026:75% latest=2026-05-17 blocks=52
10   2024:73% 2025:52% 2026:90% latest=2026-05-17 blocks=52
2    2024:40% 2025:56% 2026:45% latest=2026-05-17 blocks=52
3    2024:15% 2025:13% 2026:5% latest=2026-05-17 blocks=52
2162 2024:69% 2025:58% 2026:75% latest=2026-05-17 blocks=52
```

Smoke test:

```text
tests/smoke/test_members.py: 3 passed, 1 skipped
```

The skipped case is the login smoke test because `TEST_USERNAME` and `TEST_PASSWORD` were not provided in the test command.
