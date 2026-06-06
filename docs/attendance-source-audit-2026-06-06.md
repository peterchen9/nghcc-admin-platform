# 出席即時計算抽樣與源頭盤點

日期：2026-06-06

## 目的

本次工作執行前一輪建議的第 1、2 項：

1. 抽樣核對 `checkin_records` 即時計算是否能對上原始報到資料。
2. 確認是否可以直接從活石條碼/Datacenter 取得每週報到源頭資料。

所有驗證均在 Docker 環境內執行。

## 第 1 項：抽樣核對結果

即時計算規則目前採用：

- 來源表：`checkin_records`
- 有效主日：`timestamp` 為週日，且當天不同 `church_id` 報到人數至少 50 人。
- 同一會員同一天多次報到只算一次。

有效主日週數：

| 年度 | 有效主日週數 |
| --- | ---: |
| 2021 | 38 |
| 2022 | 46 |
| 2023 | 53 |
| 2024 | 52 |
| 2025 | 50 |

最近有效主日：

| 日期 | 不同報到人數 |
| --- | ---: |
| 2025-12-14 | 378 |
| 2025-12-07 | 374 |
| 2025-11-30 | 382 |
| 2025-11-23 | 397 |
| 2025-11-16 | 412 |

抽樣會員核對：

| Church ID | 2021 | 2022 | 2023 | 2024 | 2025 |
| ---: | --- | --- | --- | --- | --- |
| 7 | 27/38 = 71% | 29/46 = 63% | 38/53 = 72% | 47/52 = 90% | 40/50 = 80% |
| 9 | 27/38 = 71% | 27/46 = 59% | 40/53 = 75% | 43/52 = 83% | 41/50 = 82% |
| 10 | 22/38 = 58% | 26/46 = 57% | 36/53 = 68% | 37/52 = 71% | 22/50 = 44% |
| 2 | 9/38 = 24% | 3/46 = 7% | 24/53 = 45% | 19/52 = 37% | 28/50 = 56% |
| 3 | 13/38 = 34% | 0/46 = 0% | 5/53 = 9% | 8/52 = 15% | 6/50 = 12% |
| 1 | 0/38 = 0% | 1/46 = 2% | 0/53 = 0% | 0/52 = 0% | 0/50 = 0% |
| 8 | 14/38 = 37% | 17/46 = 37% | 30/53 = 57% | 18/52 = 35% | 26/50 = 52% |
| 487 | 0/38 = 0% | 3/46 = 7% | 2/53 = 4% | 0/52 = 0% | 0/50 = 0% |
| 2162 | 20/38 = 53% | 14/46 = 30% | 35/53 = 66% | 36/52 = 69% | 25/50 = 50% |
| 4632 | 34/38 = 89% | 3/46 = 7% | 2/53 = 4% | 0/52 = 0% | 0/50 = 0% |

核對結論：

- Helper 計算出的年度分子/分母與 SQL 直接從 `checkin_records` 統計的結果一致。
- 舊欄位 `members.percent_year` 與即時計算結果差異明顯。
- 舊欄位包含 2026 值，例如部分會員為 `...-100`，但本機 `checkin_records` 最新有效主日只到 `2025-12-14`。這表示舊彙總欄位不適合作為目前畫面可信來源。

## 第 2 項：活石條碼/Datacenter 源頭盤點

已新增只讀盤點腳本：

```bash
python scripts/inspect_attendance_source.py
```

使用方式：

```bash
SOURCE_DB_USER=<user> SOURCE_DB_PASSWORD=<password> python scripts/inspect_attendance_source.py
```

本次在 Docker 內嘗試候選 MySQL host：

| Host | 結果 |
| --- | --- |
| `host.docker.internal:3306` | Connection refused |
| `127.0.0.1:3306` | Connection refused |
| `192.168.16.225:3306` | Timed out |
| `192.168.16.240:3306` | MySQL 有回應，但 `peter` / `peterchen` 帳號皆被拒絕 |
| `172.20.60.241:3306` | Timed out |

SSH 只讀盤點：

- `192.168.16.225` 與 `192.168.16.240` 的 SSH 服務有回應。
- 批次模式沒有可用 SSH key，回應為 `Permission denied (publickey,password)`。
- 目前環境無法完成非互動式密碼 SSH 盤點。

源頭結論：

- 目前已確認可直接可信使用的源頭是本機 `checkin_records`。
- 活石條碼或 Datacenter 的更上游原始資料尚未取得授權確認。
- `192.168.16.240:3306` 是目前最可能的 MySQL 入口，但需要正確 MySQL 帳號，或可用 SSH 登入後在主機上檢查 Docker/DB。

## 下一步需要的資訊

若要直接接活石條碼源頭，需要取得至少其中一種：

- 活石條碼 MySQL 帳號，且可從 Docker 網路連到資料庫。
- 可用 SSH 帳密或 key，用來在主機上只讀盤點 Docker 容器與 DB 設定。
- 活石條碼資料匯出檔或 API 文件。

理想原始欄位：

- 會員編號
- 報到時間
- 聚會/活動類型
- 活動 ID
- 報到來源設備
- 是否補登
- 原始掃碼紀錄 ID

取得聚會/活動類型後，應將目前的「週日 + 50 人門檻」改成明確查詢主日聚會資料。

## 2026-06-06 更新：活石條碼 SQLite 確認

後續確認活石條碼目前不是 MySQL，而是 SQLite：

- `/home/peterchen/living_stone_barcode/nghc_daka/db.sqlite3`
- `/home/peterchen/address_book/ContactsDB`

活石條碼報到表：

- DB：`/home/peterchen/living_stone_barcode/nghc_daka/db.sqlite3`
- Table：`check_in_checkinrecord`
- Rows：`130306`
- Columns：`id`, `t_check_in`, `church_id`, `family1`, `is_qr_code`, `name`, `section`, `phone_num`
- Time range：`2020-12-04 06:06:44` 到 `2026-05-21 08:13:59`

通訊錄 SQLite：

- DB：`/home/peterchen/address_book/ContactsDB`
- 會員主表：`imports_person`
- Rows：`7896`

活石條碼 Django model 顯示 `CheckInRecord.t_check_in` 使用 `datetime.datetime.now`，主機系統時間為台灣 CST，因此 `t_check_in` 應按本地時間解讀。

### 與 admin-platform 本機 `checkin_records` 的差異

比對結果：

- 本機 `checkin_records.raw_id` 對應活石條碼 `check_in_checkinrecord.id`。
- 本機既有 `timestamp` 比活石條碼 `t_check_in` 多 16 小時。
- 例如：
  - 活石條碼 `id=122981`: `2025-12-14 11:31:25`
  - 本機 `raw_id=122981`: `2025-12-15 03:31:25`

這表示舊同步或匯入流程產生時區偏移，導致部分週日報到被推到週一，會影響出席計算。

### Dry-run 同步計畫

已新增 dry-run 預設的同步工具：

```bash
python scripts/sync_checkins_from_living_stone_sqlite.py /path/to/db.sqlite3
```

本次使用從活石條碼下載的 SQLite 做 dry-run：

```text
source_rows=130306
source_first=2020-12-04 06:06:44
source_last=2026-05-21 08:13:59
existing_raw_ids=107285
unchanged=0
updates=107285
inserts=23021
dry_run=true
```

結論：

- 需要更新本機既有 `107285` 筆報到時間，修正舊的 16 小時偏移。
- 需要新增 `23021` 筆本機缺少的活石條碼報到資料。
- 這是大量資料異動；套用前應先備份 admin-platform MySQL，再用 `--apply` 執行。
## 2026-06-06 apply record

Required attendance-source fix was applied after backup.

Backup:

- `backups/nghcc-admin-db-20260606-154152.sql`
- Size: 14126885 bytes
- Header verified as MySQL dump for database `nghcc_admin`

Operational notes:

- `checkin_records` originally had only the primary key.
- Large updates by `raw_id` timed out while `raw_id` was unindexed.
- Added index: `checkin_records_raw_id_idx ON checkin_records (raw_id)`.
- Updated `scripts/sync_checkins_from_living_stone_sqlite.py` so future `--apply` runs ensure the index exists and apply rows in batches.

Final apply output:

```text
raw_id_index=checkin_records_raw_id_idx:exists
source_rows=130306
source_first=2020-12-04 06:06:44
source_last=2026-05-21 08:13:59
existing_raw_ids=107285
unchanged=0
updates=107285
inserts=23021
applied=true
```

Post-apply database verification:

```text
total=130306
first_ts=2020-12-04 06:06:44
last_ts=2026-05-21 08:13:59
raw_ids=130306
```

Post-apply dry-run verification:

```text
existing_raw_ids=130306
unchanged=130306
updates=0
inserts=0
dry_run=true
```
