# 192.168.16.240:26001 伺服器盤點

盤點日期：2026-05-29  
盤點主機：`192.168.16.240`  
盤點網址：`http://192.168.16.240:26001`  
作業方式：僅執行查詢指令，未停止、未重啟、未修改遠端服務或設定。

## 結論

`192.168.16.240:26001` 目前是由 Docker container 對外映射提供服務。

- 對外 port：`26001`
- 監聽程序：`docker-proxy`
- Docker container：`nads26-web`
- 使用 image：`nads26-web`
- container 內部 port：`8000/tcp`
- port mapping：`0.0.0.0:26001->8000/tcp`、`[::]:26001->8000/tcp`
- Docker Compose project：`nads26`
- Compose 檔案：`/home/apps1/nads26/docker-compose.yml`
- Compose 工作目錄：`/home/apps1/nads26`
- Database container：`nads26db`
- Database image：`mysql:8.0`
- Database port：host `33069` -> container `3306`
- uploads/media：`/home/apps1/nads26/media`
- database volume：`/home/apps1/nads26/mysql_data`

## 指定指令結果摘要

### 1. `docker ps`

與 `26001` 直接相關的 container：

```text
CONTAINER ID   IMAGE        COMMAND                   STATUS       PORTS                                         NAMES
d4fb7ff50b98   nads26-web   "python manage.py ru…"   Up 2 hours   0.0.0.0:26001->8000/tcp, [::]:26001->8000/tcp   nads26-web
d31b55eb7250   mysql:8.0    "docker-entrypoint.s…"   Up 6 days    33060/tcp, 0.0.0.0:33069->3306/tcp             nads26db
```

### 2. `docker compose ls`

與 `26001` 對應的 Compose project：

```text
NAME    STATUS      CONFIG FILES
nads26  running(2)  /home/apps1/nads26/docker-compose.yml
```

### 3. `docker container ls --format "table {{.Names}}\t{{.Image}}\t{{.Ports}}"`

與 `26001` 直接相關的輸出：

```text
NAMES       IMAGE        PORTS
nads26-web  nads26-web   0.0.0.0:26001->8000/tcp, [::]:26001->8000/tcp
nads26db    mysql:8.0    33060/tcp, 0.0.0.0:33069->3306/tcp, [::]:33069->3306/tcp
```

### 4. `sudo lsof -i :26001`

```text
COMMAND       PID USER   FD   TYPE   DEVICE SIZE/OFF NODE NAME
docker-pr 3354730 root    7u  IPv4 48835057      0t0  TCP *:26001 (LISTEN)
docker-pr 3354738 root    7u  IPv6 48835058      0t0  TCP *:26001 (LISTEN)
```

### 5. `sudo netstat -tulpn | grep 26001`

```text
tcp   0  0 0.0.0.0:26001  0.0.0.0:*  LISTEN  3354730/docker-prox
tcp6  0  0 :::26001       :::*       LISTEN  3354738/docker-prox
```

## Docker Compose 內容摘要

Compose 檔案位置：

```text
/home/apps1/nads26/docker-compose.yml
```

服務：

- `db`
  - image：`mysql:8.0`
  - container_name：`nads26db`
  - volume：`./mysql_data:/var/lib/mysql`
  - port：`33069:3306`
  - restart：`always`
  - environment：含 MySQL root/user/password 設定，文件中已遮蔽密碼值
- `web`
  - build：`.`
  - container_name：`nads26-web`
  - command：`python manage.py runserver 0.0.0.0:8000`
  - volume：`.:/app`
  - port：`26001:8000`
  - depends_on：`db`
  - env_file：`.env`
  - restart：`always`

## Container Inspect 摘要

### `nads26-web`

```text
Name=/nads26-web
Image=nads26-web
StartedAt=2026-05-29T02:31:01.924585786Z
RestartCount=0
Mounts=bind:/home/apps1/nads26->/app
Compose project=nads26
Compose config=/home/apps1/nads26/docker-compose.yml
Compose working_dir=/home/apps1/nads26
Compose service=web
```

### `nads26db`

```text
Name=/nads26db
Image=mysql:8.0
StartedAt=2026-05-23T01:24:42.871837753Z
RestartCount=0
Mounts=bind:/home/apps1/nads26/mysql_data->/var/lib/mysql
Compose project=nads26
Compose config=/home/apps1/nads26/docker-compose.yml
Compose working_dir=/home/apps1/nads26
Compose service=db
```

## Volumes / Database / Uploads

### 程式與 uploads

- 專案目錄：`/home/apps1/nads26`
- web container 掛載：`/home/apps1/nads26` -> `/app`
- uploads/media 目錄：`/home/apps1/nads26/media`
- media 檔案數：`33827`
- 專案總大小：`6.3G`
- media 大小：`6.0G`

### Database

- DB container：`nads26db`
- DB image：`mysql:8.0`
- DB bind mount：`/home/apps1/nads26/mysql_data` -> `/var/lib/mysql`
- mysql_data 大小：`286M`
- mysql_data 檔案數：`234`
- database name：`nads26db`
- tables：`52`
- database data/index size：約 `15.72 MB`

## 安全備份判斷

可以安全備份，但建議採用「不停止服務」的線上備份方式，避免影響目前 `26001` 服務。

建議備份項目：

- 原始碼與設定：`/home/apps1/nads26`
- uploads/media：`/home/apps1/nads26/media`
- Docker Compose：`/home/apps1/nads26/docker-compose.yml`
- 環境設定：`/home/apps1/nads26/.env`
- 資料庫：使用 `mysqldump` 從 `nads26db` 匯出 `nads26db`

注意事項：

- 不建議在 MySQL container 正在執行時直接複製 `mysql_data` 作為唯一備份，可能產生不一致資料。
- 建議以 `mysqldump` 匯出資料庫，再另外備份 `media/` 與程式碼。
- `media/` 約 `6.0G`、檔案數約 `33827`，備份時間可能較長。
- `docker-compose.yml` 與 `.env` 含敏感資料，備份檔需妥善保護，不應提交到 GitHub。

## 判斷回答

- `26001` 是否由 Docker container 對外映射：是。
- container 名稱：`nads26-web`。
- 使用 image：`nads26-web`。
- 對應內部 port：`8000/tcp`。
- 是否有 `docker-compose.yml`：有。
- `docker-compose.yml` 位於哪個資料夾：`/home/apps1/nads26/docker-compose.yml`。
- 是否有 volumes / database / uploads：有。
  - web bind mount：`/home/apps1/nads26` -> `/app`
  - database bind mount：`/home/apps1/nads26/mysql_data` -> `/var/lib/mysql`
  - uploads/media：`/home/apps1/nads26/media`
- 是否可以安全備份：可以，建議用 `mysqldump` 搭配檔案層備份，不停止、不重啟服務。
