from collections import defaultdict
from datetime import date

from django.db import connection


ATTENDANCE_START_YEAR = 2021
MIN_WORSHIP_CHECKINS = 50
RECENT_WEEKS = 52


def _fetch_worship_dates():
    """Return observed Sunday worship dates from raw check-in records."""
    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT DATE(timestamp) AS worship_date, COUNT(DISTINCT church_id) AS people_count
            FROM checkin_records
            WHERE timestamp IS NOT NULL
              AND church_id IS NOT NULL
              AND YEAR(timestamp) >= %s
              AND DAYOFWEEK(timestamp) = 1
            GROUP BY DATE(timestamp)
            HAVING people_count >= %s
            ORDER BY worship_date
            """,
            [ATTENDANCE_START_YEAR, MIN_WORSHIP_CHECKINS],
        )
        return [row[0] for row in cursor.fetchall()]


def _fetch_member_attendance_dates(church_ids, worship_dates):
    if not church_ids or not worship_dates:
        return defaultdict(set)

    church_placeholders = ", ".join(["%s"] * len(church_ids))
    date_placeholders = ", ".join(["%s"] * len(worship_dates))
    params = list(church_ids) + list(worship_dates)

    with connection.cursor() as cursor:
        cursor.execute(
            f"""
            SELECT church_id, DATE(timestamp) AS worship_date
            FROM checkin_records
            WHERE church_id IN ({church_placeholders})
              AND DATE(timestamp) IN ({date_placeholders})
            GROUP BY church_id, DATE(timestamp)
            """,
            params,
        )
        rows = cursor.fetchall()

    attended = defaultdict(set)
    for church_id, worship_date in rows:
        attended[int(church_id)].add(worship_date)
    return attended


def _rate(attended_count, total_count):
    if total_count <= 0:
        return None
    return round(attended_count * 100 / total_count)


def get_attendance_summaries(church_ids):
    """Calculate attendance summaries from raw checkin_records.

    The source data is treated as the authority. Precomputed members.percent_year,
    members.percent_12_month, and members.data_str are intentionally ignored.
    """
    normalized_ids = [int(church_id) for church_id in church_ids if church_id]
    if not normalized_ids:
        return {}

    worship_dates = _fetch_worship_dates()
    attended_by_member = _fetch_member_attendance_dates(normalized_ids, worship_dates)

    years = sorted({d.year for d in worship_dates})
    dates_by_year = {
        year: [d for d in worship_dates if d.year == year]
        for year in years
    }
    recent_dates = worship_dates[-RECENT_WEEKS:]
    latest_source_date = worship_dates[-1] if worship_dates else None

    summaries = {}
    for church_id in normalized_ids:
        attended_dates = attended_by_member.get(church_id, set())
        yearly = []
        for year in years:
            year_dates = dates_by_year[year]
            attended_count = sum(1 for d in year_dates if d in attended_dates)
            rate = _rate(attended_count, len(year_dates))
            if rate is not None:
                yearly.append(
                    {
                        "year": year,
                        "rate": rate,
                        "attended": attended_count,
                        "total": len(year_dates),
                    }
                )

        blocks = [
            {
                "date": d,
                "attended": d in attended_dates,
            }
            for d in recent_dates
        ]

        display_items = [f"{item['year']}:{item['rate']}%" for item in yearly[-3:]]
        summaries[church_id] = {
            "yearly": yearly,
            "blocks": blocks,
            "display": " ".join(display_items) if display_items else "無紀錄",
            "latest_source_date": latest_source_date,
            "source_label": "即時計算：checkin_records 主日報到",
        }

    return summaries


def get_attendance_summary(church_id):
    return get_attendance_summaries([church_id]).get(
        int(church_id),
        {
            "yearly": [],
            "blocks": [],
            "display": "無紀錄",
            "latest_source_date": None,
            "source_label": "即時計算：checkin_records 主日報到",
        },
    )
