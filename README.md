# 北門行政作業平台

## 專案說明

這是教會系統專案之一，用於北門行政作業管理。

本 repository 名稱統一為 `nghcc-admin-platform`，Docker Compose project name 也固定使用 `nghcc-admin-platform`。

## 技術架構

- Frontend：Nginx reverse proxy
- Backend：Python 3.11、Django 5、Gunicorn，程式結構沿用舊系統 `nads26/`、`modules/`、`templates/`
- Database：MySQL 8
- Container：Docker Compose
- 持久化資料：MySQL volume、`uploads/`

## 本機啟動方式

```bash
cp .env.example .env
docker compose up -d --build
```

若本機 Docker CLI 尚未啟用 `docker compose` 子指令，可暫時使用：

```bash
docker-compose up -d --build
```

## 本機服務

- Frontend：http://localhost:26001
- Backend health：http://localhost:26002/api/health/
- Django Admin：http://localhost:26001/admin/
- MySQL：localhost:26003

## 常用指令

```bash
docker compose ps
docker compose logs -f
docker compose restart
docker compose down
```

## 本機健康檢查與備份

```powershell
.\scripts\check-local.ps1
.\scripts\backup-db.ps1
.\scripts\backup-uploads.ps1
```

## 目前本機測試狀態

2026-05-28 已完成本機 Docker 測試：

- `nghcc-admin-frontend` 可啟動並回傳 `200 text/html`
- `nghcc-admin-backend` 可啟動，`/api/health/` 回傳 database `ok`
- `nghcc-admin-db` 可啟動並通過 healthcheck
- `uploads/` 經容器重啟後仍保留測試檔案
- MySQL named volume 經容器重啟後仍可正常連線
- 已匯入舊系統 MySQL dump，本機首頁可顯示舊系統介面與選單資料

## 文件

- [既有系統盤點](docs/system-audit.md)
- [本機開發](docs/local-development.md)
- [部署說明](docs/deployment.md)
- [備份與還原](docs/backup-and-restore.md)
- [維運檢查清單](docs/operations-checklist.md)
- [除錯紀錄](docs/debug-notes.md)
