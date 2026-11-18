from datetime import timedelta

import pytest
from allauth.mfa.totp.internal.auth import TOTP, generate_totp_secret
from django.urls import reverse
from django.utils import timezone

from lab.tests import factories as lab_factories

from .factories import LabAdminUserFactory, StaffUserFactory

pytestmark = pytest.mark.django_db

PROJECTS_URL = "/lab/project/"


@pytest.fixture(autouse=True)
def local_static_storage(settings):
    settings.STORAGES = {
        "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage"
        },
    }


@pytest.fixture(name="cgu_required")
def cgu_required_fixture(settings):
    settings.FORCE_LAST_CGU_ACCEPTANCE_DT = timezone.now()


@pytest.fixture(name="user")
def user_fixture():
    return StaffUserFactory(cgu_accepted_at=None)


def test_no_cgu_gate_when_acceptance_is_not_forced(client, user):
    client.force_login(user)
    assert client.get(PROJECTS_URL).status_code == 200


@pytest.mark.usefixtures("cgu_required")
def test_recent_acceptance_passes_the_cgu_gate(client, user):
    user.cgu_accepted_at = timezone.now() + timedelta(seconds=1)
    user.save()
    client.force_login(user)
    assert client.get(PROJECTS_URL).status_code == 200


@pytest.mark.usefixtures("cgu_required")
@pytest.mark.parametrize("accepted_days_ago", [None, 1])
def test_missing_or_expired_acceptance_redirects_to_cgu(
    client, user, accepted_days_ago
):
    if accepted_days_ago:
        user.cgu_accepted_at = timezone.now() - timedelta(days=accepted_days_ago)
        user.save()
    client.force_login(user)
    response = client.get(PROJECTS_URL)
    assert response.status_code == 302
    assert response.url == reverse("cgu_acceptance")


@pytest.mark.usefixtures("cgu_required")
def test_cgu_pages_and_logout_stay_reachable(client, user):
    client.force_login(user)
    assert client.get(reverse("cgu_acceptance")).status_code == 200
    assert client.get(reverse("static_cgu")).status_code == 200
    assert client.post(reverse("admin:logout")).status_code == 302


@pytest.mark.usefixtures("cgu_required")
def test_cgu_gate_answers_api_calls_with_json(client, user):
    client.force_login(user)
    response = client.post("/api/auth/token/")
    assert response.status_code == 403
    assert response.json()["code"] == "cgu_acceptance_required"
    assert response.json()["redirect_url"] == reverse("cgu_acceptance")
    assert response.json()["detail"]


@pytest.mark.usefixtures("cgu_required")
def test_mfa_gate_comes_before_cgu_gate(client, settings):
    settings.MFA_ADMIN_REQUIRED = True
    admin = LabAdminUserFactory(cgu_accepted_at=None)
    secret = generate_totp_secret()
    TOTP.activate(admin, secret)
    client.force_login(admin)

    response = client.get(PROJECTS_URL)
    assert response.url.startswith(reverse("account_login"))


def test_cgu_gate_comes_before_employer_gate(client, settings):
    project = lab_factories.ProjectFactory()
    user = StaffUserFactory(cgu_accepted_at=None)
    lab_factories.ParticipationFactory(
        user=user,
        project=project,
        on_premises=True,
        employer=None,
        institution=lab_factories.InstitutionFactory(ror_id="https://ror.org/non"),
    )
    client.force_login(user)
    project_url = reverse("admin:lab_project_change", args=[project.id])
    assert client.get(project_url).url == reverse(
        "participation_employer_completion", kwargs={"project_id": project.id}
    )
    settings.FORCE_LAST_CGU_ACCEPTANCE_DT = timezone.now()
    assert client.get(project_url).url == reverse("cgu_acceptance")
