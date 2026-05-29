# 遷移紀錄

## 來源系統

- 來源主機：`192.168.16.240`
- 來源網址：`http://192.168.16.240:26001`
- 來源路徑：`/home/apps1/nads26`
- 來源 Docker Compose：`/home/apps1/nads26/docker-compose.yml`
- 來源 web container：`nads26-web`
- 來源 database container：`nads26db`
- 來源 database：`nads26db`
- 來源 uploads/media：`/home/apps1/nads26/media`

## 目標本機專案

- 專案名稱：`nghcc-admin-platform`
- GitHub Repository：`peterchen9/nghcc-admin-platform`
- Docker Compose project：`nghcc-admin-platform`
- web container：`nghcc-admin-web`
- db container：`nghcc-admin-db`
- database：`nghcc_admin`
- local web port：`26001`
- internal web port：`8000`

## 已完成

- 已盤點 `.240` 上的 Docker、Compose、port、database、media 與 volume。
- 已建立本機 Docker 化專案骨架。
- 已保留舊系統核心 Django 程式於 `backend/`。
- 已建立備份方案與遠端備份指令。
- 已建立本機還原 DB 與 media 的作業方向。

## 尚未執行

- 尚未在 `.240` 實際產生正式備份檔。
- 尚未將 `.240` 的 6.0G media 完整拉回本機。
- 尚未用最新正式備份在全新空資料庫做一次完整還原演練。

## 注意事項

- 遠端 `.240` 是現行服務，不可任意停止或重啟。
- `mysql_data/` 不應作為唯一備份來源，應以 `mysqldump` 為主。
- `.env` 與 DB dump 均包含敏感資料，不可提交到 GitHub。
- media 檔案量約 `33827`，備份與下載時間需預留。
