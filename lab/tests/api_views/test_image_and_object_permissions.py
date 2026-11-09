import pytest
from django.test import Client

from euphro_auth.tests.factories import LabAdminUserFactory
from lab.models import ObjectGroup
from lab.objects.models import RunObjectGroup, RunObjetGroupImage
from lab.tests import factories


@pytest.mark.parametrize("method", ["get", "post"])
def test_run_object_group_image_permissions(project_api_context, method):
    context = project_api_context
    group = RunObjectGroup.objects.create(
        run=context.run, objectgroup=factories.ObjectGroupFactory()
    )
    image = RunObjetGroupImage.objects.create(run_object_group=group, path="old.jpg")
    other_group = RunObjectGroup.objects.create(
        run=factories.RunFactory(), objectgroup=group.objectgroup
    )
    RunObjetGroupImage.objects.create(run_object_group=other_group, path="other.jpg")
    response = getattr(context.client, method)(
        f"/api/lab/run_objectgroups/{group.id}/images",
        (
            {"path": "new.jpg", "transform": {"width": 100, "height": 100}}
            if method == "post"
            else {}
        ),
        content_type="application/json",
    )
    assert response.status_code == (
        (201 if method == "post" else 200) if context.can_access_project else 403
    )
    if method == "get" and context.can_access_project:
        assert [item["id"] for item in response.json()] == [image.id]
    assert RunObjetGroupImage.objects.filter(run_object_group=group).count() == (
        2 if method == "post" and context.can_access_project else 1
    )


def test_object_group_create_permissions(project_api_context):
    context = project_api_context
    allowed = bool(context.user and context.user.is_staff)
    response = context.client.post(
        "/api/lab/objectgroups",
        {"label": "New object"},
        content_type="application/json",
    )
    assert response.status_code == (201 if allowed else 403)
    assert ObjectGroup.objects.filter(label="New object").exists() == allowed


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("method", "url"),
    [
        ("get", "/api/lab/projects/99999999/participations/remote"),
        ("get", "/api/lab/projects/99999999/participations/on-premises"),
        ("get", "/api/lab/runs/99999999/measuring-points"),
        ("patch", "/api/lab/measuring-points/99999999/image"),
        ("get", "/api/lab/run_objectgroups/99999999/images"),
        ("get", "/api/standard/runs/99999999"),
        ("post", "/api/standard/measuring-points/99999999/standard"),
        ("patch", "/api/notebook/run-notebook/99999999"),
    ],
)
def test_missing_project_resources_return_not_found(method, url):
    client = Client()
    client.force_login(LabAdminUserFactory())
    response = getattr(client, method)(url, {}, content_type="application/json")
    assert response.status_code == 404
