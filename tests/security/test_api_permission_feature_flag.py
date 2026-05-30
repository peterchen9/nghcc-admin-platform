import json
import logging

import pytest
from django.contrib.auth.models import User
from django.test import override_settings

from nads26.api_permissions import (
    API_PERMISSION_MODE_OFF,
    API_PERMISSION_MODE_REPORT_ONLY,
    API_PERMISSION_SCOPE_MAP,
    api_permission_enabled,
    get_api_permission_mode,
)


def _active_user_or_skip():
    user = User.objects.filter(is_active=True).first()
    if user is None:
        pytest.skip("Missing active local user for API permission feature flag tests.")
    return user


def _exercise_hymns_write_api(client):
    return {
        "create": client.post("/api/hymns/", data={"hymntitle": ""}).status_code,
        "update": client.put(
            "/api/hymns/999999/",
            data=json.dumps({"hymntitle": "No write"}),
            content_type="application/json",
        ).status_code,
        "delete": client.delete("/api/hymns/999999/").status_code,
        "upload": client.post("/api/hymns/999999/upload/", data={}).status_code,
    }


def _exercise_humnos_api(client):
    return {
        "info": client.post(
            "/api/humnos/info/",
            data={"url": ""},
            content_type="application/json",
        ).status_code,
        "download": client.post(
            "/api/humnos/download/",
            data={"url": ""},
            content_type="application/json",
        ).status_code,
    }


def test_api_permission_mode_defaults_to_off():
    assert get_api_permission_mode() == API_PERMISSION_MODE_OFF
    assert api_permission_enabled() is False


@override_settings(API_PERMISSION_MODE="report-only")
def test_api_permission_mode_report_only_is_recognized():
    assert get_api_permission_mode() == API_PERMISSION_MODE_REPORT_ONLY
    assert api_permission_enabled() is True


@override_settings(API_PERMISSION_MODE="unexpected")
def test_invalid_api_permission_mode_falls_back_to_off():
    assert get_api_permission_mode() == API_PERMISSION_MODE_OFF
    assert api_permission_enabled() is False


def test_api_permission_scope_mapping_covers_hymns_and_humnos():
    assert API_PERMISSION_SCOPE_MAP == {
        ("GET", "/api/hymns/"): "api:hymns:read",
        ("POST", "/api/hymns/"): "api:hymns:write",
        ("GET", "/api/hymns/<pk>/"): "api:hymns:read",
        ("PUT", "/api/hymns/<pk>/"): "api:hymns:write",
        ("DELETE", "/api/hymns/<pk>/"): "api:hymns:write",
        ("POST", "/api/hymns/<pk>/upload/"): "api:hymns:upload",
        ("POST", "/api/humnos/info/"): "api:humnos:read",
        ("POST", "/api/humnos/download/"): "api:humnos:write",
    }


def test_api_permission_off_preserves_hymns_write_api_responses(client):
    client.force_login(_active_user_or_skip())

    with override_settings(API_PERMISSION_MODE="off"):
        off_responses = _exercise_hymns_write_api(client)

    assert off_responses == {
        "create": 400,
        "update": 404,
        "delete": 404,
        "upload": 404,
    }


def test_api_permission_report_only_preserves_hymns_write_api_responses(client, caplog):
    client.force_login(_active_user_or_skip())

    with override_settings(API_PERMISSION_MODE="report-only"), caplog.at_level(
        logging.INFO,
        logger="nads26.api_permissions",
    ):
        report_only_responses = _exercise_hymns_write_api(client)

    assert report_only_responses == {
        "create": 400,
        "update": 404,
        "delete": 404,
        "upload": 404,
    }
    assert "mode=report-only" in caplog.text
    assert "scope=api:hymns:write" in caplog.text
    assert "scope=api:hymns:upload" in caplog.text


def test_api_permission_off_and_report_only_preserve_humnos_api_responses(client):
    client.force_login(_active_user_or_skip())

    with override_settings(API_PERMISSION_MODE="off"):
        off_responses = _exercise_humnos_api(client)
    with override_settings(API_PERMISSION_MODE="report-only"):
        report_only_responses = _exercise_humnos_api(client)

    assert off_responses == {"info": 400, "download": 400}
    assert report_only_responses == off_responses
