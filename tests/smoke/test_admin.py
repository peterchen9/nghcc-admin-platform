def test_admin_page_opens_or_redirects_to_login(client):
    response = client.get("/admin/")

    assert response.status_code in (200, 302)


def test_admin_index_is_available_after_login(admin_client):
    response = admin_client.get("/admin/")

    assert response.status_code == 200
