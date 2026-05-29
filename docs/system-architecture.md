# 北門行政作業平台系統架構

更新日期：2026-05-29

## 分析範圍

本文件只描述本機 `nghcc-admin-platform` 在匯入正式資料庫與掛載正式 media 後的狀態，沒有部署、停止、重啟或修改 `192.168.16.240` 上的既有服務。

## 執行架構

北門行政作業平台目前是 Django 單體式 Web 系統，不是前後端分離架構。前端畫面由 Django template、靜態 CSS/JavaScript 與後端 view/API 共同提供。

本機 Docker Compose 設定：

| 項目 | 本機設定 |
| --- | --- |
| Compose project | `nghcc-admin-platform` |
| Web container | `nghcc-admin-web` |
| Web image | `nghcc-admin-platform-web` |
| Web 對外 port | `26001` |
| Web container port | `8000` |
| DB container | `nghcc-admin-db` |
| DB image | `mysql:8.0` |
| DB 對外 port | `26003` |
| DB container port | `3306` |
| Database | `nghcc_admin` |
| Media 掛載 | `./uploads:/app/media` |
| MySQL volume | `nghcc-admin-mysql-data:/var/lib/mysql` |

正式來源資訊：

| 項目 | 來源資訊 |
| --- | --- |
| 正式網址 | `http://192.168.16.240:26001` |
| 正式 Web container | `nads26-web` |
| 正式 DB container | `nads26db` |
| 正式 DB image | `mysql:8.0` |
| 正式 Compose project | `nads26` |
| 正式 compose 檔 | `/home/apps1/nads26/docker-compose.yml` |
| 正式 media 目錄 | `/home/apps1/nads26/media` |

## 程式結構

主要程式位於 `backend/`：

| 路徑 | 說明 |
| --- | --- |
| `backend/manage.py` | Django 管理入口 |
| `backend/nads26/settings.py` | Django 設定 |
| `backend/nads26/urls.py` | 全站 URL router |
| `backend/nads26/health.py` | 健康檢查端點 |
| `backend/nads26/middleware.py` | 自訂 middleware |
| `backend/modules/accounts/` | 使用者與權限管理 |
| `backend/modules/menu/` | 左側選單與選單權限 |
| `backend/modules/pages/` | 首頁與內容頁 |
| `backend/modules/eureka/` | 會員、關懷、新朋友與名單功能 |
| `backend/modules/hymns/` | 詩歌資料庫與檔案上傳 |
| `backend/modules/humnos/` | 網路影音下載 |
| `backend/templates/` | Django templates |
| `backend/scripts/` | 匯入、同步與初始化腳本 |

## 資料流

1. 使用者透過瀏覽器連到 `localhost:26001`。
2. `nghcc-admin-web` 以 Django 開發伺服器在 container 內提供 `8000`。
3. Django 依 `DB_HOST=db` 連到 `nghcc-admin-db`。
4. Django 使用 MySQL database `nghcc_admin`。
5. Media 檔案由 container 內 `/app/media` 對應到本機 `uploads/`。
6. 詩歌、會員照片、CKEditor 上傳檔案皆使用 media 目錄。

## 已完成還原驗證

| 項目 | 結果 |
| --- | --- |
| 正式 DB dump 匯入 | 成功 |
| Database tables | 52 |
| 使用者資料 | 5 筆 |
| 選單資料 | 23 筆，其中 22 筆啟用 |
| Django 權限 | 185 筆 |
| Media 解壓 | 已掛載，解出 33812 個檔案 |
| Web 容器 | 可啟動 |
| DB 容器 | healthy |
| `/api/health/` | HTTP 200 |
| `peter` 登入 | 成功 |
| `peterchen` 登入 | 成功 |
| 詩歌檔案上傳 | 成功，測試檔已清除 |

## Media 還原限制

正式 media 壓縮檔包含 33827 個一般檔案。本機 Windows bind mount 解壓後為 33812 個檔案，差異 15 個檔案，集中在 `eureka/photo/fish2/`。這比較像 Windows 檔案系統或 Docker bind mount 對特定中文檔名的處理限制，不代表正式主機資料遺失。

建議後續正式測試改用 Docker named volume、WSL2 Linux filesystem，或 Linux 主機還原，確保 media 檔名 100% 保真。

## 主要風險

1. Django 專案名稱仍為 `nads26`，本機 Docker 專案已更名，但程式命名尚未完全重構。
2. 部分資料表為 `managed = False`，schema 由正式 dump 決定，Django migration 不是完整來源。
3. `DisableCSRFMiddleware` 會弱化 CSRF 防護，需重新評估正式環境安全性。
4. 部分選單是功能佔位，尚未有對應 view/API，例如奉獻、財會、教育、報表型功能。
5. media 目前以 bind mount 掛載，本機 Windows 還原有檔名相容性缺口。
