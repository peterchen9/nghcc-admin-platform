# 部署說明

目標 repository：`nghcc-admin-platform`  
Docker Compose project：`nghcc-admin-platform`

## 部署前檢查

1. 已完成 `.240` 備份。
2. 已備份 DB dump、media、程式目錄、`docker-compose.yml`、`.env`。
3. 已在本機用相同備份完成還原測試。
4. 已確認 `.env` 使用正式密碼與正式 `DJANGO_SECRET_KEY`。
5. 已確認 `DJANGO_DEBUG=0`。

## 建議部署流程

```bash
git clone https://github.com/peterchen9/nghcc-admin-platform.git
cd nghcc-admin-platform
cp .env.example .env
```

編輯 `.env` 後啟動：

```bash
docker compose up -d --build
docker compose ps
docker compose logs --tail=100
```

## 正式環境 Docker 名稱

- web container：`nghcc-admin-web`
- db container：`nghcc-admin-db`
- database：`nghcc_admin`
- local web port：`26001`
- internal web port：`8000`

## 還原資料庫

```bash
gzip -dc backups/192.168.16.240/<BACKUP_TS>/nads26db-<BACKUP_TS>.sql.gz \
  | docker exec -i nghcc-admin-db mysql -unghcc_admin -p<DB_PASSWORD> nghcc_admin
```

## 還原 media

```bash
tar -xzf backups/192.168.16.240/<BACKUP_TS>/nads26-media-<BACKUP_TS>.tar.gz -C uploads --strip-components=1
```

## 驗證

```bash
docker compose ps
curl http://localhost:26001/api/health/
curl -I http://localhost:26001/
```

應確認：

- `nghcc-admin-web` 狀態為 `Up`
- `nghcc-admin-db` 狀態為 `healthy`
- `/api/health/` 回傳 database `ok`
- 首頁可正常開啟
- media 圖片與檔案連結可正常讀取

## 注意事項

- 不要直接覆蓋 `.240` 現行服務。
- 不要在沒有備份與還原演練前切換正式服務。
- `.env`、DB dump、media 備份不可提交到 GitHub。
