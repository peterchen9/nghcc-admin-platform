# 維運檢查清單

## 本機開發完成後

- `docker-compose build` 成功
- `docker-compose up -d` 成功
- `docker-compose ps` 顯示三個容器啟動
- `nghcc-admin-db` 狀態為 `healthy`
- `http://localhost:26001/` 回傳正常頁面
- `http://localhost:26002/api/health/` 回傳 database `ok`
- `http://localhost:26002/api/health/` 回傳 database `ok`
- 首頁內容包含 sidebar marker
- 重啟容器後 `uploads/` 資料保留
- 重啟容器後 MySQL 資料庫仍可連線

可使用：

```powershell
.\scripts\check-local.ps1
```

## 部署前

- 舊系統原始碼已備份
- 舊系統資料庫已備份
- 舊系統 uploads/media 已備份
- 已確認舊系統服務由 Docker、systemd 或手動指令啟動
- `.env` 已改為正式設定
- `DJANGO_DEBUG=0`
- `DJANGO_ALLOWED_HOSTS` 包含正式 IP 或網域
- `CSRF_TRUSTED_ORIGINS` 包含正式來源
- 已安排停機或切換窗口

## 部署後

- `docker compose ps` 三個容器正常
- `docker compose logs --tail=100` 無明顯錯誤
- 前端首頁可開啟
- `/api/health/` 回傳 database `ok`
- Django Admin 可開啟
- uploads 可寫入與讀取
- 重新啟動容器後資料仍保留
