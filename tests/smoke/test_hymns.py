from modules.hymns.models import Hymn


def test_hymns_page_is_available(logged_in_client):
    response = logged_in_client.get("/hymns/")

    assert response.status_code == 200


def test_hymns_table_has_restored_data():
    assert Hymn.objects.count() >= 2958
