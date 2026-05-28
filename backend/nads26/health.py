from django.db import connection
from django.http import JsonResponse


def health_check(request):
    database_status = "unknown"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_status = "ok"
    except Exception as exc:
        database_status = f"error: {exc.__class__.__name__}"

    return JsonResponse(
        {
            "app": "北門行政作業平台",
            "database": database_status,
        },
        json_dumps_params={"ensure_ascii": False},
    )
