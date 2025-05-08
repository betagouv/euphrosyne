from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from ..factories import ObjectGroupFactory, ProjectFactory, RunFactory


@pytest.fixture(name="client")
def api_client():
    return APIClient()


@pytest.mark.django_db
def test_resolve_stats(client):
    last_year_project = ProjectFactory()
    # Make sure created date is timezone aware
    last_year_project.created = timezone.now() - timedelta(days=365)
    last_year_project.save()

    for run in [
        RunFactory(
            project=last_year_project,
            start_date=timezone.now() - timedelta(days=365),
            end_date=timezone.now() + timedelta(hours=6) - timedelta(days=365),
        ),
        RunFactory(
            start_date=timezone.now() - timedelta(hours=12),
            end_date=timezone.now() - timedelta(hours=6),
        ),
        RunFactory(
            start_date=timezone.now() - timedelta(hours=12),
            end_date=timezone.now() - timedelta(hours=6),
        ),
    ]:
        run.run_object_groups.add(ObjectGroupFactory())
    response = client.get("/api/lab/stats/")

    assert response.json() == {
        "all": {
            "total_projects": 3,
            "total_object_groups": 9,
            "total_hours": 18,
        },
        "year": {
            "total_projects": 2,
            "total_object_groups": 6,
            "total_hours": 12,
        },
    }


@pytest.mark.django_db
def test_resolve_stats_when_nothing(client):
    response = client.get("/api/lab/stats/")

    assert response.status_code == 200
    assert response.json() == {
        "all": {
            "total_projects": 0,
            "total_object_groups": 0,
            "total_hours": 0,
        },
        "year": {
            "total_projects": 0,
            "total_object_groups": 0,
            "total_hours": 0,
        },
    }
