from dataclasses import dataclass
import json
import os

import pytest
from django.contrib.auth.models import User
from django.test import Client


@dataclass(frozen=True)
class WriteApiEndpoint:
    app: str
    method: str
    path: str
    operation: str
    requires_authentication: bool
    requires_superuser: bool
    csrf_sensitive: bool
    recommended_scope: str


WRITE_API_PERMISSION_MATRIX = (
    WriteApiEndpoint("hymns", "POST", "/api/hymns/", "create", True, False, True, "api:hymns:write"),
    WriteApiEndpoint("hymns", "PUT", "/api/hymns/<pk>/", "update", True, False, True, "api:hymns:write"),
    WriteApiEndpoint("hymns", "DELETE", "/api/hymns/<pk>/", "delete", True, False, True, "api:hymns:write"),
    WriteApiEndpoint("hymns", "POST", "/api/hymns/<pk>/upload/", "upload", True, False, True, "api:hymns:upload"),
    WriteApiEndpoint("humnos", "POST", "/api/humnos/download/", "download", True, False, True, "api:humnos:write"),
    WriteApiEndpoint("users", "POST", "/users/create/", "create", True, True, True, "api:users:write"),
    WriteApiEndpoint("users", "PUT/POST", "/users/<pk>/", "update", True, True, True, "api:users:write"),
    WriteApiEndpoint("users", "POST", "/users/<pk>/permissions/", "update-permissions", True, True, True, "api:users:write"),
    WriteApiEndpoint("users", "DELETE/POST", "/users/<pk>/delete/", "delete", True, True, True, "api:users:write"),
)


def _active_user_or_skip():
    user = User.objects.filter(is_active=True).first()
    if user is None:
        pytest.skip("Missing active local user for write API permission tests.")
    return user


def _superuser_or_skip():
    user = User.objects.filter(is_active=True, is_superuser=True).first()
    if user is None:
        pytest.skip("Missing active local superuser for write API permission tests.")
    return user


def test_write_api_matrix_covers_requested_operations():
    assert {(item.app, item.operation) for item in WRITE_API_PERMISSION_MATRIX} == {
        ("hymns", "create"),
        ("hymns", "update"),
        ("hymns", "delete"),
        ("hymns", "upload"),
        ("humnos", "download"),
        ("users", "create"),
        ("users", "update"),
        ("users", "update-permissions"),
        ("users", "delete"),
    }


def test_write_api_matrix_preserves_current_enforcement_boundaries():
    for endpoint in WRITE_API_PERMISSION_MATRIX:
        assert endpoint.requires_authentication is True
        assert endpoint.csrf_sensitive is True

    assert {
        (endpoint.app, endpoint.operation, endpoint.requires_superuser)
        for endpoint in WRITE_API_PERMISSION_MATRIX
        if endpoint.app in {"hymns", "humnos"}
    } == {
        ("hymns", "create", False),
        ("hymns", "update", False),
        ("hymns", "delete", False),
        ("hymns", "upload", False),
        ("humnos", "download", False),
    }

    assert all(
        endpoint.requires_superuser
        for endpoint in WRITE_API_PERMISSION_MATRIX
        if endpoint.app == "users"
    )


def test_write_api_recommended_scopes_are_explicit():
    assert {endpoint.recommended_scope for endpoint in WRITE_API_PERMISSION_MATRIX} == {
        "api:hymns:write",
        "api:hymns:upload",
        "api:humnos:write",
        "api:users:write",
    }


def test_anonymous_users_cannot_call_write_api_endpoints(client):
    responses = [
        client.post("/api/hymns/", data={"hymntitle": ""}),
        client.put("/api/hymns/999999/", data=json.dumps({"hymntitle": "No write"}), content_type="application/json"),
        client.delete("/api/hymns/999999/"),
        client.post("/api/hymns/999999/upload/", data={}),
        client.post("/api/humnos/download/", data={"url": ""}, content_type="application/json"),
        client.post("/users/create/", data={"username": "no-write", "password": "unused"}),
        client.post("/users/999999/", data={"username": "no-write"}),
        client.post("/users/999999/permissions/", data=json.dumps({"menu_ids": []}), content_type="application/json"),
        client.post("/users/999999/delete/", data={}),
    ]

    assert all(response.status_code in (401, 403) for response in responses)


def test_non_superuser_user_write_api_is_forbidden_for_user_management(client):
    user = User.objects.filter(is_active=True, is_superuser=False).first()
    if user is None:
        pytest.skip("Missing active non-superuser for user write API permission tests.")

    client.force_login(user)

    responses = [
        client.post("/users/create/", data={"username": "no-write", "password": "unused"}),
        client.post("/users/999999/", data={"username": "no-write"}),
        client.post("/users/999999/permissions/", data=json.dumps({"menu_ids": []}), content_type="application/json"),
        client.post("/users/999999/delete/", data={}),
    ]

    assert all(response.status_code == 403 for response in responses)


def test_logged_in_user_reaches_hymns_write_api_without_new_scope_enforcement(client):
    client.force_login(_active_user_or_skip())

    create_response = client.post("/api/hymns/", data={"hymntitle": ""})
    update_response = client.put(
        "/api/hymns/999999/",
        data=json.dumps({"hymntitle": "No write"}),
        content_type="application/json",
    )
    delete_response = client.delete("/api/hymns/999999/")
    upload_response = client.post("/api/hymns/999999/upload/", data={})

    assert create_response.status_code == 400
    assert update_response.status_code == 404
    assert delete_response.status_code == 404
    assert upload_response.status_code == 404


@pytest.mark.skipif(
    os.getenv("ENABLE_CSRF_PROTECTION", "").lower() not in {"1", "true", "yes", "on"},
    reason="Write API CSRF behavior tests run only in ENABLE_CSRF_PROTECTION=True mode.",
)
def test_csrf_enabled_rejects_write_api_requests_without_token():
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())

    responses = [
        client.post("/api/hymns/", data={"hymntitle": ""}),
        client.put("/api/hymns/999999/", data=json.dumps({"hymntitle": "No write"}), content_type="application/json"),
        client.delete("/api/hymns/999999/"),
        client.post("/api/hymns/999999/upload/", data={}),
        client.post("/api/humnos/download/", data={"url": ""}, content_type="application/json"),
        client.post("/users/create/", data={"username": "no-write", "password": "unused"}),
        client.post("/users/999999/", data={"username": "no-write"}),
        client.post("/users/999999/permissions/", data=json.dumps({"menu_ids": []}), content_type="application/json"),
        client.post("/users/999999/delete/", data={}),
    ]

    assert all(response.status_code == 403 for response in responses)
