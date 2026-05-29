from functools import wraps

from django.conf import settings
from django.core.exceptions import PermissionDenied

from modules.menu.models import MenuItem


def menu_permission_enforcement_enabled():
    return bool(getattr(settings, 'ENABLE_MENU_PERMISSION_ENFORCEMENT', False))


def user_has_menu_route(user, route):
    if not getattr(user, 'is_authenticated', False):
        return False
    if getattr(user, 'is_superuser', False):
        return True

    menu_item = MenuItem.objects.filter(route=route, is_active=True).first()
    if menu_item is None:
        return False

    try:
        return user.profile.allowed_menu_items.filter(id=menu_item.id, is_active=True).exists()
    except Exception:
        return False


def menu_permission_required(route):
    """實驗性 menu permission decorator；預設關閉，不影響正式行為。"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapped(request, *args, **kwargs):
            if not menu_permission_enforcement_enabled():
                return view_func(request, *args, **kwargs)
            if user_has_menu_route(request.user, route):
                return view_func(request, *args, **kwargs)
            raise PermissionDenied("您無權存取此功能。")

        return wrapped

    return decorator
