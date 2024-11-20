from datetime import timedelta

import pytest
from django.utils import timezone
from graphene.test import Client

from lab.schema import schema

from .factories import ObjectGroupFactory, ProjectFactory, RunFactory


@pytest.fixture(name="client")
def graphene_client():
    return Client(schema)


@pytest.mark.django_db
def test_resolve_stats(client):
    last_year_project = ProjectFactory()
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

    executed = client.execute(
        """
        query StatsQuery {
            stats {
                all {
                totalProjects
                totalObjectGroups
                totalHours
                }
                year {
                totalProjects
                totalObjectGroups
                totalHours
                }
            }
        }
        """
    )

    assert executed == {
        "data": {
            "stats": {
                "all": {"totalProjects": 3, "totalObjectGroups": 9, "totalHours": 18},
                "year": {"totalProjects": 2, "totalObjectGroups": 6, "totalHours": 12},
            }
        }
    }


@pytest.mark.django_db
def test_resolve_stats_when_nothing(client):
    executed = client.execute(
        """
        query StatsQuery {
            stats {
                all {
                totalProjects
                totalObjectGroups
                totalHours
                }
                year {
                totalProjects
                totalObjectGroups
                totalHours
                }
            }
        }
        """
    )

    assert executed == {
        "data": {
            "stats": {
                "all": {"totalProjects": 0, "totalObjectGroups": 0, "totalHours": 0},
                "year": {"totalProjects": 0, "totalObjectGroups": 0, "totalHours": 0},
            }
        }
    }
