# 既有系統盤點

盤點日期：2026-05-28  
既有服務位置：http://192.168.16.240:26001  
新 repository：`nghcc-admin-platform`

## 盤點原則

- 本階段只讀取既有系統狀態，不修改舊系統原始碼。
- 已於 2026-05-28 取得 SSH 權限並完成唯讀盤點。
- SSH 盤點只執行讀取、inspect、dump stdout 串流到本機，未修改遠端舊系統內容。
- 敏感資訊只記錄鍵名與用途，不記錄密碼、secret 或 token。

## 可確認資訊

### HTTP 回應

- `GET /` 回傳 `200 OK`
- Server 標頭：`WSGIServer/0.2 CPython/3.11.14`
- Content-Type：`text/html; charset=utf-8`
- 頁面 title：`北門行政中心`
- 首頁主標題：`北門行政作業平台`
- 頁面內容提到：`這是從 DjangoCMS 移植過來的新系統`

### 技術架構判斷

- 後端：Django。
- Python：CPython 3.11.14，container image 為 `python:3.11-slim`。
- 啟動方式：Django development server，命令為 `python manage.py runserver 0.0.0.0:8000`。
- 前端：伺服器端 rendered HTML template，搭配 inline CSS 與少量 JavaScript。
- 資料庫：MySQL 8，Django engine 為 `django.db.backends.mysql`。
- 套件管理：`requirements.txt`。

## 可見功能模組

首頁側欄可見模組如下：

- 首頁
- 崇拜禮儀
  - 詩歌資料庫：`/hymns/`
- 聚會活動
- 關懷
  - Eureka!找人：`/eureka/`
  - 牧區小組：`/eureka/pastoral/`
  - 新朋友登記：`/eureka/add/`
  - 搜名單：`/eureka/modify/`
- 同工
- 交通
- 教育
- 場地設施
- 工具
  - 網路影音下載：`/webav/`
- 資訊網路
- 報到系統
- 管理員
- 財會
- 參考資料
- 奉獻
- 使用者管理：`/users/`

## 可見入口與路由

- `/`
- `/admin/login/`
- `/admin/pages/page/add/`
- `/hymns/`
- `/eureka/`
- `/eureka/pastoral/`
- `/eureka/add/`
- `/eureka/modify/`
- `/webav/`
- `/users/`

## 主機檔案層級盤點

### 主機與容器

- 主機：`192.168.16.240`
- hostname：`gino25`
- 使用者：`peter`
- OS：Ubuntu 22.04 系列，Linux kernel `6.8.0-111-generic`
- 舊系統容器：`nads26-web`
- 舊系統資料庫容器：`nads26db`
- Docker Compose project：`nads26`
- Compose 設定檔：`/home/apps1/nads26/docker-compose.yml`
- 專案工作目錄：`/home/apps1/nads26`
- 容器掛載：`/home/apps1/nads26` bind mount 到 `/app`
- 26001 port 映射：host `26001` -> container `8000`

### Docker Compose 摘要

- `db`
  - image：`mysql:8.0`
  - container：`nads26db`
  - volume：`./mysql_data:/var/lib/mysql`
  - port：`33069:3306`
  - restart：`always`
- `web`
  - build：`.`
  - container：`nads26-web`
  - command：`python manage.py runserver 0.0.0.0:8000`
  - volume：`.:/app`
  - port：`26001:8000`
  - env_file：`.env`
  - restart：`always`

### 重要檔案與目錄

- `manage.py`
- `nads26/settings.py`
- `nads26/urls.py`
- `nads26/wsgi.py`
- `nads26/asgi.py`
- `Dockerfile`
- `docker-compose.yml`
- `.env`
- `requirements.txt`
- `templates/`
- `modules/`
- `media/`
- `mysql_data/`

### 資料大小

- `/home/apps1/nads26`：約 `6.3G`
- `/home/apps1/nads26/media`：約 `6.0G`
- `/home/apps1/nads26/mysql_data`：約 `286M`
- MySQL database `nads26db`：約 `15.72MB`
- `db.sqlite3`：`0`
- media 檔案數：約 `33,824`

### requirements.txt

```text
Django>=5.0
djangorestframework
djangorestframework-simplejwt
django-cors-headers
mysqlclient
requests
pymysql
openpyxl
python-barcode==0.16.1
django-ckeditor
yt-dlp
```

### Django apps

- `rest_framework`
- `modules.accounts`
- `modules.menu`
- `modules.pages`
- `modules.humnos`
- `modules.hymns`
- `modules.eureka`
- `ckeditor`
- `ckeditor_uploader`

### 資料模型摘要

- `modules.accounts.models.UserProfile`
- `modules.accounts.models.SystemSetting`
- `modules.eureka.models.Member`
- `modules.hymns.models.Hymn`
- `modules.menu.models.MenuItem`
- `modules.pages.models.Page`

### 已確認路由

- `/admin/`
- `/users/`
- `/users/routes/`
- `/users/create/`
- `/users/<pk>/`
- `/users/<pk>/permissions/`
- `/users/<pk>/delete/`
- `/ckeditor/`
- `/api/humnos/info/`
- `/api/humnos/download/`
- `/api/hymns/`
- `/api/hymns/<pk>/`
- `/api/hymns/<pk>/upload/`
- `/hymn_resources/htm/<filename>`
- `/worship/hymns/`
- `/hymns/`
- `/webav/`
- `/eureka/`
- `/eureka/photo/<filename>`
- `/eureka/melos/<church_id>`
- `/eureka/neos`
- `/eureka/pastoral/`
- `/eureka/add/`
- `/eureka/add/download/`
- `/eureka/modify/`
- `/eureka/modify/download/`
- `/eureka/modify/duplicates/`
- `/eureka/modify/delete/<church_id>/`
- `/`
- `/p/<slug>/`

### 安全與維運觀察

- `DEBUG=True`
- `ALLOWED_HOSTS=['*']`
- 自訂 middleware：`nads26.middleware.DisableCSRFMiddleware`
- `django.middleware.csrf.CsrfViewMiddleware` 目前被註解
- 使用 Django development server 作為容器命令
- 舊系統目錄不是 Git repository

以上項目後續正式部署前應整理為 production 設定。

## 本機備份紀錄

已在本機 `backups/legacy-nads26/` 建立備份，該目錄已被 `.gitignore` 排除，不會提交：

- `nads26-source-no-media-mysql_data.tar.gz`
  - 內容：舊系統原始碼與設定檔
  - 排除：`media/`、`mysql_data/`、`.git/`、`__pycache__/`
- `nads26db-mysql-dump.sql.gz`
  - 內容：`nads26db` MySQL dump
  - 方式：透過 `mysqldump` 從容器 stdout 串流到本機，未在遠端落檔

`media/` 約 6.0G，尚未下載完整實體檔。正式遷移前需安排外接硬碟、NAS 或主機對主機複製流程完整備份。

## 本機複製紀錄

已將舊系統程式內容複製進新專案 `backend/`，保留舊系統主要目錄名稱：

- `nads26/`
- `modules/`
- `templates/`
- `scripts/`

未複製到 Git 的項目：

- `.env`
- `db.sqlite3`
- `mysql_data/`
- `media/` 實體檔
- `__pycache__/`
- `*.pyc`

已將舊系統 MySQL dump 匯入本機 `nghcc_admin_platform`，並改由新專案 Docker Compose 管理：

- `nghcc-admin-frontend`
- `nghcc-admin-backend`
- `nghcc-admin-db`

本機 `uploads/` 掛載到容器 `/app/media`，保留舊系統 media path。已建立主要 media 子目錄，但尚未複製 6.0G 實體檔。

## 待補查項目

- `media/` 完整檔案備份與校驗
- 舊系統資料匯入新專案的 migration plan
- 使用者帳號、權限與 menu permission 規則細節
- 背景同步腳本實際排程方式，例如 `scripts/sync_members_data.py`
- 影音下載工具 `yt-dlp` 的使用情境與風險控管

## 新專案整理決策

既有系統不是前後端分離架構。為了後續維護與 Docker 化，本次新專案採用：

- `frontend/`：Nginx 靜態入口與 reverse proxy
- `backend/`：Django API、Admin 與未來業務邏輯
- `database/`：資料庫初始化與備份相關檔案預留
- `uploads/`：使用者上傳檔案持久化目錄
- `docs/`：盤點、開發、部署與除錯文件

資料庫已調整為 MySQL 8，以貼近舊系統 `nads26db`，降低後續資料遷移成本。
