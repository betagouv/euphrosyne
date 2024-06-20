from unittest import mock

import pytest
from rest_framework.permissions import IsAdminUser

from ... import models
from ...api_views import run_objectgroup as views
from ...api_views import serializers
from .. import factories


@pytest.fixture(name="run")
def run_with_objectgroup():
    run = factories.RunFactory()
    run.run_object_groups.add(factories.ObjectGroupFactory())
    return run


def test_run_objectgroup_mixin_permissions():
    assert views.RunObjectGroupMixin.permission_classes == [IsAdminUser]


@pytest.mark.django_db
@pytest.mark.usefixtures("run")
def test_run_objectgroup_mixin_get_queryset_when_user():
    user = factories.StaffUserFactory()

    view = views.RunObjectGroupMixin()
    view.request = mock.MagicMock(user=user)

    assert view.get_queryset().count() == 0


@pytest.mark.django_db
def test_run_objectgroup_mixin_get_queryset_when_member(
    run: models.Run,
):
    user = factories.StaffUserFactory()
    run.project.members.add(user)

    view = views.RunObjectGroupMixin()
    view.request = mock.MagicMock(user=user)  # type: ignore
    assert view.get_queryset().count() == 1


@pytest.mark.django_db
@pytest.mark.usefixtures("run")
def test_run_objectgroup_mixin_get_queryset_when_admin():
    user = factories.LabAdminUserFactory()

    view = views.RunObjectGroupMixin()
    view.request = mock.MagicMock(user=user)
    assert view.get_queryset().count() == 1


def test_run_object_group_view_lookup_field():
    assert views.RunObjectGroupView().lookup_field == "run_id"


def test_run_object_group_view_get_serializer_class_when_create():
    view = views.RunObjectGroupView()
    view.request = mock.MagicMock(method="POST")
    assert view.get_serializer_class() == serializers.RunObjectGroupCreateSerializer


def test_run_object_group_view_get_serializer_class_when_list():
    view = views.RunObjectGroupView()
    view.request = mock.MagicMock(method="GET")
    assert view.get_serializer_class() == serializers.RunObjectGroupSerializer


@pytest.mark.django_db
def test_run_object_group_view_get_queryset(run: models.Run):
    view = views.RunObjectGroupView()
    view.request = mock.MagicMock()
    view.kwargs = {"run_id": run.id}
    assert view.get_queryset().count() == 1


@pytest.mark.django_db
def test_run_object_group_view_perform_create_when_admin(run: models.Run):
    view = views.RunObjectGroupView()
    view.kwargs = {"run_id": run.id}
    view.request = mock.MagicMock(user=factories.LabAdminUserFactory())

    objectgroup = factories.ObjectGroupFactory()
    serializer = serializers.RunObjectGroupCreateSerializer(
        data={"objectgroup": objectgroup.id}
    )
    serializer.is_valid()

    view.perform_create(serializer)
    assert models.Run.run_object_groups.through.objects.filter(
        objectgroup=objectgroup
    ).exists()


@pytest.mark.django_db
def test_run_object_group_view_perform_create_when_member(run: models.Run):
    user = factories.StaffUserFactory()
    view = views.RunObjectGroupView()
    view.kwargs = {"run_id": run.id}
    view.request = mock.MagicMock(user=user)

    run.project.members.add(user)

    objectgroup = factories.ObjectGroupFactory()
    serializer = serializers.RunObjectGroupCreateSerializer(
        data={"objectgroup": objectgroup.id}
    )
    serializer.is_valid()

    view.perform_create(serializer)

    assert models.Run.run_object_groups.through.objects.filter(
        objectgroup=objectgroup
    ).exists()


@pytest.mark.django_db
def test_run_object_group_view_perform_create_when_not_member(run: models.Run):
    user = factories.StaffUserFactory()
    view = views.RunObjectGroupView()
    view.kwargs = {"run_id": run.id}
    view.request = mock.MagicMock(user=user)

    objectgroup = factories.ObjectGroupFactory()
    serializer = serializers.RunObjectGroupCreateSerializer(
        data={"objectgroup": objectgroup.id}
    )
    serializer.is_valid()

    with pytest.raises(views.PermissionDenied):
        view.perform_create(serializer)


def test_run_object_group_available_view_lookup_field():
    assert views.RunObjectGroupAvailableListView().lookup_field == "run_id"


@pytest.mark.django_db
def test_run_object_group_available_view_get_queryset_when_admin():
    project = factories.ProjectFactory()
    view = views.RunObjectGroupAvailableListView()
    view.request = mock.MagicMock(user=factories.LabAdminUserFactory())

    run_1 = factories.RunFactory(project=project)
    run_2 = factories.RunFactory(project=project)

    objectgroup = factories.ObjectGroupFactory()
    run_1.run_object_groups.add(objectgroup)

    view.kwargs = {"run_id": run_2.id}
    assert view.get_queryset().count() == 1


@pytest.mark.django_db
def test_run_object_group_available_view_get_queryset_when_member():
    project = factories.ProjectFactory()
    user = factories.StaffUserFactory()
    project.members.add(user)

    view = views.RunObjectGroupAvailableListView()
    view.request = mock.MagicMock(user=user)

    run_1 = factories.RunFactory(project=project)
    run_2 = factories.RunFactory(project=project)

    objectgroup = factories.ObjectGroupFactory()
    run_1.run_object_groups.add(objectgroup)

    view.kwargs = {"run_id": run_2.id}
    assert view.get_queryset().count() == 1


@pytest.mark.django_db
def test_run_object_group_available_view_get_queryset_when_not_member():
    user = factories.StaffUserFactory()

    view = views.RunObjectGroupAvailableListView()
    view.request = mock.MagicMock(user=user)

    run = factories.RunFactory()

    view.kwargs = {"run_id": run.id}
    with pytest.raises(views.Http404):
        view.get_queryset()


@pytest.mark.django_db
def test_run_object_group_available_view_get_queryset_when_run_has_object():
    project = factories.ProjectFactory()
    view = views.RunObjectGroupAvailableListView()
    view.request = mock.MagicMock(user=factories.LabAdminUserFactory())

    run_1 = factories.RunFactory(project=project)
    run_2 = factories.RunFactory(project=project)

    objectgroup = factories.ObjectGroupFactory()
    run_1.run_object_groups.add(objectgroup)
    run_2.run_object_groups.add(objectgroup)

    view.kwargs = {"run_id": run_2.id}
    assert view.get_queryset().count() == 0
