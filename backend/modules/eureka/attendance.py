from collections import defaultdict
from datetime import timedelta

from django.db.models import Count, DateField, F, Func, IntegerField
from django.utils import timezone

from .models import CheckinRecord


ATTENDANCE_START_YEAR = 2021
MIN_WORSHIP_CHECKINS = 50
RECENT_WEEKS = 52
WORSHIP_DATES_CACHE_SECONDS = 300
NO_ATTENDANCE_RECORDS = "No records"
SOURCE_LABEL = "Realtime: checkin_records Sunday check-ins"

_worship_dates_cache = {
    "expires_at": None,
    "value": None,
}


def _fetch_worship_dates_uncached():
    """Return observed Sunday worship dates from raw check-in records."""
    rows = (
        CheckinRecord.objects
        .filter(
            timestamp__isnull=False,
            church_id__isnull=False,
        )
        .annotate(
            raw_year=Func(F("timestamp"), function="YEAR", output_field=IntegerField()),
            raw_week_day=Func(F("timestamp"), function="DAYOFWEEK", output_field=IntegerField()),
            worship_date=Func(F("timestamp"), function="DATE", output_field=DateField()),
        )
        .filter(
            raw_year__gte=ATTENDANCE_START_YEAR,
            raw_week_day=1,
        )
        .values("worship_date")
        .annotate(people_count=Count("church_id", distinct=True))
        .filter(people_count__gte=MIN_WORSHIP_CHECKINS)
        .order_by("worship_date")
    )
    return [row["worship_date"] for row in rows]


def _fetch_worship_dates():
    now = timezone.now()
    if (
        _worship_dates_cache["value"] is not None
        and _worship_dates_cache["expires_at"] is not None
        and _worship_dates_cache["expires_at"] > now
    ):
        return _worship_dates_cache["value"]

    worship_dates = _fetch_worship_dates_uncached()
    _worship_dates_cache["value"] = worship_dates
    _worship_dates_cache["expires_at"] = now + timedelta(seconds=WORSHIP_DATES_CACHE_SECONDS)
    return worship_dates


def _fetch_member_attendance_dates(church_ids, worship_dates):
    if not church_ids or not worship_dates:
        return defaultdict(set)

    rows = (
        CheckinRecord.objects
        .filter(church_id__in=church_ids)
        .annotate(worship_date=Func(F("timestamp"), function="DATE", output_field=DateField()))
        .filter(worship_date__in=worship_dates)
        .values_list("church_id", "worship_date")
        .distinct()
    )

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
            "display": " ".join(display_items) if display_items else NO_ATTENDANCE_RECORDS,
            "latest_source_date": latest_source_date,
            "source_label": SOURCE_LABEL,
        }

    return summaries


def get_attendance_summary(church_id):
    return get_attendance_summaries([church_id]).get(
        int(church_id),
        {
            "yearly": [],
            "blocks": [],
            "display": NO_ATTENDANCE_RECORDS,
            "latest_source_date": None,
            "source_label": SOURCE_LABEL,
        },
    )
