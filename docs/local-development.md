# 本機開發

## 前置需求

- Docker Desktop
- Docker Compose
- Git

## 啟動

```bash
cp .env.example .env
docker compose up -d --build
```

Windows 若 `docker compose` 不可用，可改用：

```bash
docker-compose up -d --build
```

## 服務

- Web：`http://localhost:26001`
- Health：`http://localhost:26001/api/health/`
- Django Admin：`http://localhost:26001/admin/`
- MySQL：`localhost:26003`

## Docker 名稱

- project name：`nghcc-admin-platform`
- web container：`nghcc-admin-web`
- db container：`nghcc-admin-db`
- database name：`nghcc_admin`
- internal web port：`8000`

## 檢查

```bash
docker compose ps
docker compose logs --tail=100
```

PowerShell：

```powershell
.\scripts\check-local.ps1
```

Git Bash / WSL2 / Linux：

```bash
scripts/check-local.sh
```

Smoke 與唯讀 integration tests：

```bash
export TEST_USERNAME=<username>
export TEST_PASSWORD=<password>
export TEST_USERNAME_SECONDARY=<username>
export TEST_PASSWORD_SECONDARY=<password>
export TEST_ADMIN_USERNAME=<username>
export TEST_ADMIN_PASSWORD=<password>
scripts/run-smoke-tests.sh
```

PowerShell：

```powershell
$env:TEST_USERNAME="<username>"
$env:TEST_PASSWORD="<password>"
$env:TEST_USERNAME_SECONDARY="<username>"
$env:TEST_PASSWORD_SECONDARY="<password>"
$env:TEST_ADMIN_USERNAME="<username>"
$env:TEST_ADMIN_PASSWORD="<password>"
.\scripts\run-smoke-tests.ps1
```

## 建立管理員

```bash
docker compose exec web python manage.py createsuperuser
```

## 匯入 `.240` 備份資料庫

請先依 [備份方案](backup-plan.md) 從 `.240` 取得 `nads26db-<BACKUP_TS>.sql.gz`。

```bash
YES=1 scripts/restore-db.sh backups/192.168.16.240/<BACKUP_TS>/nads26db-<BACKUP_TS>.sql.gz
```

## 匯入 media

### 建議方式：Docker named volume

Windows bind mount 在處理大量中文檔名 media 時，可能因檔案系統、Docker Desktop 或 tar 編碼相容性造成少數檔案沒有解出。正式資料完整性驗證請優先使用 Docker named volume：

```bash
scripts/verify-backup-checksum.sh backups/192.168.16.240/<BACKUP_TS>
scripts/restore-media-to-volume.sh backups/192.168.16.240/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz
scripts/check-media-integrity.sh volume nghcc-admin-media-data
```

使用 named volume 啟動本機服務：

```bash
docker compose -f docker-compose.yml -f docker-compose.volume.yml up -d --build
```

### 開發方式：Windows bind mount

日常開發仍可使用預設 `./uploads:/app/media`：

```bash
tar -xzf backups/192.168.16.240/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz -C uploads --strip-components=1
scripts/check-media-integrity.sh uploads uploads
```

確認 `uploads/` 下有舊系統 media 檔案後，重新整理 `http://localhost:26001` 測試。

目前正式 media 預期檔案數為 `33827`。若 Windows bind mount 只解出 `33812` 個檔案，請改用 named volume 或 WSL2/Linux filesystem 補齊，不要把 bind mount 的缺檔視為正式備份缺檔。

## P0 本機完整還原範例

```bash
BACKUP_TS=20260529-134006
BACKUP_DIR=backups/192.168.16.240/$BACKUP_TS

scripts/verify-backup-checksum.sh "$BACKUP_DIR"
YES=1 scripts/restore-db.sh "$BACKUP_DIR/nads26db-$BACKUP_TS.sql.gz"
scripts/restore-media-to-volume.sh "$BACKUP_DIR/nads26-media-$BACKUP_TS.tar.gz"
scripts/check-media-integrity.sh volume nghcc-admin-media-data
docker compose -f docker-compose.yml -f docker-compose.volume.yml up -d --build
scripts/check-local.sh
```

## 注意事項

- `.env` 不可提交到 GitHub。
- `uploads/` 實際檔案不可提交到 GitHub。
- DB dump 與 media 備份不可提交到 GitHub。
- `docker-compose.volume.yml` 只切換本機 media 掛載方式，不會連線或修改 `.240`。

## P5 安全設定提醒

- 本機 HTTP 開發環境維持 `SESSION_COOKIE_SECURE=False` 與 `CSRF_COOKIE_SECURE=False`。
- production 部署前必須改為 `SESSION_COOKIE_SECURE=True` 與 `CSRF_COOKIE_SECURE=True`。
- production 部署前必須設定正式 `ALLOWED_HOSTS` / `DJANGO_ALLOWED_HOSTS`。
- production 部署前必須設定正式 HTTPS `CSRF_TRUSTED_ORIGINS`。
- `DisableCSRFMiddleware` 目前仍存在，P5 第一階段只盤點不硬改，避免破壞既有登入、上傳與 admin 流程。
- `.env.production.example` 提供 production 樣板；目前 `.240` 若仍使用 HTTP，cookie secure 先維持 `False`，改 HTTPS 後必須調整為 `True`。
- `UPLOAD_STRICT_MIME_CHECK=False` 為預設值；若改為 `True`，請先跑完整 smoke、integration、security tests。
