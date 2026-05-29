def test_health_api_is_public_and_readonly(client):
    response = client.get("/api/health/")

    assert response.status_code == 200
    assert response.json()["database"] == "ok"


def test_hymns_api_is_available_for_logged_in_user(logged_in_client):
    response = logged_in_client.get("/api/hymns/?page_size=1")

    assert response.status_code == 200
    payload = response.json()
    assert "results" in payload
    assert len(payload["results"]) >= 1


def test_hymns_api_does_not_allow_anonymous_read(client):
    response = client.get("/api/hymns/?page_size=1")

    assert response.status_code in (302, 401, 403)


def test_user_routes_api_is_available_for_admin(admin_client):
    response = admin_client.get("/users/routes/")

    assert response.status_code == 200
    assert isinstance(response.json(), list)
