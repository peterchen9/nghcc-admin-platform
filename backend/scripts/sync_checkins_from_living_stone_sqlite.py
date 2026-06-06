import argparse
import os
import sqlite3
import sys
from pathlib import Path

import django
from django.db import connection, transaction


BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.append(str(BASE_DIR))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nads26.settings")
django.setup()


def fetch_source_rows(sqlite_path):
    source = sqlite3.connect(sqlite_path)
    source.row_factory = sqlite3.Row
    try:
        return source.execute(
            """
            SELECT id, t_check_in, church_id, is_qr_code
            FROM check_in_checkinrecord
            WHERE t_check_in IS NOT NULL
              AND church_id IS NOT NULL
            ORDER BY id
            """
        ).fetchall()
    finally:
        source.close()


def get_existing_by_raw_id(raw_ids):
    if not raw_ids:
        return {}

    existing = {}
    chunk_size = 1000
    with connection.cursor() as cursor:
        for start in range(0, len(raw_ids), chunk_size):
            chunk = raw_ids[start:start + chunk_size]
            placeholders = ", ".join(["%s"] * len(chunk))
            cursor.execute(
                f"""
                SELECT raw_id, church_id, timestamp
                FROM checkin_records
                WHERE raw_id IN ({placeholders})
                """,
                chunk,
            )
            for raw_id, church_id, timestamp in cursor.fetchall():
                existing[int(raw_id)] = {
                    "church_id": church_id,
                    "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S") if timestamp else None,
                }
    return existing


def normalize_timestamp(value):
    return str(value).split(".")[0]


def build_plan(source_rows, existing_by_raw_id):
    inserts = []
    updates = []
    unchanged = 0

    for row in source_rows:
        raw_id = int(row["id"])
        timestamp = normalize_timestamp(row["t_check_in"])
        church_id = int(row["church_id"])
        device_id = "living_stone_qr" if row["is_qr_code"] else "living_stone_manual"
        existing = existing_by_raw_id.get(raw_id)

        if existing is None:
            inserts.append((church_id, timestamp, device_id, raw_id))
            continue

        if existing["church_id"] != church_id or existing["timestamp"] != timestamp:
            updates.append((church_id, timestamp, device_id, raw_id))
        else:
            unchanged += 1

    return inserts, updates, unchanged


def apply_plan(inserts, updates):
    with transaction.atomic():
        with connection.cursor() as cursor:
            if updates:
                cursor.executemany(
                    """
                    UPDATE checkin_records
                    SET church_id = %s,
                        timestamp = %s,
                        device_id = %s
                    WHERE raw_id = %s
                    """,
                    updates,
                )
            if inserts:
                cursor.executemany(
                    """
                    INSERT INTO checkin_records (church_id, timestamp, device_id, raw_id)
                    VALUES (%s, %s, %s, %s)
                    """,
                    inserts,
                )


def main():
    parser = argparse.ArgumentParser(
        description="Sync check-in records from Living Stone barcode SQLite into local checkin_records."
    )
    parser.add_argument("sqlite_path", help="Path to living_stone_barcode/nghc_daka/db.sqlite3")
    parser.add_argument("--apply", action="store_true", help="Write changes. Default is dry-run.")
    args = parser.parse_args()

    source_rows = fetch_source_rows(args.sqlite_path)
    raw_ids = [int(row["id"]) for row in source_rows]
    existing_by_raw_id = get_existing_by_raw_id(raw_ids)
    inserts, updates, unchanged = build_plan(source_rows, existing_by_raw_id)

    timestamps = [normalize_timestamp(row["t_check_in"]) for row in source_rows]
    print(f"source_rows={len(source_rows)}")
    print(f"source_first={min(timestamps) if timestamps else '-'}")
    print(f"source_last={max(timestamps) if timestamps else '-'}")
    print(f"existing_raw_ids={len(existing_by_raw_id)}")
    print(f"unchanged={unchanged}")
    print(f"updates={len(updates)}")
    print(f"inserts={len(inserts)}")

    if not args.apply:
        print("dry_run=true")
        return

    apply_plan(inserts, updates)
    print("applied=true")


if __name__ == "__main__":
    main()
