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

