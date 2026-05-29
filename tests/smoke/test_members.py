from modules.eureka.models import Member


def test_members_page_is_available(logged_in_client):
    response = logged_in_client.get("/eureka/")

    assert response.status_code == 200


def test_members_table_has_restored_data():
    assert Member.objects.count() >= 7895
