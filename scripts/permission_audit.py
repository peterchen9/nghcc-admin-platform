import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, "/app")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nads26.settings")

import django

django.setup()

from django.contrib.auth.models import Group, Permission, User
from django.urls import URLPattern, URLResolver, get_resolver

from modules.menu.models import MenuItem


REPORT_JSON = "/app/reports/permission-audit.json"
REPORT_MD = "/app/reports/permission-audit.md"


def summarize_users():
    users = User.objects.all().order_by("id")
    active = users.filter(is_active=True)
    staff = users.filter(is_staff=True)
    superusers = users.filter(is_superuser=True)
    return {
        "total": users.count(),
        "active": active.count(),
        "inactive": users.filter(is_active=False).count(),
        "staff": staff.count(),
        "superusers": superusers.count(),
        "active_summary": {
            "first_id": active.first().id if active.exists() else None,
            "last_id": active.last().id if active.exists() else None,
        },
        "staff_user_ids": list(staff.values_list("id", flat=True)),
        "superuser_ids": list(superusers.values_list("id", flat=True)),
    }


def summarize_groups():
    groups = []
    for group in Group.objects.prefetch_related("permissions").order_by("name"):
        permissions = [
            f"{perm.content_type.app_label}.{perm.codename}"
            for perm in group.permissions.all().order_by("content_type__app_label", "codename")
        ]
        groups.append(
            {
                "name": group.name,
                "permission_count": len(permissions),
                "permissions": permissions,
            }
        )
    return groups


def summarize_menu():
    menu_items = []
    for item in MenuItem.objects.select_related("parent").order_by("parent_id", "order", "id"):
        allowed_user_count = item.userprofile_set.count()
        menu_items.append(
            {
                "id": item.id,
                "title": item.title,
                "route": item.route,
                "parent": item.parent.title if item.parent else "",
                "is_active": item.is_active,
                "roles": item.roles,
                "allowed_user_count": allowed_user_count,
            }
        )
    return menu_items


def view_flags(callback):
    callback_name = getattr(callback, "__name__", callback.__class__.__name__)
    module = getattr(callback, "__module__", "")
    view_class = getattr(callback, "view_class", None)
    if view_class:
        callback_name = view_class.__name__
        module = view_class.__module__

    permission_classes = [
        getattr(cls, "__name__", str(cls))
        for cls in getattr(callback, "cls", callback).__dict__.get("permission_classes", [])
    ]
    if not permission_classes:
        permission_classes = [
            getattr(cls, "__name__", str(cls))
            for cls in getattr(callback, "permission_classes", [])
        ]

    login_required = bool(getattr(callback, "login_url", None))
    return {
        "view": callback_name,
        "module": module,
        "login_required": login_required,
        "permission_classes": permission_classes,
        "staff_required": "admin" in module or callback_name.lower().startswith("admin"),
    }


def walk_patterns(patterns, prefix=""):
    rows = []
    for pattern in patterns:
        route = prefix + str(pattern.pattern)
        if isinstance(pattern, URLResolver):
            rows.extend(walk_patterns(pattern.url_patterns, route))
            continue
        if isinstance(pattern, URLPattern):
            flags = view_flags(pattern.callback)
            rows.append(
                {
                    "pattern": route,
                    "name": pattern.name or "",
                    **flags,
                }
            )
    return rows


def main():
    users = summarize_users()
    groups = summarize_groups()
    menu_items = summarize_menu()
    resolver_rows = walk_patterns(get_resolver().url_patterns)

    counts = {
        "users": users["total"],
        "active_users": users["active"],
        "staff_users": users["staff"],
        "superusers": users["superusers"],
        "groups": Group.objects.count(),
        "permissions": Permission.objects.count(),
        "user_permissions": User.user_permissions.through.objects.count(),
        "group_permissions": Group.permissions.through.objects.count(),
        "menu_permissions": sum(item["allowed_user_count"] for item in menu_items),
        "menu_items": len(menu_items),
        "active_menu_items": sum(1 for item in menu_items if item["is_active"]),
    }

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scope": "local only; no .240 access",
        "counts": counts,
        "users": users,
        "groups": groups,
        "menu_items": menu_items,
        "url_patterns": resolver_rows,
    }

    with open(REPORT_JSON, "w", encoding="utf-8") as fp:
        json.dump(report, fp, ensure_ascii=False, indent=2)

    group_rows = "\n".join(
        f"| {group['name']} | {group['permission_count']} | {', '.join(group['permissions']) or '無'} |"
        for group in groups
    )
    if not group_rows:
        group_rows = "| 無群組 | 0 | 無 |"

    menu_rows = "\n".join(
        "| {title} | {route} | {parent} | {roles} | {allowed_user_count} | {state} |".format(
            title=item["title"],
            route=item["route"] or "(父層或未設定)",
            parent=item["parent"] or "(root)",
            roles=item["roles"],
            allowed_user_count=item["allowed_user_count"],
            state="啟用" if item["is_active"] else "停用",
        )
        for item in menu_items
    )

    url_rows = "\n".join(
        "| {pattern} | {view} | {module} | {login} | {perms} | {staff} |".format(
            pattern=row["pattern"] or "/",
            view=row["view"],
            module=row["module"],
            login="是" if row["login_required"] else "否/需人工判斷",
            perms=", ".join(row["permission_classes"]) or "無明確標註",
            staff="是/疑似" if row["staff_required"] else "否/未標註",
        )
        for row in resolver_rows
        if not row["pattern"].startswith("admin/")
    )

    md = f"""# 本機權限盤點報表

產生時間：{report['generated_at']}

範圍：只讀查詢本機 Docker / MySQL，不連線 `.240`，不修改 DB。

## 統計

| 項目 | 數量 |
| --- | ---: |
| users | {counts['users']} |
| active users | {counts['active_users']} |
| staff users | {counts['staff_users']} |
| superusers | {counts['superusers']} |
| groups | {counts['groups']} |
| Django permissions | {counts['permissions']} |
| user permissions | {counts['user_permissions']} |
| group permissions | {counts['group_permissions']} |
| menu permissions | {counts['menu_permissions']} |
| menu items | {counts['menu_items']} |
| active menu items | {counts['active_menu_items']} |

## 群組權限

| 群組 | permission 數量 | permissions |
| --- | ---: | --- |
{group_rows}

## 選單權限摘要

| 選單 | route | parent | roles | 授權使用者數 | 狀態 |
| --- | --- | --- | --- | ---: | --- |
{menu_rows}

## URL/View 權限摘要

| URL pattern | View | Module | Login Required | Permission Required | Staff Required |
| --- | --- | --- | --- | --- | --- |
{url_rows}
"""

    with open(REPORT_MD, "w", encoding="utf-8") as fp:
        fp.write(md)

    print(json.dumps({"counts": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
