import os

import pytest
from django.test import Client


@pytest.fixture(autouse=True)
def allow_existing_database_access(django_db_blocker):
    """Smoke tests read the already-restored local database, not a new test DB."""
    with django_db_blocker.unblock():
        yield


@pytest.fixture
def client():
    return Client(HTTP_HOST="localhost")


@pytest.fixture
def logged_in_client(client):
    username = os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_PASSWORD")
    if not username or not password:
        pytest.skip("TEST_USERNAME and TEST_PASSWORD are required for login smoke tests.")

    assert client.login(username=username, password=password), "primary smoke test login failed"
    return client


@pytest.fixture
def admin_client(client):
    username = os.getenv("TEST_ADMIN_USERNAME") or os.getenv("TEST_USERNAME")
    password = os.getenv("TEST_ADMIN_PASSWORD") or os.getenv("TEST_PASSWORD")
    if not username or not password:
        pytest.skip("TEST_ADMIN_USERNAME/TEST_ADMIN_PASSWORD or TEST_USERNAME/TEST_PASSWORD are required.")

    assert client.login(username=username, password=password), "admin smoke test login failed"
    return client
