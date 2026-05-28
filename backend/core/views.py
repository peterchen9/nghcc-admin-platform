import os

from django.db import connection
from django.http import JsonResponse


MODULES = [
    {"slug": "worship", "icon": "⛪", "name": "崇拜禮儀", "description": "詩歌資料庫、禮拜流程與禮儀資料整理。"},
    {"slug": "events", "icon": "🎵", "name": "聚會活動", "description": "聚會、活動與行政排程的後續整合入口。"},
    {"slug": "care", "icon": "◎", "name": "關懷", "description": "Eureka 找人、牧區小組與新朋友登記。"},
    {"slug": "coworkers", "icon": "💼", "name": "同工", "description": "同工資料、服事角色與權限盤點。"},
    {"slug": "traffic", "icon": "🚗", "name": "交通", "description": "交通服事與車輛相關資料。"},
    {"slug": "education", "icon": "🎓", "name": "教育", "description": "課程、訓練與教材資料。"},
    {"slug": "facility", "icon": "🏢", "name": "場地設施", "description": "場地、設備與借用流程。"},
    {"slug": "tools", "icon": "🔧", "name": "工具", "description": "網路影音下載等行政工具。"},
    {"slug": "admin", "icon": "🛡", "name": "管理員", "description": "使用者、選單與系統設定。"},
    {"slug": "finance", "icon": "◎", "name": "財會", "description": "財會與奉獻資料的待整理模組。"},
]


def health_check(request):
    database_status = "unknown"
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        database_status = "ok"
    except Exception as exc:
        database_status = f"error: {exc.__class__.__name__}"

    upload_dir = os.getenv("UPLOAD_DIR", "/app/uploads")
    os.makedirs(upload_dir, exist_ok=True)

    return JsonResponse(
        {
            "app": os.getenv("APP_NAME", "北門行政作業平台"),
            "environment": os.getenv("APP_ENV", "local"),
            "database": database_status,
            "upload_dir": upload_dir,
        }
    )


def modules(request):
    return JsonResponse(MODULES, safe=False)

