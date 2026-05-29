import os

import pytest


def test_login_page_can_open(client):
    response = client.get("/admin/login/")

    assert response.status_code == 200


def test_primary_user_can_login(client):
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    if not username or not password:
        pytest.skip("TEST_USERNAME and TEST_PASSWORD are required.")

    assert client.login(username=username, password=password)


def test_secondary_user_can_login(client):
    username = os.getenv("TEST_USERNAME_SECONDARY")
    password = os.getenv("TEST_PASSWORD_SECONDARY")
    if not username or not password:
        pytest.skip("TEST_USERNAME_SECONDARY and TEST_PASSWORD_SECONDARY are required.")

    assert client.login(username=username, password=password)
