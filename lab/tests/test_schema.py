from datetime import timedelta

import pytest
from django.utils import timezone
from graphene.test import Client

from lab.objects.models import Location
from lab.schema import schema

from .factories import FinishedProject, ObjectGroupFactory, ProjectFactory, RunFactory


@pytest.fixture(name="client")
def graphene_client():
    return Client(schema)


@pytest.mark.django_db
def test_resolve_last_projects_are_finished(client):
    finished_project = FinishedProject()
    ProjectFactory()  # not finished project
    executed = client.execute(
        """
        query {
            lastProjects(limit: 3) {
                name
                status
                comments
                slug
            }
        }
        """
    )

    assert executed == {
        "data": {
            "lastProjects": [
                {
                    "name": finished_project.name,
                    "status": "Status.FINISHED",
                    "comments": finished_project.comments,
                    "slug": finished_project.slug,
                }
            ]
        }
    }


@pytest.mark.django_db
def test_resolve_last_projects_are_confidential(client):
    public_project = ProjectFactory(name="Finished project", confidential=False)
    public_project.runs.create(
        start_date=timezone.now() - timezone.timedelta(days=2),
        end_date=timezone.now() - timezone.timedelta(days=1),
    )
    confidential_project = ProjectFactory(
        name="Not Finished Project", confidential=True
    )
    confidential_project.runs.create(
        start_date=timezone.now() - timezone.timedelta(days=1),
        end_date=timezone.now() - timezone.timedelta(days=1),
    )
    executed = client.execute(
        """
        query {
            lastProjects(limit: 3) {
                name
                status
                comments
                slug
            }
        }
        """
    )

    assert executed == {
        "data": {
            "lastProjects": [
                {
                    "name": public_project.name,
                    "status": "Status.FINISHED",
                    "comments": public_project.comments,
                    "slug": public_project.slug,
                }
            ]
        }
    }


@pytest.mark.django_db
def test_resolve_project_detail(client):
    project = FinishedProject()
    executed = client.execute(
        """
        query {
            projectDetail(slug: "%s") {
                name
                comments
                slug
            }
        }
        """
        % project.slug
    )

    assert executed == {
        "data": {
            "projectDetail": {
                "name": project.name,
                "comments": project.comments,
                "slug": project.slug,
            }
        }
    }


@pytest.mark.django_db
def test_resolve_object_group_detail(client):
    location = Location.objects.create(label="Location")
    objectgroup = ObjectGroupFactory(discovery_place_location=location)
    objectgroup.runs.add(FinishedProject().runs.first())
    executed = client.execute(
        """
        query {
            objectGroupDetail(pk: "%s") {
                label
                discoveryPlace
                collection
                dataAvailable
            }
        }
        """
        % objectgroup.id
    )

    assert executed == {
        "data": {
            "objectGroupDetail": {
                "label": objectgroup.label,
                "discoveryPlace": objectgroup.discovery_place,
                "collection": objectgroup.collection,
                "dataAvailable": False,
            }
        }
    }


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
                "all": {"totalProjects": 3, "totalObjectGroups": 3, "totalHours": 18},
                "year": {"totalProjects": 2, "totalObjectGroups": 2, "totalHours": 12},
            }
        }
    }


@pytest.mark.django_db
def test_resolve_when_nothing(client):
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
