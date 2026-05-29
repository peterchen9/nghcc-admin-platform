import importlib

from django.conf import settings


def test_current_security_settings_are_configured():
    assert settings.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert settings.X_FRAME_OPTIONS == "SAMEORIGIN"
    assert settings.SESSION_COOKIE_HTTPONLY is True
    assert settings.CSRF_COOKIE_HTTPONLY is False


def test_debug_can_be_controlled_by_env(monkeypatch):
    monkeypatch.setenv("DJANGO_DEBUG", "1")
    from nads26 import settings as project_settings

    reloaded = importlib.reload(project_settings)

    assert reloaded.DEBUG is True


def test_allowed_hosts_can_be_controlled_by_env(monkeypatch):
    monkeypatch.setenv("DJANGO_ALLOWED_HOSTS", "localhost,example.test")
    from nads26 import settings as project_settings

    reloaded = importlib.reload(project_settings)

    assert reloaded.ALLOWED_HOSTS == ["localhost", "example.test"]


def test_cookie_and_security_settings_can_be_controlled_by_env(monkeypatch):
    monkeypatch.setenv("SESSION_COOKIE_SECURE", "true")
    monkeypatch.setenv("CSRF_COOKIE_SECURE", "true")
    monkeypatch.setenv("SESSION_COOKIE_HTTPONLY", "true")
    monkeypatch.setenv("CSRF_COOKIE_HTTPONLY", "false")
    monkeypatch.setenv("SECURE_CONTENT_TYPE_NOSNIFF", "true")
    monkeypatch.setenv("X_FRAME_OPTIONS", "DENY")
    from nads26 import settings as project_settings

    reloaded = importlib.reload(project_settings)

    assert reloaded.SESSION_COOKIE_SECURE is True
    assert reloaded.CSRF_COOKIE_SECURE is True
    assert reloaded.SESSION_COOKIE_HTTPONLY is True
    assert reloaded.CSRF_COOKIE_HTTPONLY is False
    assert reloaded.SECURE_CONTENT_TYPE_NOSNIFF is True
    assert reloaded.X_FRAME_OPTIONS == "DENY"
