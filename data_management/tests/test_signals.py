from datetime import timedelta

import pytest

from data_management.models import ProjectData
from lab.tests.factories import ProjectFactory


@pytest.mark.django_db
def test_project_data_created_with_initial_eligibility():
    project = ProjectFactory()

    project_data = ProjectData.objects.get(project=project)

    expected = project.created + timedelta(days=30 * 6)
    assert project_data.cooling_eligible_at == expected
