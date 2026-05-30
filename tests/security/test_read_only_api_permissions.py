from dataclasses import dataclass

import pytest
from django.contrib.auth.models import User
from django.test import override_settings

from nads26.menu_permissions import user_has_menu_route


@dataclass(frozen=True)
class ApiEndpointPermission:
    app: str
    method: str
    path: str
    operation: str
    is_read_only: bool
    requires_authentication: bool
    requires_menu_permission: bool
    django_permission: str


READ_ONLY_API_PERMISSION_MATRIX = (
    ApiEndpointPermission("hymns", "GET", "/api/hymns/", "hymn-list", True, True, False, ""),
    ApiEndpointPermission("hymns", "GET", "/api/hymns/<pk>/", "hymn-detail", True, True, False, ""),
    ApiEndpointPermission("humnos", "POST", "/api/humnos/info/", "video-info", True, True, False, ""),
    ApiEndpointPermission("hymns", "POST", "/api/hymns/", "hymn-create", False, True, False, ""),
    ApiEndpointPermission("hymns", "PUT", "/api/hymns/<pk>/", "hymn-update", False, True, False, ""),
    ApiEndpointPermission("hymns", "DELETE", "/api/hymns/<pk>/", "hymn-delete", False, True, False, ""),
    ApiEndpointPermission("hymns", "POST", "/api/hymns/<pk>/upload/", "hymn-upload", False, True, False, ""),
    ApiEndpointPermission("humnos", "POST", "/api/humnos/download/", "video-download", False, True, False, ""),
)


def endpoints_for_app(app):
    return tuple(endpoint for endpoint in READ_ONLY_API_PERMISSION_MATRIX if endpoint.app == app)


def read_only_endpoints():
    return tuple(endpoint for endpoint in READ_ONLY_API_PERMISSION_MATRIX if endpoint.is_read_only)


def write_endpoints():
    return tuple(endpoint for endpoint in READ_ONLY_API_PERMISSION_MATRIX if not endpoint.is_read_only)


@pytest.fixture
def permission_matrix_user_without_menu():
    user = User.objects.filter(username="test_staff_nomenu").select_related("profile").first()
    if user is None:
        pytest.skip(
            "Missing local permission test account: test_staff_nomenu. "
            "Run scripts/create-test-accounts.sh or .ps1 first."
        )
    return user


def test_read_only_api_permission_matrix_covers_hymns_and_humnos():
    assert {
        (endpoint.app, endpoint.method, endpoint.path, endpoint.is_read_only)
        for endpoint in endpoints_for_app("hymns")
    } == {
        ("hymns", "GET", "/api/hymns/", True),
        ("hymns", "GET", "/api/hymns/<pk>/", True),
        ("hymns", "POST", "/api/hymns/", False),
        ("hymns", "PUT", "/api/hymns/<pk>/", False),
        ("hymns", "DELETE", "/api/hymns/<pk>/", False),
        ("hymns", "POST", "/api/hymns/<pk>/upload/", False),
    }

    assert {
        (endpoint.app, endpoint.method, endpoint.path, endpoint.is_read_only)
        for endpoint in endpoints_for_app("humnos")
    } == {
        ("humnos", "POST", "/api/humnos/info/", True),
        ("humnos", "POST", "/api/humnos/download/", False),
    }


def test_read_only_api_matrix_requires_login_but_not_page_menu_or_django_permission():
    for endpoint in read_only_endpoints():
        assert endpoint.requires_authentication is True
        assert endpoint.requires_menu_permission is False
        assert endpoint.django_permission == ""


def test_write_api_matrix_is_documented_but_left_without_new_enforcement():
    for endpoint in write_endpoints():
        assert endpoint.requires_authentication is True
        assert endpoint.requires_menu_permission is False
        assert endpoint.django_permission == ""


def test_anonymous_user_cannot_read_hymns_api(client):
    response = client.get("/api/hymns/?page_size=1")

    assert response.status_code in (401, 403)


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=True)
def test_hymns_read_only_api_does_not_reuse_page_menu_permission(
    client,
    permission_matrix_user_without_menu,
):
    assert user_has_menu_route(permission_matrix_user_without_menu, "/hymns/") is False

    client.force_login(permission_matrix_user_without_menu)
    response = client.get("/api/hymns/?page_size=1")

    assert response.status_code == 200


def test_anonymous_user_cannot_call_humnos_info_api(client):
    response = client.post(
        "/api/humnos/info/",
        data={"url": "https://example.test/watch?v=demo"},
        content_type="application/json",
    )

    assert response.status_code in (401, 403)


def test_logged_in_user_can_call_humnos_read_only_info_api(
    client,
    permission_matrix_user_without_menu,
    monkeypatch,
):
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

    client.force_login(permission_matrix_user_without_menu)
    response = client.post(
        "/api/humnos/info/",
        data={"url": "https://example.test/watch?v=demo&list=playlist"},
        content_type="application/json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Demo video"
    assert payload["url"] == "https://example.test/watch?v=demo"
