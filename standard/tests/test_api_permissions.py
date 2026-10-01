from unittest import mock

import pytest
from django.core.exceptions import PermissionDenied

from lab.measuring_points.models import MeasuringPoint
from lab.tests import factories
from standard.api.views import MeasuringPointStandardView
from standard.models import MeasuringPointStandard, Standard


def test_run_standard_list_permissions(project_api_context):
    context = project_api_context
    point = MeasuringPoint.objects.create(run=context.run, name="Point")
    association = MeasuringPointStandard.objects.create(
        measuring_point=point, standard=Standard.objects.create(label="Standard")
    )
    MeasuringPointStandard.objects.create(
        measuring_point=MeasuringPoint.objects.create(
            run=factories.RunFactory(), name="Other project point"
        ),
        standard=association.standard,
    )
    response = context.client.get(f"/api/standard/runs/{context.run.id}")
    assert response.status_code == (200 if context.can_access_project else 403)
    if context.can_access_project:
        assert [item["id"] for item in response.json()] == [association.id]


@pytest.mark.parametrize("method", ["get", "post", "put", "patch", "delete"])
def test_point_standard_permissions(project_api_context, method):
    context = project_api_context
    point = MeasuringPoint.objects.create(run=context.run, name="Point")
    old_standard = Standard.objects.create(label="Old standard")
    new_standard = Standard.objects.create(label="New standard")
    if method != "post":
        MeasuringPointStandard.objects.create(
            measuring_point=point, standard=old_standard
        )
    response = getattr(context.client, method)(
        f"/api/standard/measuring-points/{point.id}/standard",
        (
            {"standard": {"label": new_standard.label}}
            if method in {"post", "put", "patch"}
            else {}
        ),
        content_type="application/json",
    )
    success = {"get": 200, "post": 201, "put": 200, "patch": 200, "delete": 204}[method]
    assert response.status_code == (success if context.can_access_project else 403)
    associations = MeasuringPointStandard.objects.filter(measuring_point=point)
    if method == "post":
        assert associations.exists() == context.can_access_project
    elif method == "delete":
        assert associations.exists() != context.can_access_project
    else:
        changed = context.can_access_project and method in {"put", "patch"}
        assert associations.get().standard == (
            new_standard if changed else old_standard
        )


@pytest.mark.django_db
def test_point_standard_get_object_checks_permissions():
    point = MeasuringPoint.objects.create(run=factories.RunFactory(), name="Point")
    association = MeasuringPointStandard.objects.create(
        measuring_point=point, standard=Standard.objects.create(label="Standard")
    )
    view = MeasuringPointStandardView()
    view.kwargs = {"measuring_point_id": point.id}
    view.request = mock.sentinel.request
    with mock.patch.object(
        view, "check_object_permissions", side_effect=PermissionDenied
    ) as permission_check:
        with pytest.raises(PermissionDenied):
            view.get_object()
    permission_check.assert_called_once_with(view.request, association)
