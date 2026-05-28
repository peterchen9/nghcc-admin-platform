# 部署說明

目標正式部署主機：`192.168.16.240`  
正式服務 port：`26001`  
Compose project name：`nghcc-admin-platform`

## 部署前檢查

正式部署前需先完成：

- 本機 `docker compose up -d --build` 成功
- `frontend`、`backend`、`db` 容器狀態正常
- `GET /api/health/` 回傳 database `ok`
- `uploads/` 重啟後資料保留
- PostgreSQL volume 重啟後資料保留
- 已備份舊系統原始碼與資料庫
- 已確認舊系統部署路徑與啟動方式

## 容器命名

- `nghcc-admin-frontend`
- `nghcc-admin-backend`
- `nghcc-admin-db`

## 建議部署流程

```bash
git clone https://github.com/peterchen9/nghcc-admin-platform.git
cd nghcc-admin-platform
cp .env.example .env
docker compose up -d --build
docker compose ps
docker compose logs -f
```

## 正式環境注意事項

- `.env` 不可提交到 Git。
- `DJANGO_SECRET_KEY`、`JWT_SECRET`、`SESSION_SECRET` 必須改為正式亂數。
- `DJANGO_DEBUG` 正式環境應設定為 `0`。
- `DJANGO_ALLOWED_HOSTS` 需包含正式 IP 或網域。
- 若要替換既有 `26001` 服務，需先確認舊服務已完整備份並安排停機窗口。

