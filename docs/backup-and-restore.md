# 備份與還原

本專案目前有兩類持久化資料：

- MySQL named volume：`nghcc-admin-mysql-data`
- 上傳檔案目錄：`uploads/`

正式部署前與每次重大異動前，都應先完成資料庫與 uploads 備份。

## 備份資料庫

Windows PowerShell：

```powershell
.\scripts\backup-db.ps1
```

腳本會透過 `mysqldump` 匯出目前 `.env` 指定的 MySQL database。輸出檔會放在 `backups/`，檔名格式如下：

```text
nghcc-admin-db-yyyyMMdd-HHmmss.sql
```

## 備份 uploads

Windows PowerShell：

```powershell
.\scripts\backup-uploads.ps1
```

輸出檔會放在 `backups/`，檔名格式如下：

```text
nghcc-admin-uploads-yyyyMMdd-HHmmss.zip
```

## 還原資料庫

還原前務必確認目前 `.env` 指向正確資料庫，且已備份現有資料。

```powershell
.\scripts\restore-db.ps1 -BackupFile .\backups\nghcc-admin-db-yyyyMMdd-HHmmss.sql
```

## 注意事項

- `backups/` 內的實際備份檔不會提交到 Git。
- 不要刪除 Docker volume，除非已確認備份可還原。
- 若部署到 `192.168.16.240`，請在主機本地執行備份，避免網路中斷造成備份不完整。
