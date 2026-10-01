import pytest
from django.urls import reverse

from euphro_auth.tests.factories import StaffUserFactory
from lab.models import Participation
from lab.tests import factories


@pytest.mark.parametrize("participation_type", ["remote", "on-premises"])
def test_participation_list_permissions(project_api_context, participation_type):
    context = project_api_context
    participation = factories.ParticipationFactory(
        project=context.project, on_premises=participation_type == "on-premises"
    )
    other_participation = factories.ParticipationFactory(
        on_premises=participation_type == "on-premises"
    )
    url = reverse(
        f"api:project-{participation_type}-participation-list-create",
        kwargs={"project_id": context.project.id},
    )
    response = context.client.get(url)
    assert response.status_code == (200 if context.can_access_project else 403)
    if context.can_access_project:
        ids = [item["id"] for item in response.json()]
        assert participation.id in ids
        assert other_participation.id not in ids


@pytest.mark.parametrize("participation_type", ["remote", "on-premises"])
def test_participation_create_permissions(project_api_context, participation_type):
    context = project_api_context
    user = StaffUserFactory()
    url = reverse(
        f"api:project-{participation_type}-participation-list-create",
        kwargs={"project_id": context.project.id},
    )
    response = context.client.post(
        url,
        {"user": {"email": user.email}, "institution": {"name": "Test Institute"}},
        content_type="application/json",
    )
    assert response.status_code == (201 if context.can_manage_participations else 403)
    assert Participation.objects.filter(
        project=context.project, user=user
    ).exists() == (context.can_manage_participations)


@pytest.mark.parametrize("on_premises", [False, True])
@pytest.mark.parametrize("method", ["get", "put", "patch", "delete"])
def test_participation_detail_permissions(project_api_context, on_premises, method):
    context = project_api_context
    participation = factories.ParticipationFactory(
        project=context.project,
        on_premises=on_premises,
        institution=factories.InstitutionFactory(),
    )
    url = reverse(
        "api:project-remote-participation-retrieve-update-destroy",
        kwargs={"project_id": context.project.id, "pk": participation.id},
    )
    data = (
        {"on_premises": not on_premises}
        if method == "put"
        else {"institution": {"name": "Updated Institute"}}
    )
    allowed = (
        context.can_access_project
        if method == "get"
        else context.can_manage_participations
    )
    response = getattr(context.client, method)(
        url,
        data if method in {"put", "patch"} else {},
        content_type="application/json",
    )
    assert response.status_code == (
        (204 if method == "delete" else 200) if allowed else 403
    )
    if not allowed:
        participation.refresh_from_db()
        assert participation.institution.name != "Updated Institute"
        assert participation.on_premises == on_premises
    elif method == "put":
        participation.refresh_from_db()
        assert participation.on_premises != on_premises


def test_participation_from_another_project_is_not_returned(project_api_context):
    context = project_api_context
    participation = factories.ParticipationFactory()
    url = reverse(
        "api:project-remote-participation-retrieve-update-destroy",
        kwargs={"project_id": context.project.id, "pk": participation.id},
    )
    assert context.client.get(url).status_code == (
        404 if context.can_access_project else 403
    )
