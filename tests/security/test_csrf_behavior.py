import importlib
import os

import pytest
from django.test import Client


def reload_project_settings(monkeypatch, enabled):
    monkeypatch.setenv("ENABLE_CSRF_PROTECTION", "True" if enabled else "False")
    from nads26 import settings as project_settings

    return importlib.reload(project_settings)


def test_csrf_disabled_mode_keeps_compatibility_middleware(monkeypatch):
    project_settings = reload_project_settings(monkeypatch, enabled=False)

    assert project_settings.ENABLE_CSRF_PROTECTION is False
    assert "nads26.middleware.DisableCSRFMiddleware" in project_settings.MIDDLEWARE
    assert "django.middleware.csrf.CsrfViewMiddleware" not in project_settings.MIDDLEWARE


def test_csrf_enabled_mode_switches_to_django_middleware(monkeypatch):
    project_settings = reload_project_settings(monkeypatch, enabled=True)

    assert project_settings.ENABLE_CSRF_PROTECTION is True
    assert "django.middleware.csrf.CsrfViewMiddleware" in project_settings.MIDDLEWARE
    assert "nads26.middleware.DisableCSRFMiddleware" not in project_settings.MIDDLEWARE


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF behavior tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
def test_csrf_enabled_get_pages_still_open():
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")

    response = client.get("/admin/login/")

    assert response.status_code == 200


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF behavior tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
def test_csrf_enabled_rejects_login_post_without_token():
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")

    response = client.post("/admin/login/", {"username": "unused", "password": "unused"})

    assert response.status_code == 403


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF behavior tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
def test_csrf_enabled_allows_login_post_with_valid_token():
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    if not username or not password:
        pytest.skip("TEST_USERNAME and TEST_PASSWORD are required.")

    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    login_page = client.get("/admin/login/")
    token = login_page.cookies["csrftoken"].value

    response = client.post(
        "/admin/login/",
        {
            "username": username,
            "password": password,
            "csrfmiddlewaretoken": token,
            "next": "/admin/",
        },
        HTTP_REFERER="http://localhost/admin/login/",
    )

    assert response.status_code in (200, 302)
    assert response.status_code != 403
