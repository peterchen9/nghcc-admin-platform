#!/usr/bin/env python3
"""Exercise common local API permission endpoints in report-only mode."""

from __future__ import annotations

import json
import logging
import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "nads26.settings")
sys.path.insert(0, "/app")

import django

django.setup()

from django.contrib.auth.models import User
from django.test import Client, override_settings


RAW_LOG = f"/app/reports/{os.environ.get('REPORT_RAW_LOG', 'api-permission-report-only.log')}"


def first_user(**filters):
    return User.objects.filter(is_active=True, **filters).order_by("id").first()


def request_json(client, method, path, payload):
    return getattr(client, method)(
        path,
        data=json.dumps(payload),
        content_type="application/json",
    )


def exercise_user(label, user):
    client = Client(HTTP_HOST="localhost")
    client.force_login(user)
    checks = [
        ("GET", "/api/hymns/", lambda: client.get("/api/hymns/?page=1&page_size=1")),
        ("POST", "/api/hymns/", lambda: client.post("/api/hymns/", data={"hymntitle": ""})),
        ("GET", "/api/hymns/999999/", lambda: client.get("/api/hymns/999999/")),
        (
            "PUT",
            "/api/hymns/999999/",
            lambda: request_json(
                client,
                "put",
                "/api/hymns/999999/",
                {"hymntitle": "Report-only no write"},
            ),
        ),
        ("DELETE", "/api/hymns/999999/", lambda: client.delete("/api/hymns/999999/")),
        ("POST", "/api/hymns/999999/upload/", lambda: client.post("/api/hymns/999999/upload/", data={})),
        ("POST", "/api/humnos/info/", lambda: request_json(client, "post", "/api/humnos/info/", {"url": ""})),
        (
            "POST",
            "/api/humnos/download/",
            lambda: request_json(client, "post", "/api/humnos/download/", {"url": ""}),
        ),
    ]
    for method, path, call in checks:
        response = call()
        print(f"{label},{user.username},{method},{path},{response.status_code}")


def main():
    normal_user = first_user(is_superuser=False) or first_user()
    superuser = first_user(is_superuser=True)
    if normal_user is None:
        raise SystemExit("No active local user found. Run scripts/create-test-accounts first.")

    logger = logging.getLogger("nads26.api_permissions")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler(RAW_LOG, mode="w", encoding="utf-8")
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)
    logger.propagate = False

    try:
        with override_settings(API_PERMISSION_MODE="report-only", ALLOWED_HOSTS=["localhost", "testserver"]):
            exercise_user("normal", normal_user)
            if superuser is not None and superuser.id != normal_user.id:
                exercise_user("superuser", superuser)
    finally:
        logger.removeHandler(handler)
        handler.close()

    print(f"wrote {RAW_LOG}")


if __name__ == "__main__":
    main()
