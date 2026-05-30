import pytest
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser, User
from django.test import override_settings

from nads26.menu_permissions import user_has_menu_route


MATRIX_USERNAMES = {
    "superuser": "test_superuser",
    "staff_with_menu": "test_staff_menu",
    "staff_without_menu": "test_staff_nomenu",
    "normal_user": "test_user",
}


@pytest.fixture
def permission_matrix_users():
    users = {
        role: User.objects.filter(username=username).select_related("profile").first()
        for role, username in MATRIX_USERNAMES.items()
    }
    missing = [username for role, username in MATRIX_USERNAMES.items() if users[role] is None]
    if missing:
        pytest.skip(
            "Missing local permission test accounts: "
            + ", ".join(missing)
            + ". Run scripts/create-test-accounts.sh or .ps1 first."
        )
    return users


def test_permission_matrix_flags(permission_matrix_users):
    assert permission_matrix_users["superuser"].is_superuser
    assert permission_matrix_users["superuser"].is_staff

    assert permission_matrix_users["staff_with_menu"].is_staff
    assert not permission_matrix_users["staff_with_menu"].is_superuser

    assert permission_matrix_users["staff_without_menu"].is_staff
    assert not permission_matrix_users["staff_without_menu"].is_superuser

    assert not permission_matrix_users["normal_user"].is_staff
    assert not permission_matrix_users["normal_user"].is_superuser


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("superuser", True),
        ("staff_with_menu", True),
        ("staff_without_menu", False),
        ("normal_user", False),
    ],
)
def test_menu_permission_matrix(permission_matrix_users, role, expected):
    assert user_has_menu_route(permission_matrix_users[role], "/webav/") is expected


def test_anonymous_user_fails_menu_permission():
    assert user_has_menu_route(AnonymousUser(), "/webav/") is False


def test_login_required_matrix(client, permission_matrix_users):
    anonymous_response = client.get("/api/hymns/")
    assert anonymous_response.status_code in (401, 403)

    client.force_login(permission_matrix_users["normal_user"])
    response = client.get("/api/hymns/")
    assert response.status_code == 200


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=True)
@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        ("superuser", 200),
        ("staff_with_menu", 200),
        ("staff_without_menu", 403),
        ("normal_user", 403),
    ],
)
def test_webav_menu_permission_enforcement(client, permission_matrix_users, role, expected_status):
    client.force_login(permission_matrix_users[role])
    response = client.get("/webav/")

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected"),
    [
        ("superuser", True),
        ("staff_with_menu", True),
        ("staff_without_menu", True),
        ("normal_user", False),
    ],
)
def test_staff_required_matrix(rf, permission_matrix_users, role, expected):
    request = rf.get("/admin/")
    request.user = permission_matrix_users[role]

    assert admin.site.has_permission(request) is expected


def test_anonymous_user_fails_staff_required_matrix(rf):
    request = rf.get("/admin/")
    request.user = AnonymousUser()

    assert admin.site.has_permission(request) is False


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        ("superuser", 200),
        ("staff_with_menu", 403),
        ("staff_without_menu", 403),
        ("normal_user", 403),
    ],
)
def test_superuser_required_api_matrix(client, permission_matrix_users, role, expected_status):
    client.force_login(permission_matrix_users[role])
    response = client.get("/users/routes/")

    assert response.status_code == expected_status


@pytest.mark.parametrize(
    ("role", "expected_status"),
    [
        ("superuser", 200),
        ("staff_with_menu", 403),
        ("staff_without_menu", 403),
        ("normal_user", 403),
    ],
)
def test_superuser_required_page_matrix(client, permission_matrix_users, role, expected_status):
    client.force_login(permission_matrix_users[role])
    response = client.get("/users/")

    assert response.status_code == expected_status
