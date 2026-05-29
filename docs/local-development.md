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

## 建立管理員

```bash
docker compose exec web python manage.py createsuperuser
```

## 匯入 `.240` 備份資料庫

請先依 [備份方案](backup-plan.md) 從 `.240` 取得 `nads26db-<BACKUP_TS>.sql.gz`。

```bash
gzip -dc backups/192.168.16.240/<BACKUP_TS>/nads26db-<BACKUP_TS>.sql.gz \
  | docker exec -i nghcc-admin-db mysql -unghcc_admin -pchange_me_password nghcc_admin
```

## 匯入 media

```bash
tar -xzf backups/192.168.16.240/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz -C uploads --strip-components=1
```

確認 `uploads/` 下有舊系統 media 檔案後，重新整理 `http://localhost:26001` 測試。

## 注意事項

- `.env` 不可提交到 GitHub。
- `uploads/` 實際檔案不可提交到 GitHub。
- DB dump 與 media 備份不可提交到 GitHub。
