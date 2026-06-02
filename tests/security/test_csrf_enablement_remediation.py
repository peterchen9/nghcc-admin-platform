import os

import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, override_settings


def _superuser_or_skip():
    user = User.objects.filter(is_active=True, is_superuser=True).first()
    if user is None:
        pytest.skip("Missing active superuser for CSRF enablement remediation tests.")
    return user


def _csrf_token_from_page(client, path="/users/"):
    response = client.get(path)
    assert response.status_code == 200
    token = response.cookies.get("csrftoken")
    assert token is not None
    return token.value


@pytest.mark.csrf
def test_humnos_page_uses_dual_csrf_cookie_fallback():
    client = Client(HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())

    response = client.get("/webav/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "function getCSRFToken()" in content
    assert "getCookie('cms26_csrftoken') || getCookie('csrftoken')" in content
    assert "'X-CSRFToken': getCSRFToken()" in content


@pytest.mark.csrf
def test_credentialed_core_pages_load_with_superuser():
    client = Client(HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())

    responses = [
        client.get("/admin/"),
        client.get("/users/"),
        client.get("/hymns/"),
        client.get("/webav/"),
    ]

    assert all(response.status_code == 200 for response in responses)


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF positive-path tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
@pytest.mark.csrf
def test_logout_post_with_csrf_token_logs_user_out():
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())
    token = _csrf_token_from_page(client)

    response = client.post(
        "/admin/logout/",
        {"csrfmiddlewaretoken": token},
        HTTP_REFERER="http://localhost/",
    )

    assert response.status_code in (200, 302)
    assert "_auth_user_id" not in client.session


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF positive-path tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
@pytest.mark.csrf
def test_humnos_info_post_accepts_dual_cookie_csrf_token(monkeypatch):
    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def extract_info(self, url, download=False):
            assert download is False
            return {
                "title": "Demo video",
                "duration": 123,
                "thumbnail": "https://example.test/thumb.jpg",
                "uploader": "Demo uploader",
            }

    monkeypatch.setattr("modules.humnos.views.yt_dlp.YoutubeDL", FakeYoutubeDL)

    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())
    token = _csrf_token_from_page(client, "/webav/")
    client.cookies["cms26_csrftoken"] = token

    response = client.post(
        "/api/humnos/info/",
        {"url": "https://example.test/watch?v=demo&list=playlist"},
        content_type="application/json",
        HTTP_X_CSRFTOKEN=token,
        HTTP_REFERER="http://localhost/webav/",
    )

    assert response.status_code == 200
    assert response.json()["url"] == "https://example.test/watch?v=demo"


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF CKEditor tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
@pytest.mark.csrf
def test_ckeditor_upload_rejects_missing_csrf_token(tmp_path):
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())
    upload = SimpleUploadedFile("csrf-check.txt", b"csrf check", "text/plain")

    with override_settings(MEDIA_ROOT=tmp_path, CKEDITOR_UPLOAD_PATH="ckeditor-test/"):
        response = client.post("/ckeditor/upload/", {"upload": upload})

    assert response.status_code == 403


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="CSRF CKEditor tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
@pytest.mark.csrf
def test_ckeditor_upload_accepts_valid_csrf_token(tmp_path):
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())
    token = _csrf_token_from_page(client)
    upload = SimpleUploadedFile("csrf-check.txt", b"csrf check", "text/plain")

    with override_settings(MEDIA_ROOT=tmp_path, CKEDITOR_UPLOAD_PATH="ckeditor-test/"):
        response = client.post(
            "/ckeditor/upload/",
            {"upload": upload},
            HTTP_X_CSRFTOKEN=token,
            HTTP_REFERER="http://localhost/users/",
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["uploaded"] == "1"
    assert payload["fileName"].endswith(".txt")
    assert payload["url"]
