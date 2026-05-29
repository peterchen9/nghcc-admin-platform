# 備份方案

適用主機：`192.168.16.240`  
既有系統路徑：`/home/apps1/nads26`  
既有 Docker Compose：`/home/apps1/nads26/docker-compose.yml`  
既有 web container：`nads26-web`  
既有 DB container：`nads26db`  
既有資料庫：`nads26db`  
既有 media/uploads：`/home/apps1/nads26/media`

## 原則

1. MySQL 使用 `mysqldump` 做線上備份。
2. `media/` 使用 `tar` 或 `rsync` 備份。
3. `docker-compose.yml`、`.env` 與程式目錄需一起備份。
4. 不要把執行中的 `mysql_data/` 直接當作唯一備份，因為 MySQL 正在寫入時直接複製資料目錄可能不一致。
5. 備份檔命名需包含日期時間，格式建議為 `YYYYmmdd-HHMMSS`。
6. 備份過程不要停止服務、不要重啟服務、不要修改遠端設定。
7. 備份檔含 `.env` 與資料庫內容，需視為敏感資料，不可提交到 GitHub。

## 遠端備份指令

以下指令在 `192.168.16.240` 主機上執行。

### 1. 建立備份資料夾

```bash
export BACKUP_TS="$(date +%Y%m%d-%H%M%S)"
export APP_DIR="/home/apps1/nads26"
export BACKUP_ROOT="/home/peter/backups/nghcc-admin-platform"
export BACKUP_DIR="${BACKUP_ROOT}/${BACKUP_TS}"

mkdir -p "${BACKUP_DIR}"
echo "BACKUP_DIR=${BACKUP_DIR}"
```

### 2. 使用 mysqldump 備份 `nads26db`

```bash
docker exec nads26db sh -c 'mysqldump \
  -u"$MYSQL_USER" \
  -p"$MYSQL_PASSWORD" \
  --single-transaction \
  --quick \
  --routines \
  --triggers \
  --events \
  --default-character-set=utf8mb4 \
  "$MYSQL_DATABASE"' \
  > "${BACKUP_DIR}/nads26db-${BACKUP_TS}.sql"

gzip -9 "${BACKUP_DIR}/nads26db-${BACKUP_TS}.sql"
```

### 3. 壓縮 `media/`

```bash
tar -C "${APP_DIR}" -czf "${BACKUP_DIR}/nads26-media-${BACKUP_TS}.tar.gz" media
```

若要降低遠端主機壓縮期間的 CPU 壓力，可改用 `rsync` 先同步到外部備份機，再由備份機壓縮。

### 4. 壓縮程式目錄，排除資料庫與暫存

```bash
tar -C "$(dirname "${APP_DIR}")" -czf "${BACKUP_DIR}/nads26-source-${BACKUP_TS}.tar.gz" \
  --exclude='nads26/mysql_data' \
  --exclude='nads26/media' \
  --exclude='nads26/.git' \
  --exclude='nads26/__pycache__' \
  --exclude='nads26/*/__pycache__' \
  --exclude='nads26/*/*/__pycache__' \
  --exclude='*.pyc' \
  nads26
```

### 5. 另外保留 compose 與環境設定副本

```bash
cp "${APP_DIR}/docker-compose.yml" "${BACKUP_DIR}/docker-compose-${BACKUP_TS}.yml"
cp "${APP_DIR}/.env" "${BACKUP_DIR}/env-${BACKUP_TS}.backup"
```

### 6. 檢查備份檔大小

```bash
du -sh "${BACKUP_DIR}"
ls -lh "${BACKUP_DIR}"
```

### 7. 產生 sha256 checksum

```bash
cd "${BACKUP_DIR}"
sha256sum * > "SHA256SUMS-${BACKUP_TS}.txt"
cat "SHA256SUMS-${BACKUP_TS}.txt"
```

## 本機下載指令

以下指令在本機 PowerShell 或 Git Bash 執行。請先把 `<BACKUP_TS>` 換成實際備份時間，例如 `20260529-123000`。

### 1. 建立本機備份資料夾

PowerShell：

```powershell
$BackupTs = "<BACKUP_TS>"
$LocalBackupDir = "C:\Users\peter\OneDrive\Documents\北門行政中心\nghcc-admin-platform\backups\192.168.16.240\$BackupTs"
New-Item -ItemType Directory -Force -Path $LocalBackupDir
```

### 2. 使用 scp 下載 DB dump

```powershell
scp peter@192.168.16.240:/home/peter/backups/nghcc-admin-platform/<BACKUP_TS>/nads26db-<BACKUP_TS>.sql.gz $LocalBackupDir\
```

### 3. 使用 scp 下載 media 壓縮檔

```powershell
scp peter@192.168.16.240:/home/peter/backups/nghcc-admin-platform/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz $LocalBackupDir\
```

### 4. 使用 scp 下載程式備份檔

```powershell
scp peter@192.168.16.240:/home/peter/backups/nghcc-admin-platform/<BACKUP_TS>/nads26-source-<BACKUP_TS>.tar.gz $LocalBackupDir\
```

### 5. 使用 scp 下載 docker-compose.yml 與 checksum

```powershell
scp peter@192.168.16.240:/home/peter/backups/nghcc-admin-platform/<BACKUP_TS>/docker-compose-<BACKUP_TS>.yml $LocalBackupDir\
scp peter@192.168.16.240:/home/peter/backups/nghcc-admin-platform/<BACKUP_TS>/SHA256SUMS-<BACKUP_TS>.txt $LocalBackupDir\
```

### 6. 使用 rsync 下載整個備份資料夾

若本機環境有 `rsync`，也可以一次下載：

```bash
rsync -avh --progress peter@192.168.16.240:/home/peter/backups/nghcc-admin-platform/<BACKUP_TS>/ ./backups/192.168.16.240/<BACKUP_TS>/
```

## 本機還原準備

1. 解壓 `nads26-source-<BACKUP_TS>.tar.gz` 到暫存資料夾，將舊系統內容整理進 `backend/`。
2. 先驗證 checksum，確認 DB dump、media tar 與程式備份檔沒有下載損壞。
3. 啟動本機 Docker：

```bash
cp .env.example .env
docker compose up -d --build
```

4. 匯入資料庫：

```bash
YES=1 scripts/restore-db.sh backups/192.168.16.240/<BACKUP_TS>/nads26db-<BACKUP_TS>.sql.gz
```

5. 還原 media。正式資料還原建議優先使用 Docker named volume 或 Linux/WSL2 filesystem：

```bash
scripts/restore-media-to-volume.sh backups/192.168.16.240/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz
```

若只是一般 Windows 開發，也可以使用 bind mount `uploads/`，但中文檔名可能遇到相容性問題：

```bash
tar -xzf backups/192.168.16.240/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz -C uploads --strip-components=1
```

6. 驗證：

```bash
docker compose ps
docker compose logs --tail=100
curl http://localhost:26001/api/health/
```

## Checksum 驗證流程

本機下載備份後，先執行：

```bash
scripts/verify-backup-checksum.sh backups/192.168.16.240/<BACKUP_TS>
```

此腳本會讀取 `SHA256SUMS-<BACKUP_TS>.txt`，並驗證同資料夾內的 DB dump、media tar、project tar、compose 與 env 備份。若 checksum 失敗，不可進行還原，應重新下載備份檔。

## Media 完整性與 Windows bind mount 風險

正式備份 `nads26-media-20260529-134006.tar.gz` 內有 `33827` 個一般檔案。先前在 Windows bind mount `uploads/` 解壓時只得到 `33812` 個檔案，缺少 15 個中文檔名照片。這通常不是正式主機資料遺失，而是 Windows 檔案系統、Docker Desktop bind mount、tar 工具或中文檔名編碼在跨系統處理時的相容性風險。

建議：

1. 正式還原與完整性驗證使用 Linux/WSL2 filesystem 或 Docker named volume。
2. 本機 Windows bind mount 只作日常開發，不作唯一的 media 完整性依據。
3. 每次還原後都執行完整性檢查：

```bash
scripts/check-media-integrity.sh volume nghcc-admin-media-data
scripts/check-media-integrity.sh uploads uploads
```

named volume 達到 `33827` 個檔案才視為 media 還原完整。Windows bind mount 若仍為 `33812`，應記錄為本機 bind mount 限制，不應推論正式備份缺檔。
