import pytest
from django.urls import reverse
from django.utils import timezone

from .. import factories as auth_factories


@pytest.mark.django_db
def test_cgu_acceptance_view_get(client):
    user = auth_factories.StaffUserFactory(cgu_accepted_at=None)
    client.force_login(user)

    response = client.get(reverse("cgu_acceptance"))

    assert response.status_code == 200
    assert "euphro_auth/cgu_acceptance.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_cgu_acceptance_view_post(client):
    user = auth_factories.StaffUserFactory(cgu_accepted_at=None)
    client.force_login(user)

    request_time = timezone.now()
    response = client.post(reverse("cgu_acceptance"), {"accept_cgu": True})

    user.refresh_from_db()
    assert response.status_code == 302
    assert response.url == "/"
    assert user.cgu_accepted_at is not None
    assert request_time <= user.cgu_accepted_at <= timezone.now()


@pytest.mark.django_db
def test_cgu_acceptance_view_post_when_no_checkbox(client):
    user = auth_factories.StaffUserFactory(cgu_accepted_at=None)
    client.force_login(user)

    response = client.post(reverse("cgu_acceptance"))

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.cgu_accepted_at is None
