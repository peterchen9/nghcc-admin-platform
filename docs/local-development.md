# 本機開發

## 需求

- Docker Desktop
- Docker Compose
- Git

## 第一次啟動

```bash
cp .env.example .env
docker compose up -d --build
```

若 Windows 環境尚未提供 `docker compose` 子指令，可使用：

```bash
docker-compose up -d --build
```

## 檢查服務

```bash
docker compose ps
docker compose logs -f
```

或使用本機健康檢查腳本：

```powershell
.\scripts\check-local.ps1
```

確認以下網址：

- Frontend：http://localhost:26001
- Backend health：http://localhost:26002/api/health/
- Django Admin：http://localhost:26001/admin/

## 建立管理員帳號

```bash
docker compose exec backend python manage.py createsuperuser
```

## uploads 持久化

本機 `uploads/` 會掛載到後端容器 `/app/media`，對應舊系統的 media 目錄。容器重啟後，上傳檔案應保留。

目前已建立與舊系統相同的主要 media 子目錄：

```text
uploads/eureka/photo
uploads/hymns/html
uploads/hymns/midi
uploads/hymns/mp3
uploads/hymns/pdf
```

## database 持久化

MySQL 使用 Docker named volume：

```text
nghcc-admin-mysql-data
```

除非已完成備份，不要刪除此 volume。

## 本機備份

```powershell
.\scripts\backup-db.ps1
.\scripts\backup-uploads.ps1
```
