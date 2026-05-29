# 除錯紀錄

## 2026-05-28

### Docker CLI 狀態

本機 `docker version` 可正常回應，Docker Engine 可用。

`docker compose version` 在目前 PowerShell 環境回傳：

```text
WARNING: Error loading config file: open C:\Users\peter\.docker\config.json: Access is denied.
docker: unknown command: docker compose
```

但 `docker-compose version` 可正常回應：

```text
Docker Compose version v5.1.3
```

因此本機測試先使用 `docker-compose` 指令。文件仍保留標準 `docker compose` 寫法，並補充 Windows fallback。

### SSH 盤點狀態

`192.168.16.240:22` 可連線，但目前沒有可用的非互動 SSH 權限：

```text
peterchen@192.168.16.240: Permission denied (publickey,password).
```

後續若提供主機帳密或 SSH key，需回補完整檔案結構、資料庫設定與啟動方式。

### 本機 Docker 測試

已執行：

```bash
docker-compose build
docker-compose up -d
docker-compose ps
docker-compose logs --tail=80
docker-compose restart
```

測試結果：

- `nghcc-admin-frontend`：啟動成功，`http://localhost:26001/` 回傳 `200 text/html`
- `nghcc-admin-backend`：啟動成功，`http://localhost:26002/api/health/` 回傳 database `ok`
- `nghcc-admin-db`：啟動成功，healthcheck 狀態為 `healthy`
- `http://localhost:26001/api/modules/` 可透過 frontend proxy 取得模組 JSON
- `uploads/persistence-check.txt` 在容器重啟後仍保留
- PostgreSQL volume `nghcc-admin-db-data` 在容器重啟後仍可正常使用

### 瀏覽器自動化驗證

嘗試使用 Codex 的 Node/Playwright 瀏覽器驗證時，Node kernel 回報：

```text
node_repl kernel exited unexpectedly
windows sandbox failed: spawn setup refresh
```

因此本次畫面驗證以 HTTP smoke test 為準，尚未取得瀏覽器截圖。

### 2026-05-28 後續維運腳本驗證

新增並驗證 PowerShell 腳本：

```powershell
.\scripts\check-local.ps1
.\scripts\backup-db.ps1
.\scripts\backup-uploads.ps1
```

驗證結果：

- `check-local.ps1` 可列出三個容器，並確認 frontend、backend health、frontend API proxy 都回傳 HTTP 200。
- `check-local.ps1` 可確認 database 狀態為 `ok`。
- `backup-db.ps1` 可用 `pg_dump` 匯出 PostgreSQL 備份，測試檔大小約 23 KB。
- `backup-uploads.ps1` 可壓縮 `uploads/`，測試檔大小約 272 bytes。
- `backups/` 內實際備份檔已由 `.gitignore` 排除，不會提交。

PowerShell 腳本原本使用繁體中文輸出訊息，但 Windows PowerShell 5 讀取無 BOM UTF-8 腳本時會把中文字串解析成亂碼，造成 parser error。為了讓腳本在目前 Windows 環境可直接執行，腳本執行輸出改為 ASCII；繁體中文說明保留在 docs 文件中。

### 2026-05-28 舊系統 SSH 盤點

使用提供的 SSH 帳號完成唯讀盤點，未修改遠端舊系統內容。

確認結果：

- 舊系統主機：`192.168.16.240`
- hostname：`gino25`
- 舊系統路徑：`/home/apps1/nads26`
- 舊系統容器：`nads26-web`
- 舊系統資料庫容器：`nads26db`
- 對外 port：`26001`
- 舊系統資料庫：MySQL 8，database `nads26db`
- 舊系統啟動命令：`python manage.py runserver 0.0.0.0:8000`
- 舊系統不是 Git repository

已在本機 `backups/legacy-nads26/` 建立備份：

- `nads26-source-no-media-mysql_data.tar.gz`，大小 `116235` bytes
- `nads26db-mysql-dump.sql.gz`，大小 `2627335` bytes

`media/` 約 `6.0G`、約 `33824` 個檔案，尚未下載完整實體檔。正式遷移前需安排專門的 media 備份與校驗流程。

### 2026-05-28 新專案資料庫改為 MySQL

因舊系統實際使用 MySQL 8，新專案已從 PostgreSQL 調整為 MySQL 8：

- Docker image：`mysql:8.0`
- container name：`nghcc-admin-db`
- volume：`nghcc-admin-mysql-data`
- local port：`26003 -> 3306`
- Django driver：`PyMySQL`

已重新執行：

```powershell
docker-compose up -d --build
.\scripts\check-local.ps1
.\scripts\backup-db.ps1
```

結果：

- frontend、backend、frontend API proxy 均回傳 HTTP 200
- `/api/health/` 回傳 database `ok`
- `nghcc-admin-db` 狀態為 `healthy`
- MySQL 版 `backup-db.ps1` 可正常匯出 SQL

MySQL 8 使用一般應用帳號執行 `mysqldump` 時，若未加 `--no-tablespaces` 會出現 `PROCESS privilege` 錯誤；腳本已加入 `--no-tablespaces`。

### 2026-05-28 複製舊系統程式內容

依照「目錄要一樣」的要求，已將舊系統程式內容複製到新專案 `backend/`：

- `backend/nads26/`
- `backend/modules/`
- `backend/templates/`
- `backend/scripts/`
- `backend/manage.py`
- `backend/requirements.txt`

排除項目：

- `.env`
- `db.sqlite3`
- `mysql_data/`
- `media/` 實體檔
- `__pycache__/`
- `*.pyc`
- 明文資料庫密碼與使用者密碼雜湊

Nginx frontend 已改為 reverse proxy，`http://localhost:26001/` 直接代理到 Django 舊系統介面。

已匯入本機備份 `backups/legacy-nads26/nads26db-mysql-dump.sql.gz` 到本機 MySQL database `nghcc_admin_platform`，目前本機資料庫有 52 張資料表。

本機 `uploads/` 會掛載到容器 `/app/media`，並已建立舊系統主要 media 子目錄：

- `uploads/eureka/photo`
- `uploads/hymns/html`
- `uploads/hymns/midi`
- `uploads/hymns/mp3`
- `uploads/hymns/pdf`

完整 `media/` 約 6.0G，尚未複製實體檔。

同步腳本中的舊資料庫密碼已改為環境變數：

- `REMOTE_MEMBER_DB_PASSWORD`
- `DATACENTER_DB_PASSWORD`
- `NADS26_DB_PASSWORD`

`migrate_users.py` 中的舊密碼雜湊也已移除，避免把可重用的帳號雜湊提交到 GitHub。

驗證結果：

- `http://localhost:26001/` 回傳 `200 text/html; charset=utf-8`
- `http://localhost:26002/api/health/` 回傳 database `ok`
- `.\scripts\check-local.ps1` 通過
- `/hymns/`、`/eureka/`、`/users/` 目前回傳 `302`，符合需要登入或權限導向的舊系統行為

### 2026-05-29 新增使用者無法登入後台

現象：

```text
請輸入正確的工作人員帳號使用者名稱及密碼。請注意兩者皆區分大小寫。
```

原因：

- Django Admin 只允許 `is_staff=True` 的使用者登入。
- 舊系統 `/users/create/` 使用 `User.objects.create_user()` 建立使用者，但沒有設定 `is_staff=True`。
- 因此新建帳號雖然 `is_active=True`、密碼正確，仍會被 `/admin/login/` 拒絕。

已修正：

- `backend/modules/accounts/views.py`
  - 新增使用者時接收 `is_staff`，預設為 `True`。
  - 編輯使用者時可更新 `is_staff`。
- `backend/templates/accounts/user_list.html`
  - 使用者列表新增「後台」欄位。
  - 新增/編輯表單新增「允許登入管理後台」勾選項。

本機驗證：

- 本機資料庫中 `peterchen` 已修正為 `is_staff=1`。
- 建立臨時測試帳號 `codex_login_test`，設定 `is_staff=True` 後 `authenticate()` 回傳成功，驗證後已刪除。
- `.\scripts\check-local.ps1` 通過。
- `/admin/login/` 回傳 `200 text/html; charset=utf-8`。

.240 唯讀確認：

```text
id  username   is_active  is_staff  is_superuser
8   peterchen  1          0         0
9   abcde      1          0         0
10  emily      1          0         0
```

尚未修改 .240 原始系統或資料庫。若要修 .240 既有帳號，需在舊系統資料庫執行：

```sql
UPDATE auth_user
SET is_staff = 1
WHERE username IN ('peterchen', 'abcde', 'emily');
```

## 2026-05-29 本機修正：新增使用者登入後只剩首頁

### 問題原因

本機與 `.240` 的舊系統都使用 `accounts_userprofile_allowed_menu_items` 控制非 superuser 的左側選單。新增使用者若只有 `is_staff=True`，只能登入 Django Admin 或後台頁面；若沒有任何 `allowed_menu_items`，登入後左側仍會只看到固定的「首頁」。

### 本機修正

- `backend/modules/accounts/views.py`
  - 新增使用者時，若未另外指定權限，會自動套用所有啟用中的 `MenuItem`。
  - 設定權限時只接受 list 格式，並只寫入啟用中的選單項目。
- `backend/modules/pages/`
  - 補齊 `.240` 已出現的首頁編輯入口與 CKEditor 上傳欄位 migration。
- `backend/templates/base.html`
  - 補齊 `.240` 的登入 `next=/` 與首頁快速連結 CSS。

### `.240` 比對結果

本次對 `.240` 僅做唯讀比對，沒有修改遠端檔案、資料庫或 container。

- `.240` 啟用選單資料仍存在，`menu_menuitem` 有 23 筆啟用資料。
- `.240` 有些帳號沒有選單權限，例如 `abcde` 的權限數為 0，因此畫面會只剩首頁。
- `.240` 在 2026-05-29 10:28-10:32 曾偵測到遠端檔案變更並自動 reload，該現象不是本機修正造成。
