def test_health_endpoint_reports_database_ok(client):
    response = client.get("/api/health/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["database"] == "ok"
