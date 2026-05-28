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
