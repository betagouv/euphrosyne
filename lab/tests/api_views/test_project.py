from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from euphro_auth.tests import factories as auth_factories
from lab.api_views.project import (
    IsLabAdminUser,
    ProjectList,
    ProjectSerializer,
    UpcomingProjectList,
    UpcomingProjectSerializer,
)

from .. import factories


class TestProjectListView(TestCase):
    def setUp(self):
        self.client = client = Client()
        self.api_url = reverse("api:project-list")

        client.force_login(auth_factories.LabAdminUserFactory())

        self.june_project = factories.RunFactory(
            start_date="2023-06-01 10:00:00", end_date="2023-06-30 10:00:00"
        ).project
        self.july_project = factories.RunFactory(
            start_date="2023-07-01 10:00:00", end_date="2023-07-30 10:00:00"
        ).project
        self.august_project = factories.RunFactory(
            start_date="2023-08-01 10:00:00", end_date="2023-08-30 10:00:00"
        ).project

    def test_project_list_conf(self):
        assert ProjectList.serializer_class == ProjectSerializer
        assert IsLabAdminUser in ProjectList.permission_classes

    def test_project_without_filering(self):
        response = self.client.get(self.api_url)

        assert response.status_code == 200
        assert len(response.json()) == 3
        assert set(
            [
                self.june_project.name,
                self.july_project.name,
                self.august_project.name,
            ]
        ) == set(project["name"] for project in response.json())

    def test_project_in_between(self):
        response = self.client.get(
            f"{self.api_url}?start_after=2023-06-01&end_before=2023-08-31"
        )

        assert response.status_code == 200
        assert len(response.json()) == 3
        assert set(
            [
                self.june_project.name,
                self.july_project.name,
                self.august_project.name,
            ]
        ) == set(project["name"] for project in response.json())

    def test_project_filering_before_june(self):
        response = self.client.get(f"{self.api_url}?start_before=2023-05-31")

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_project_filering_before_july(self):
        response = self.client.get(f"{self.api_url}?start_before=2023-06-30")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == self.june_project.name

    def test_project_filering_before_september(self):
        response = self.client.get(f"{self.api_url}?start_before=2023-09-30")

        assert response.status_code == 200
        assert len(response.json()) == 3
        assert set(
            [
                self.june_project.name,
                self.july_project.name,
                self.august_project.name,
            ]
        ) == set(project["name"] for project in response.json())

    def test_project_filering_after_august(self):
        response = self.client.get(f"{self.api_url}?end_after=2023-09-01")

        assert response.status_code == 200
        assert len(response.json()) == 0

    def test_project_filering_after_may(self):
        response = self.client.get(f"{self.api_url}?end_after=2023-05-31")

        assert response.status_code == 200
        assert len(response.json()) == 3
        assert set(
            [
                self.june_project.name,
                self.july_project.name,
                self.august_project.name,
            ]
        ) == set(project["name"] for project in response.json())


class TestUpcomingProjectListView(TestCase):
    def setUp(self):
        self.client = client = Client()
        self.api_url = reverse("api:project-upcoming-list")

        client.force_login(auth_factories.LabAdminUserFactory())

        self.last_month_project = factories.RunFactory(
            start_date=timezone.now() - timezone.timedelta(days=30),
            end_date=timezone.now() - timezone.timedelta(days=1),
        ).project
        self.next_projects = [
            (
                factories.RunFactory(
                    start_date=timezone.now() + timezone.timedelta(days=i * i),
                    end_date=timezone.now() + timezone.timedelta(days=(i * i) + 1),
                ).project
            )
            for i in range(10)
        ]

    def test_conf(self):
        assert UpcomingProjectList.serializer_class == UpcomingProjectSerializer
        assert IsLabAdminUser in UpcomingProjectList.permission_classes

    def test_upcoming_project_list(self):
        response = self.client.get(self.api_url)

        assert response.status_code == 200
        assert len(response.json()) == 4
        assert set(
            [
                self.next_projects[0].name,
                self.next_projects[1].name,
                self.next_projects[2].name,
                self.next_projects[3].name,
            ]
        ) == set(project["name"] for project in response.json())
