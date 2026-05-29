import os
from urllib.parse import quote

import pytest
from django.conf import settings


def first_hymn_htm_filename():
    html_dir = os.path.join(settings.MEDIA_ROOT, "hymns", "html")
    if not os.path.isdir(html_dir):
        pytest.skip("本機 media volume 沒有 hymns/html 目錄。")

    for filename in os.listdir(html_dir):
        if filename.lower().endswith((".htm", ".html")):
            return filename

    pytest.skip("本機 media volume 沒有 HTM/HTML 詩歌檔可供唯讀測試。")


def hymn_resource_path():
    return f"/hymn_resources/htm/{quote(first_hymn_htm_filename())}"


def test_anonymous_user_cannot_read_hymn_resource(client):
    response = client.get(hymn_resource_path())

    assert response.status_code in (302, 403)


def test_logged_in_user_can_read_hymn_resource(logged_in_client):
    response = logged_in_client.get(hymn_resource_path())

    assert response.status_code == 200


@pytest.mark.parametrize("path", ["/hymns/", "/webav/", "/eureka/"])
def test_anonymous_user_cannot_open_core_pages(client, path):
    response = client.get(path)

    assert response.status_code in (302, 403)


def test_logged_in_user_can_open_current_core_pages(logged_in_client):
    for path in ["/hymns/", "/webav/", "/eureka/"]:
        response = logged_in_client.get(path)
        assert response.status_code == 200
