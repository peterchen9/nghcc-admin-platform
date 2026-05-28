# 既有系統盤點

盤點日期：2026-05-28  
既有服務位置：http://192.168.16.240:26001  
新 repository：`nghcc-admin-platform`

## 盤點原則

- 本階段只讀取既有系統狀態，不修改舊系統原始碼。
- 目前尚未取得可用 SSH 權限，因此檔案結構、實際部署路徑與資料庫檔案位置仍需後續補查。
- 本文件先記錄可由 HTTP、頁面內容與回應標頭確認的資訊。

## 可確認資訊

### HTTP 回應

- `GET /` 回傳 `200 OK`
- Server 標頭：`WSGIServer/0.2 CPython/3.11.14`
- Content-Type：`text/html; charset=utf-8`
- 頁面 title：`北門行政中心`
- 首頁主標題：`北門行政作業平台`
- 頁面內容提到：`這是從 DjangoCMS 移植過來的新系統`

### 技術架構判斷

- 後端：高度可能為 Django。
- Python：回應標頭顯示 CPython 3.11.14。
- 啟動方式：目前看起來像 Django development WSGI server，而不是 Gunicorn/uWSGI。
- 前端：伺服器端 rendered HTML template，搭配 inline CSS 與少量 JavaScript。
- 資料庫：尚無法由 HTTP 直接確認，待 SSH 或原始碼盤點。
- 套件管理：尚待確認，可能為 `requirements.txt`、Poetry 或其他 Python dependency 管理方式。

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

## 待補查項目

取得 192.168.16.240 的 SSH 權限後，需補查：

- 專案實際路徑
- Git 狀態與 remote
- Docker 或 systemd 啟動方式
- Django settings module
- `manage.py`、`requirements.txt`、`pyproject.toml` 或其他套件檔
- `.env`、環境變數與 secrets 保存方式
- database engine、database name、連線資訊與備份方式
- media/uploads 實際路徑
- static files 來源與收集方式
- 是否有 Celery、排程、背景工作或檔案轉換工具
- 既有資料備份策略

## 新專案整理決策

既有系統看起來不是前後端分離架構。為了後續維護與 Docker 化，本次新專案採用：

- `frontend/`：Nginx 靜態入口與 reverse proxy
- `backend/`：Django API、Admin 與未來業務邏輯
- `database/`：資料庫初始化與備份相關檔案預留
- `uploads/`：使用者上傳檔案持久化目錄
- `docs/`：盤點、開發、部署與除錯文件

