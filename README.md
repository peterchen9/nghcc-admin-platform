# 北門行政作業平台

這是教會系統專案之一，用於北門行政作業管理。此 repository 名稱統一為 `nghcc-admin-platform`。

## 技術架構

- Backend：Python 3.11、Django 5、Gunicorn
- Database：MySQL 8
- Container：Docker Compose
- uploads/media：本機 `uploads/` 掛載到 container `/app/media`
- 舊系統來源：`192.168.16.240:/home/apps1/nads26`

## Docker 命名

- Docker Compose project：`nghcc-admin-platform`
- web container：`nghcc-admin-web`
- db container：`nghcc-admin-db`
- database name：`nghcc_admin`
- local web port：`26001`
- internal web port：`8000`

## 本機啟動方式

```bash
cp .env.example .env
docker compose up -d --build
```

Windows 若 `docker compose` 不可用，可改用：

```bash
docker-compose up -d --build
```

## 本機網址

- Web：`http://localhost:26001`
- Health：`http://localhost:26001/api/health/`
- Django Admin：`http://localhost:26001/admin/`
- MySQL：`localhost:26003`

## 常用指令

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
```

## 本機檢查

```powershell
.\scripts\check-local.ps1
```

## 文件

- [192.168.16.240 伺服器盤點](docs/server-audit-192.168.16.240.md)
- [備份方案](docs/backup-plan.md)
- [本機開發](docs/local-development.md)
- [部署說明](docs/deployment.md)
- [遷移紀錄](docs/migration-notes.md)
- [既有系統盤點](docs/system-audit.md)
- [除錯紀錄](docs/debug-notes.md)
