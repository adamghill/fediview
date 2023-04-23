import pytest

from account.models import Instance


@pytest.mark.django_db
def test_login_get(client):
    assert Instance.objects.all().count() == 0

    response = client.get("/account/login")

    assert response.status_code == 200
    assert "Both read and write permissions" in response.content.decode()

    assert Instance.objects.all().count() == 0


@pytest.mark.django_db
@pytest.mark.integration
def test_login_post_invalid_instance_url(client):
    assert Instance.objects.all().count() == 0

    response = client.post("/account/login", data={"url": "fake-test-server"})

    assert response.status_code == 200
    assert "Invalid instance url" in response.content.decode()

    assert Instance.objects.all().count() == 0


@pytest.mark.django_db
@pytest.mark.integration
def test_login_post(client):
    assert Instance.objects.all().count() == 0

    response = client.post("/account/login", data={"url": "indieweb.social"})

    assert response.status_code == 302

    assert Instance.objects.all().count() == 1
