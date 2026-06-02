import pytest
from django.contrib.auth.models import User
from django.db.models import Max
from django.test import Client

from modules.eureka.models import Member


def _superuser_or_skip():
    user = User.objects.filter(is_active=True, is_superuser=True).first()
    if user is None:
        pytest.skip("Missing active superuser for Eureka delete method safety tests.")
    return user


@pytest.fixture
def eureka_member():
    next_id = (Member.objects.aggregate(Max("church_id"))["church_id__max"] or 900000000) + 1
    member = Member.objects.create(
        church_id=next_id,
        name=f"csrf-delete-member-{next_id}",
    )
    yield member
    Member.objects.filter(church_id=next_id).delete()


def _csrf_token_for_member(client, member):
    response = client.get(f"/eureka/modify/?key_word={member.name}")
    assert response.status_code == 200
    token = response.cookies.get("csrftoken")
    assert token is not None
    return token.value


@pytest.mark.csrf
def test_anonymous_user_cannot_delete_eureka_member(eureka_member):
    client = Client(HTTP_HOST="localhost")

    response = client.post(f"/eureka/modify/delete/{eureka_member.church_id}/")

    assert response.status_code == 302
    assert Member.objects.filter(church_id=eureka_member.church_id).exists()


@pytest.mark.csrf
def test_eureka_delete_get_is_method_not_allowed(eureka_member):
    client = Client(HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())

    response = client.get(f"/eureka/modify/delete/{eureka_member.church_id}/")

    assert response.status_code == 405
    assert Member.objects.filter(church_id=eureka_member.church_id).exists()


@pytest.mark.csrf
def test_eureka_delete_post_without_csrf_is_rejected(eureka_member):
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())

    response = client.post(f"/eureka/modify/delete/{eureka_member.church_id}/")

    assert response.status_code == 403
    assert Member.objects.filter(church_id=eureka_member.church_id).exists()


@pytest.mark.csrf
def test_eureka_delete_post_with_csrf_deletes_member(eureka_member):
    client = Client(enforce_csrf_checks=True, HTTP_HOST="localhost")
    client.force_login(_superuser_or_skip())
    token = _csrf_token_for_member(client, eureka_member)

    response = client.post(
        f"/eureka/modify/delete/{eureka_member.church_id}/",
        {"csrfmiddlewaretoken": token},
        HTTP_REFERER="http://localhost/eureka/modify/",
    )

    assert response.status_code == 302
    assert not Member.objects.filter(church_id=eureka_member.church_id).exists()
