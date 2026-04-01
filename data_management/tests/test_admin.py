from __future__ import annotations

from unittest import mock

import pytest
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.messages import get_messages
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.utils.formats import date_format
from django.utils.text import capfirst
from django.utils.translation import gettext

from data_management.admin import ProjectDataAdmin
from data_management.models import (
    FromDataDeletionStatus,
    LifecycleOperation,
    LifecycleOperationStatus,
    LifecycleOperationType,
    LifecycleState,
    ProjectData,
)
from euphro_auth.tests.factories import LabAdminUserFactory, StaffUserFactory

from .factories import ProjectDataFactory


class DummyResponse:
    def __init__(self, status_code: int, text: str = "") -> None:
        self.status_code = status_code
        self.text = text


@pytest.mark.django_db
def test_project_data_admin_is_only_accessible_to_lab_admin():
    project_data = ProjectDataFactory()
    url = reverse("admin:data_management_projectdata_change", args=[project_data.pk])

    anon_response = Client().get(url)
    assert anon_response.status_code == 302

    staff_client = Client()
    staff_client.force_login(StaffUserFactory())
    staff_response = staff_client.get(url)
    assert staff_response.status_code == 403

    admin_client = Client()
    admin_client.force_login(LabAdminUserFactory())
    admin_response = admin_client.get(url)
    assert admin_response.status_code == 302
    assert admin_response.headers["Location"] == reverse(
        "admin:lab_project_workplace",
        args=[project_data.project_id],
    )


@pytest.mark.django_db
def test_project_data_admin_changelist_is_accessible_to_lab_admin():
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(reverse("admin:data_management_projectdata_changelist"))

    assert response.status_code == 200
    assert gettext("Project data lifecycle") in response.content.decode()


@pytest.mark.django_db
def test_project_data_admin_changelist_renders_tag_filters():
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(reverse("admin:data_management_projectdata_changelist"))

    assert response.status_code == 200
    lifecycle_filter = response.context_data["cl"].filter_specs[0]
    assert lifecycle_filter.lookup_choices == [
        (LifecycleState.HOT, capfirst(gettext("available"))),
        (LifecycleState.COOLING, capfirst(gettext("archiving"))),
        (LifecycleState.COOL, capfirst(gettext("archived"))),
        (LifecycleState.RESTORING, capfirst(gettext("restoring"))),
        (LifecycleState.ERROR, capfirst(gettext("error"))),
    ]
    content = response.content.decode()
    assert (
        '<nav aria-labelledby="changelist-filter-header" class="changelist-filters'
        in content
    )
    assert 'class="fr-tags-group"' in content
    assert 'class="fr-tag"' in content
    assert 'data-filter-title="' in content
    assert 'id="changelist-filter"' not in content


@pytest.mark.django_db
def test_project_data_admin_changelist_filters_by_lifecycle_state():
    error_project_data = ProjectDataFactory(lifecycle_state=LifecycleState.ERROR)
    ProjectDataFactory(lifecycle_state=LifecycleState.HOT)

    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        reverse("admin:data_management_projectdata_changelist"),
        data={"lifecycle_state": LifecycleState.ERROR},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert error_project_data.project.name in content


@pytest.mark.django_db
def test_project_data_admin_changelist_filters_by_cooling_eligibility():
    eligible_project_data = ProjectDataFactory(
        cooling_eligible_at=timezone.now() - timezone.timedelta(days=1)
    )
    ineligible_project_data = ProjectDataFactory(
        cooling_eligible_at=timezone.now() + timezone.timedelta(days=1)
    )

    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        reverse("admin:data_management_projectdata_changelist"),
        data={"cooling_eligibility": "eligible"},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert eligible_project_data.project.name in content
    assert ineligible_project_data.project.name not in content


@pytest.mark.django_db
def test_project_data_admin_changelist_sorts_by_last_operation_datetime():
    older_project_data = ProjectDataFactory()
    newer_project_data = ProjectDataFactory()
    LifecycleOperation.objects.create(
        project_data=older_project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
        started_at=timezone.now() - timezone.timedelta(days=2),
        finished_at=timezone.now() - timezone.timedelta(days=1),
    )
    LifecycleOperation.objects.create(
        project_data=newer_project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.RUNNING,
        started_at=timezone.now() - timezone.timedelta(hours=3),
    )

    request = RequestFactory().get(
        reverse("admin:data_management_projectdata_changelist"),
    )
    request.user = LabAdminUserFactory()
    model_admin = admin.site._registry[ProjectData]  # pylint: disable=protected-access

    ascending_results = list(
        model_admin.get_queryset(request).order_by("last_operation_datetime")
    )
    descending_results = list(
        model_admin.get_queryset(request).order_by("-last_operation_datetime")
    )

    assert ascending_results[0].pk == older_project_data.pk
    assert descending_results[0].pk == newer_project_data.pk


@pytest.mark.django_db
def test_project_data_admin_last_operation_helpers_require_annotations():
    project_data = ProjectDataFactory()

    with pytest.raises(AttributeError):
        # pylint: disable=protected-access
        ProjectDataAdmin._get_last_operation_type(project_data)

    with pytest.raises(AttributeError):
        # pylint: disable=protected-access
        ProjectDataAdmin._get_last_operation_datetime(project_data)

    with pytest.raises(AttributeError):
        # pylint: disable=protected-access
        ProjectDataAdmin._get_last_operation_id(project_data)


@pytest.mark.django_db
def test_project_data_admin_changelist_displays_requested_lifecycle_fields():
    project_data = ProjectDataFactory(
        lifecycle_state=LifecycleState.ERROR,
        cooling_eligible_at=timezone.now() - timezone.timedelta(days=2),
    )
    operation = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.FAILED,
        started_at=timezone.now() - timezone.timedelta(hours=2),
        finished_at=timezone.now() - timezone.timedelta(hours=1),
        bytes_total=20,
        files_total=4,
        bytes_copied=10,
        files_copied=3,
        error_message="Verification failed.",
        error_details='{"reason": "verification_mismatch"}',
    )

    response = Client()
    response.force_login(LabAdminUserFactory())
    changelist_response = response.get(
        reverse("admin:data_management_projectdata_changelist")
    )

    assert changelist_response.status_code == 200
    assert tuple(changelist_response.context_data["cl"].list_display) == (
        "project_link",
        "lifecycle_state_badge",
        "cooling_eligible_at",
        "last_operation_lifecycle",
        "last_operation",
    )
    model_admin = admin.site._registry[ProjectData]  # pylint: disable=protected-access
    result = changelist_response.context_data["cl"].result_list[0]
    assert model_admin.last_operation.short_description == gettext("Last operation")
    assert model_admin.last_operation.admin_order_field == "last_operation_datetime"
    assert str(result.last_operation_id) == str(operation.operation_id)
    assert result.last_operation_type == operation.type
    assert result.last_operation_datetime == operation.started_at
    content = changelist_response.content.decode()
    assert (
        reverse("admin:lab_project_workplace", args=[project_data.project_id])
        in content
    )
    assert project_data.project.name in content
    # pylint: disable=line-too-long
    assert 'class="fr-badge fr-badge--error fr-badge--no-icon fr-badge--sm"' in content
    assert gettext("error") in content
    assert (
        'class="fr-badge fr-badge--success fr-badge--no-icon fr-badge--sm"' in content
    )
    assert 'class="fr-badge fr-badge--no-icon fr-badge--sm"' in content
    assert gettext("available") in content
    assert gettext("archived") in content
    assert 'class="fr-sr-only"' in content
    assert (
        gettext("%(old_state)s to %(new_state)s")
        % {
            "old_state": gettext("available"),
            "new_state": gettext("archived"),
        }
        in content
    )
    assert "&rarr;" in content
    assert (
        date_format(
            operation.started_at,
            format="SHORT_DATETIME_FORMAT",
            use_l10n=True,
        )
        in content
    )
    assert (
        reverse(
            "admin:data_management_lifecycleoperation_change",
            args=[operation.operation_id],
        )
        in content
    )


@pytest.mark.django_db
def test_project_data_admin_change_view_redirects_to_workplace():
    project_data = ProjectDataFactory()
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        reverse("admin:data_management_projectdata_change", args=[project_data.pk])
    )

    assert response.status_code == 302
    assert response.headers["Location"] == reverse(
        "admin:lab_project_workplace",
        args=[project_data.project_id],
    )


@pytest.mark.django_db
def test_lifecycle_operation_admin_changelist_is_accessible_to_lab_admin():
    project_data = ProjectDataFactory()
    other_project_data = ProjectDataFactory()
    operation = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
    )
    LifecycleOperation.objects.create(
        project_data=other_project_data,
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.FAILED,
    )

    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        reverse("admin:data_management_lifecycleoperation_changelist"),
        data={"project_data": project_data.pk},
    )

    assert response.status_code == 200
    content = response.content.decode()
    assert str(operation.operation_id) in content
    assert project_data.project.name in content
    assert other_project_data.project.name not in content


@pytest.mark.django_db
def test_lifecycle_operation_admin_change_view_is_accessible_to_lab_admin():
    project_data = ProjectDataFactory()
    operation = LifecycleOperation.objects.create(
        project_data=project_data,
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.RUNNING,
    )

    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        reverse(
            "admin:data_management_lifecycleoperation_change",
            args=[operation.operation_id],
        )
    )

    assert response.status_code == 200
    assert str(operation.operation_id) in response.content.decode()


@pytest.mark.django_db
def test_lifecycle_operation_admin_change_view_displays_from_data_deletion_fields():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
        from_data_deletion_status=FromDataDeletionStatus.FAILED,
        from_data_deleted_at=timezone.now(),
        from_data_deletion_error="delete failed",
    )
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.get(
        reverse(
            "admin:data_management_lifecycleoperation_change",
            args=[operation.operation_id],
        )
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert "from_data_deletion_status" in content
    assert "from_data_deleted_at" in content
    assert "from_data_deletion_error" in content
    assert "delete failed" in content


@pytest.mark.django_db
def test_lifecycle_operation_admin_exposes_delete_source_data_action_to_lab_admin():
    request = RequestFactory().get(
        reverse("admin:data_management_lifecycleoperation_changelist"),
    )
    request.user = LabAdminUserFactory()
    # pylint: disable=protected-access
    model_admin = admin.site._registry[LifecycleOperation]

    actions = model_admin.get_actions(request)

    assert "delete_source_data" in actions


@pytest.mark.django_db
def test_lifecycle_operation_admin_delete_source_data_action_renders_confirmation():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(lifecycle_state=LifecycleState.COOL),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    client = Client()
    client.force_login(LabAdminUserFactory())

    response = client.post(
        reverse("admin:data_management_lifecycleoperation_changelist"),
        data={
            "action": "delete_source_data",
            "index": 0,
            helpers.ACTION_CHECKBOX_NAME: [str(operation.operation_id)],
        },
    )

    content = response.content.decode()

    assert response.status_code == 200
    assert str(operation.operation_id) in content
    assert 'name="post" value="yes"' in content
    assert 'name="action" value="delete_source_data"' in content


@pytest.mark.django_db
def test_lifecycle_operation_admin_delete_source_data_action_triggers_deletion():
    operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(lifecycle_state=LifecycleState.COOL),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    client = Client()
    client.force_login(LabAdminUserFactory())

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        return_value=DummyResponse(status_code=202),
    ):
        response = client.post(
            reverse("admin:data_management_lifecycleoperation_changelist"),
            data={
                "action": "delete_source_data",
                helpers.ACTION_CHECKBOX_NAME: [str(operation.operation_id)],
                "post": "yes",
            },
            follow=True,
        )

    operation.refresh_from_db()

    assert response.status_code == 200
    assert operation.from_data_deletion_status == FromDataDeletionStatus.RUNNING
    assert operation.from_data_deletion_error is None
    assert operation.from_data_deleted_at is None
    assert (
        "Suppression des données source lancée pour 1 opération(s)."
        in response.content.decode()
    )


@pytest.mark.django_db
def test_lifecycle_operation_admin_delete_source_data_action_skips_ineligible_rows():
    eligible_operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(lifecycle_state=LifecycleState.COOL),
        type=LifecycleOperationType.COOL,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    ineligible_operation = LifecycleOperation.objects.create(
        project_data=ProjectDataFactory(lifecycle_state=LifecycleState.COOL),
        type=LifecycleOperationType.RESTORE,
        status=LifecycleOperationStatus.SUCCEEDED,
    )
    client = Client()
    client.force_login(LabAdminUserFactory())

    with mock.patch(
        "data_management.operations.post_delete_project_source_data",
        return_value=DummyResponse(status_code=202),
    ):
        response = client.post(
            reverse("admin:data_management_lifecycleoperation_changelist"),
            data={
                "action": "delete_source_data",
                helpers.ACTION_CHECKBOX_NAME: [
                    str(eligible_operation.operation_id),
                    str(ineligible_operation.operation_id),
                ],
                "post": "yes",
            },
            follow=True,
        )

    eligible_operation.refresh_from_db()
    ineligible_operation.refresh_from_db()
    # pylint: disable=line-too-long
    response_messages = [
        str(message) for message in get_messages(response.wsgi_request)
    ]

    assert response.status_code == 200
    assert (
        eligible_operation.from_data_deletion_status == FromDataDeletionStatus.RUNNING
    )
    assert (
        ineligible_operation.from_data_deletion_status
        == FromDataDeletionStatus.NOT_REQUESTED
    )
    # pylint: disable=line-too-long
    assert (
        "Suppression des données source lancée pour 1 opération(s)."
        in response_messages
    )

    expected_message = gettext(
        "Could not delete source data for operation %(operation_id)s: %(detail)s"
    ) % {
        "operation_id": ineligible_operation.operation_id,
        "detail": gettext("Only cool operations can delete source data."),
    }
    assert expected_message in response_messages
