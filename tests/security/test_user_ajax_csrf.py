import json
import os

import pytest
from django.contrib.auth.models import User
from django.test import Client


def superuser_or_skip():
    user = User.objects.filter(is_active=True, is_superuser=True).first()
    if user is None:
        pytest.skip("本機還原資料沒有 active superuser 可供 CSRF 測試。")
    return user


def test_user_list_page_contains_csrf_token(admin_client):
    response = admin_client.get("/users/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'name="csrfmiddlewaretoken"' in content


def test_user_list_page_ajax_uses_csrf_header(admin_client):
    response = admin_client.get("/users/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "function getCSRFToken()" in content
    assert "function csrfHeaders(" in content
    assert "X-CSRFToken" in content


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="User AJAX CSRF behavior tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
def test_user_management_post_without_csrf_is_rejected():
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(superuser_or_skip())

    response = client.post(
        "/users/create/",
        data=json.dumps({"username": "csrf-check-only", "password": "unused"}),
        content_type="application/json",
    )

    assert response.status_code == 403


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="User AJAX CSRF behavior tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
def test_user_management_post_with_csrf_reaches_view_without_writing_data():
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    superuser = superuser_or_skip()
    client.force_login(superuser)

    page = client.get("/users/")
    token = page.cookies["csrftoken"].value
    response = client.post(
        "/users/create/",
        data=json.dumps({"username": superuser.username, "password": "unused"}),
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
    )

    assert response.status_code == 400
    assert response.status_code != 403
