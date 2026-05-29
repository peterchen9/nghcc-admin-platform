import pytest
from django.contrib.auth.models import User


@pytest.mark.parametrize(
    "path",
    [
        "/eureka/",
        "/hymns/",
        "/webav/",
        "/users/",
        "/pages/edit-home/",
    ],
)
def test_anonymous_user_cannot_open_login_required_pages(client, path):
    response = client.get(path)

    assert response.status_code in (302, 403)


def test_logged_in_user_can_open_allowed_core_pages(logged_in_client):
    for path in ["/eureka/", "/hymns/", "/webav/"]:
        response = logged_in_client.get(path)
        assert response.status_code == 200


def test_non_staff_user_cannot_enter_django_admin(client):
    user = User.objects.filter(is_active=True, is_staff=False).first()
    if user is None:
        pytest.skip("目前本機還原資料沒有非 staff 使用者可供唯讀驗證。")

    client.force_login(user)
    response = client.get("/admin/")

    assert response.status_code in (302, 403)


@pytest.mark.parametrize(
    "path",
    [
        "/users/",
        "/users/routes/",
        "/users/create/",
        "/users/1/permissions/",
        "/users/1/delete/",
    ],
)
def test_user_management_urls_reject_anonymous_user(client, path):
    response = client.get(path)

    assert response.status_code in (302, 401, 403, 405)


def test_user_routes_api_rejects_anonymous_user(client):
    response = client.get("/users/routes/")

    assert response.status_code in (302, 401, 403)
