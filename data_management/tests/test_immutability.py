import pytest

from data_management.immutability import (
    PROJECT_IMMUTABLE_ERROR,
    ProjectImmutableError,
    ensure_project_data_writable,
    is_project_data_immutable,
)
from data_management.models import LifecycleState, ProjectData
from lab.tests.factories import ProjectFactory


@pytest.mark.django_db
def test_ensure_project_writable_allows_hot_project():
    project = ProjectFactory()
    project_data = ProjectData.for_project(project)
    project_data.lifecycle_state = LifecycleState.HOT
    project_data.save(update_fields=["lifecycle_state"])

    ensure_project_data_writable(project)


@pytest.mark.django_db
@pytest.mark.parametrize("state", [LifecycleState.COOL, LifecycleState.COOLING])
def test_ensure_project_writable_rejects_immutable_project(state: LifecycleState):
    project = ProjectFactory()
    project_data = ProjectData.for_project(project)
    project_data.lifecycle_state = state
    project_data.save(update_fields=["lifecycle_state"])

    with pytest.raises(ProjectImmutableError) as exc_info:
        ensure_project_data_writable(project)

    error = exc_info.value
    assert error.payload.error == PROJECT_IMMUTABLE_ERROR
    assert error.payload.lifecycle_state == state


@pytest.mark.django_db
@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (LifecycleState.HOT, False),
        (LifecycleState.RESTORING, False),
        (LifecycleState.ERROR, False),
        (LifecycleState.COOL, True),
        (LifecycleState.COOLING, True),
    ],
)
def test_is_project_immutable(state: LifecycleState, expected: bool):
    project = ProjectFactory()
    project_data = ProjectData.for_project(project)
    project_data.lifecycle_state = state
    project_data.save(update_fields=["lifecycle_state"])

    assert is_project_data_immutable(project) is expected
