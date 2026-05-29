# P3 Smoke Test 策略

更新日期：2026-05-29

## 為什麼先做 Smoke Test

目前 `nghcc-admin-platform` 已定位為「Portal + 核心行政查詢平台」。這類系統最重要的是在修改 Docker、Django、套件版本、資料庫設定、media volume 或權限規則時，能快速知道核心入口是否壞掉。

本階段不追求高覆蓋率，也不測複雜業務流程。先建立最小但有效的保護網，確保系統可啟動、可登入、可讀核心資料、可讀 media、admin 可進入。

## 納入 Smoke Test 的功能

| 測試檔 | 驗證內容 |
| --- | --- |
| `tests/smoke/test_health.py` | `/api/health/` 回傳 HTTP 200 且 database 為 ok |
| `tests/smoke/test_login.py` | `/admin/login/` 可開啟，主要與次要測試帳號可登入 |
| `tests/smoke/test_members.py` | `/eureka/` 可開啟，`members` table 至少有 7895 筆 |
| `tests/smoke/test_hymns.py` | `/hymns/` 可開啟，`hymns` table 至少有 2958 筆 |
| `tests/smoke/test_media.py` | `MEDIA_ROOT` 可讀，檔案數至少 33827 |
| `tests/smoke/test_admin.py` | `/admin/` 可開啟或導向登入，登入後 admin index HTTP 200 |

## 尚未測試的功能

- 奉獻、財會、課程教育、報表：目前未在 admin-platform 內完整實作。
- QR 報到完整流程：目前只有 `checkin_records` 資料與會員頁局部引用。
- 影音下載外部實際下載：會牽涉第三方網站、網路與 ffmpeg/yt-dlp 行為，暫不放入最小 smoke test。
- 檔案上傳破壞性測試：目前先不寫入資料，後續可用自動清除策略補 integration test。

## 執行方式

本機需先完成 P0 正式資料與 media named volume 還原，並啟動：

```bash
docker compose -f docker-compose.yml -f docker-compose.volume.yml up -d --build
```

設定測試帳密環境變數，不要寫進 Git：

```bash
export TEST_USERNAME=<username>
export TEST_PASSWORD=<password>
export TEST_USERNAME_SECONDARY=<username>
export TEST_PASSWORD_SECONDARY=<password>
export TEST_ADMIN_USERNAME=<username>
export TEST_ADMIN_PASSWORD=<password>
```

Git Bash / WSL2 / Linux：

```bash
scripts/run-smoke-tests.sh
```

PowerShell：

```powershell
.\scripts\run-smoke-tests.ps1
```

## 未來如何擴充

1. 加入 API integration tests，先測 read-only API。
2. 加入可自動清理的檔案上傳測試。
3. 為 QR 報到資料查詢補 fixture 或 read-only 檢查。
4. 為使用者權限與選單可見性補角色矩陣測試。
5. 建立匿名使用者、一般同工、superuser 三種角色的行為測試。

## CI 規劃

已建立 `.github/workflows/smoke-tests.yml` 作為 CI 基礎架構。由於目前 smoke test 依賴正式資料還原後的本機 DB 與 media volume，GitHub Actions 暫時只保留 build 與 scaffold。

後續要讓 CI 完整跑通，需要準備：

1. 去識別化的最小 MySQL fixture。
2. 小型 media fixture。
3. CI 專用 `.env.test`。
4. 不含正式密碼的測試帳號。
5. 可在 CI 中還原 DB 與 media 的腳本。
