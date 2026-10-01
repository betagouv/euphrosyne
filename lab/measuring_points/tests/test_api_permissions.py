from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied

from lab.measuring_points.api.views import MeasuringPointImageCreateView
from lab.measuring_points.models import MeasuringPoint, MeasuringPointImage
from lab.objects.models import RunObjectGroup, RunObjetGroupImage
from lab.tests import factories


def test_measuring_point_list_permissions(project_api_context):
    context = project_api_context
    point = MeasuringPoint.objects.create(run=context.run, name="Initial point")
    MeasuringPoint.objects.create(
        run=factories.RunFactory(), name="Other project point"
    )
    response = context.client.get(f"/api/lab/runs/{context.run.id}/measuring-points")
    assert response.status_code == (200 if context.can_access_project else 403)
    if context.can_access_project:
        assert [item["id"] for item in response.json()] == [point.id]


def test_measuring_point_create_permissions(project_api_context):
    context = project_api_context
    response = context.client.post(
        f"/api/lab/runs/{context.run.id}/measuring-points",
        {"name": "New point", "comments": "New comments"},
        content_type="application/json",
    )
    assert response.status_code == (201 if context.can_access_project else 403)
    assert MeasuringPoint.objects.filter(run=context.run).exists() == (
        context.can_access_project
    )


@pytest.mark.parametrize("method", ["put", "patch"])
def test_measuring_point_update_permissions(project_api_context, method):
    context = project_api_context
    point = MeasuringPoint.objects.create(run=context.run, name="Initial point")
    response = getattr(context.client, method)(
        f"/api/lab/runs/{context.run.id}/measuring-points/{point.id}",
        {"name": "Updated point", "comments": "Updated comments"},
        content_type="application/json",
    )
    assert response.status_code == (200 if context.can_access_project else 403)
    point.refresh_from_db()
    assert point.name == (
        "Updated point" if context.can_access_project else "Initial point"
    )


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_measuring_point_image_permissions(project_api_context, method):
    context = project_api_context
    point = MeasuringPoint.objects.create(run=context.run, name="Point")
    group = RunObjectGroup.objects.create(
        run=context.run, objectgroup=factories.ObjectGroupFactory()
    )
    image = RunObjetGroupImage.objects.create(
        run_object_group=group, path="images/test.jpg"
    )
    if method != "post":
        MeasuringPointImage.objects.create(
            measuring_point=point,
            run_object_group_image=image,
            point_location={"x": 1},
        )
    response = getattr(context.client, method)(
        f"/api/lab/measuring-points/{point.id}/image",
        {"run_object_group_image": image.id, "point_location": {"x": 2}},
        content_type="application/json",
    )
    success = {"post": 201, "put": 200, "patch": 200, "delete": 204}[method]
    assert response.status_code == (success if context.can_access_project else 403)
    images = MeasuringPointImage.objects.filter(measuring_point=point)
    if method == "post":
        assert images.exists() == context.can_access_project
    elif method == "delete":
        assert images.exists() != context.can_access_project
    else:
        assert images.get().point_location == {
            "x": 2 if context.can_access_project else 1
        }


@pytest.mark.django_db
def test_measuring_point_image_get_object_checks_permissions():
    point = MeasuringPoint.objects.create(run=factories.RunFactory(), name="Point")
    group = RunObjectGroup.objects.create(
        run=point.run, objectgroup=factories.ObjectGroupFactory()
    )
    image = RunObjetGroupImage.objects.create(run_object_group=group, path="test.jpg")
    point_image = MeasuringPointImage.objects.create(
        measuring_point=point, run_object_group_image=image
    )
    view = MeasuringPointImageCreateView()
    view.kwargs = {"measuring_point_id": point.id}
    view.request = mock.sentinel.request
    with mock.patch.object(
        view, "check_object_permissions", side_effect=PermissionDenied
    ) as permission_check:
        with pytest.raises(PermissionDenied):
            view.get_object()
    permission_check.assert_called_once_with(view.request, point_image)
