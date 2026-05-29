import os
import sys

import django

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'nads26.settings')
django.setup()

from modules.menu.models import MenuItem


MENU_ITEMS = [
    {'id': 39, 'title': '崇拜禮儀', 'route': '', 'icon': '⛪', 'parent_id': None, 'order': 10},
    {'id': 40, 'title': '詩歌資料庫', 'route': '/hymns/', 'icon': '', 'parent_id': 39, 'order': 1},
    {'id': 41, 'title': '聚會活動', 'route': '', 'icon': '🎵', 'parent_id': None, 'order': 20},
    {'id': 42, 'title': '關懷', 'route': '', 'icon': '⚪', 'parent_id': None, 'order': 30},
    {'id': 43, 'title': 'Eureka!找人', 'route': '/eureka/', 'icon': '', 'parent_id': 42, 'order': 1},
    {'id': 44, 'title': '牧區小組', 'route': '/eureka/pastoral/', 'icon': '', 'parent_id': 42, 'order': 2},
    {'id': 45, 'title': '新朋友登記', 'route': '/eureka/add/', 'icon': '', 'parent_id': 42, 'order': 3},
    {'id': 46, 'title': '搜名單', 'route': '/eureka/modify/', 'icon': '', 'parent_id': 42, 'order': 4},
    {'id': 47, 'title': '同工', 'route': '', 'icon': '💼', 'parent_id': None, 'order': 40},
    {'id': 48, 'title': '交通', 'route': '', 'icon': '🚗', 'parent_id': None, 'order': 50},
    {'id': 49, 'title': '教育', 'route': '', 'icon': '🎓', 'parent_id': None, 'order': 60},
    {'id': 50, 'title': '場地設施', 'route': '', 'icon': '🏢', 'parent_id': None, 'order': 70},
    {'id': 51, 'title': '工具', 'route': '', 'icon': '🔧', 'parent_id': None, 'order': 80},
    {'id': 52, 'title': '網路影音下載', 'route': '/webav/', 'icon': '', 'parent_id': 51, 'order': 1},
    {'id': 53, 'title': '資訊網路', 'route': '', 'icon': '⚪', 'parent_id': None, 'order': 90},
    {'id': 54, 'title': '報到系統', 'route': '', 'icon': '📅', 'parent_id': None, 'order': 100},
    {'id': 55, 'title': '管理員', 'route': '', 'icon': '🛡️', 'parent_id': None, 'order': 110},
    {'id': 56, 'title': '財會', 'route': '', 'icon': '⚪', 'parent_id': None, 'order': 120},
    {'id': 57, 'title': '參考資料', 'route': '', 'icon': '📱', 'parent_id': None, 'order': 130},
    {'id': 58, 'title': '奉獻', 'route': '', 'icon': '⚪', 'parent_id': None, 'order': 140},
    {'id': 59, 'title': '使用者管理', 'route': '/users/', 'icon': '👤', 'parent_id': 55, 'order': 20},
    {'id': 60, 'title': '首頁內容編輯', 'route': '/pages/edit-home/', 'icon': '', 'parent_id': 55, 'order': 10},
    {'id': 61, 'title': '選單項目管理', 'route': '/admin/menu/menuitem/', 'icon': '', 'parent_id': 55, 'order': 30},
]


def sync_menu():
    source_ids = [item['id'] for item in MENU_ITEMS]
    MenuItem.objects.exclude(id__in=source_ids).delete()

    for item in MENU_ITEMS:
        MenuItem.objects.update_or_create(
            id=item['id'],
            defaults={
                'title': item['title'],
                'route': item['route'],
                'icon': item['icon'],
                'parent_id': item['parent_id'],
                'order': item['order'],
                'roles': '*',
                'is_active': True,
            },
        )
        print(f"同步選單：{item['id']} {item['title']}")


if __name__ == '__main__':
    sync_menu()
