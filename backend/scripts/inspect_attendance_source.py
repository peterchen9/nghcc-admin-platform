import os

import pymysql


DEFAULT_HOSTS = [
    "host.docker.internal",
    "127.0.0.1",
    "192.168.16.225",
    "192.168.16.240",
    "172.20.60.241",
]

SOURCE_KEYWORDS = ("barcode", "checkin", "daka", "qr", "attend", "scan")


def connect(host, database=None):
    return pymysql.connect(
        host=host,
        port=int(os.getenv("SOURCE_DB_PORT", "3306")),
        user=os.getenv("SOURCE_DB_USER", "peter"),
        password=os.environ["SOURCE_DB_PASSWORD"],
        database=database,
        connect_timeout=5,
        read_timeout=10,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )


def list_databases(host):
    with connect(host) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW DATABASES")
            return [row["Database"] for row in cursor.fetchall()]


def list_candidate_tables(host, database):
    with connect(host, database=database) as conn:
        with conn.cursor() as cursor:
            cursor.execute("SHOW TABLES")
            key = f"Tables_in_{database}"
            tables = [row[key] for row in cursor.fetchall()]

            candidates = [
                table
                for table in tables
                if any(keyword in table.lower() for keyword in SOURCE_KEYWORDS)
            ]

            result = []
            for table in candidates:
                cursor.execute(f"SHOW COLUMNS FROM `{table}`")
                columns = [row["Field"] for row in cursor.fetchall()]
                cursor.execute(f"SELECT COUNT(*) AS row_count FROM `{table}`")
                row_count = cursor.fetchone()["row_count"]
                result.append((table, row_count, columns))
            return result


def main():
    if not os.getenv("SOURCE_DB_PASSWORD"):
        raise RuntimeError("SOURCE_DB_PASSWORD is required")

    hosts = os.getenv("SOURCE_DB_HOSTS")
    host_list = [h.strip() for h in hosts.split(",")] if hosts else DEFAULT_HOSTS

    for host in host_list:
        print(f"=== {host} ===")
        try:
            databases = list_databases(host)
        except Exception as exc:
            print(f"connect failed: {type(exc).__name__}: {str(exc)[:160]}")
            continue

        print("databases:", ", ".join(databases))
        for database in databases:
            if database in {"information_schema", "mysql", "performance_schema", "sys"}:
                continue
            try:
                candidates = list_candidate_tables(host, database)
            except Exception as exc:
                print(f"{database}: table scan failed: {type(exc).__name__}: {str(exc)[:120]}")
                continue

            for table, row_count, columns in candidates:
                print(f"{database}.{table}: rows={row_count}; columns={', '.join(columns)}")


if __name__ == "__main__":
    main()
