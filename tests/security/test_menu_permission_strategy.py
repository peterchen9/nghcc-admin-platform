from types import SimpleNamespace

from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.test import RequestFactory, override_settings

from modules.humnos import views as humnos_views
from nads26.menu_permissions import menu_permission_required, user_has_menu_route


class FakeAllowedMenuItems:
    def __init__(self, exists_result):
        self.exists_result = exists_result

    def filter(self, **kwargs):
        return self

    def exists(self):
        return self.exists_result


def fake_user(*, is_superuser=False, has_menu=False):
    return SimpleNamespace(
        is_authenticated=True,
        is_superuser=is_superuser,
        profile=SimpleNamespace(allowed_menu_items=FakeAllowedMenuItems(has_menu)),
    )


def poc_view(request):
    return HttpResponse("ok")


def request_for(user):
    request = RequestFactory().get("/hymns/")
    request.user = user
    return request


def webav_request_for(user):
    request = RequestFactory().get("/webav/")
    request.user = user
    return request


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=False)
def test_menu_enforcement_off_keeps_current_behavior():
    protected_view = menu_permission_required("/hymns/")(poc_view)
    response = protected_view(request_for(fake_user(has_menu=False)))

    assert response.status_code == 200


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=True)
def test_menu_enforcement_on_allows_user_with_menu_permission():
    protected_view = menu_permission_required("/hymns/")(poc_view)
    response = protected_view(request_for(fake_user(has_menu=True)))

    assert response.status_code == 200


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=True)
def test_menu_enforcement_on_denies_user_without_menu_permission():
    protected_view = menu_permission_required("/hymns/")(poc_view)

    try:
        protected_view(request_for(fake_user(has_menu=False)))
    except PermissionDenied:
        return

    raise AssertionError("menu_permission_required should deny users without menu permission.")


def test_superuser_passes_menu_route_check():
    assert user_has_menu_route(fake_user(is_superuser=True), "/hymns/")


def test_unknown_menu_route_is_not_allowed_for_regular_user():
    assert not user_has_menu_route(fake_user(has_menu=True), "/not-a-real-menu-route/")


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=False)
def test_webav_trial_route_keeps_default_behavior_when_flag_is_off(monkeypatch):
    monkeypatch.setattr(humnos_views, "render", lambda request, template: HttpResponse(template))

    response = humnos_views.humnos_page_view(webav_request_for(fake_user(has_menu=False)))

    assert response.status_code == 200
    assert response.content == b"humnos/humnos_page.html"


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=True)
def test_webav_trial_route_allows_user_with_menu_permission(monkeypatch):
    monkeypatch.setattr(humnos_views, "render", lambda request, template: HttpResponse(template))

    response = humnos_views.humnos_page_view(webav_request_for(fake_user(has_menu=True)))

    assert response.status_code == 200


@override_settings(ENABLE_MENU_PERMISSION_ENFORCEMENT=True)
def test_webav_trial_route_denies_user_without_menu_permission(monkeypatch):
    monkeypatch.setattr(humnos_views, "render", lambda request, template: HttpResponse(template))

    try:
        humnos_views.humnos_page_view(webav_request_for(fake_user(has_menu=False)))
    except PermissionDenied:
        return

    raise AssertionError("webav trial route should deny users without menu permission.")
