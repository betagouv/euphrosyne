from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from euphro_auth.tests import factories as auth_factories
from lab.api_views.project import (
    IsLabAdminUser,
    ProjectLeaderParticipationRetrieveCreateUpdateGroupView,
    ProjectList,
    ProjectSerializer,
    UpcomingProjectList,
    UpcomingProjectSerializer,
)
from lab.api_views.serializers import OnPremisesParticipationSerializer
from lab.models import Project

from .. import factories


class TestProjectListView(TestCase):
    def setUp(self):
        self.client = client = Client()
        self.api_url = reverse("api:project-list")

        client.force_login(auth_factories.LabAdminUserFactory())

        tz = timezone.get_current_timezone()
        self.june_project = factories.RunFactory(
            start_date=timezone.datetime(2023, 6, 1, 10, 0, 0, tzinfo=tz),
            end_date=timezone.datetime(2023, 6, 30, 10, 0, 0, tzinfo=tz),
        ).project
        self.july_project = factories.RunFactory(
            start_date=timezone.datetime(2023, 7, 1, 10, 0, 0, tzinfo=tz),
            end_date=timezone.datetime(2023, 7, 30, 10, 0, 0, tzinfo=tz),
        ).project
        self.august_project = factories.RunFactory(
            start_date=timezone.datetime(2023, 8, 1, 10, 0, 0, tzinfo=tz),
            end_date=timezone.datetime(2023, 8, 30, 10, 0, 0, tzinfo=tz),
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

    @mock.patch("lab.api_views.project.ProjectFilter.filter_after")
    @mock.patch("lab.api_views.project.ProjectFilter.filter_before")
    def test_project_in_between(self, mock_filter_before, mock_filter_after):
        # Setup mocks to return the correct queryset
        mock_filter_after.return_value = Project.objects.filter(
            id__in=[self.june_project.id, self.july_project.id, self.august_project.id]
        )
        mock_filter_before.return_value = Project.objects.filter(
            id__in=[self.june_project.id, self.july_project.id, self.august_project.id]
        )

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

    @mock.patch("lab.api_views.project.ProjectFilter.filter_before")
    def test_project_filering_before_june(self, mock_filter_before):
        # Setup mock to return empty queryset
        mock_filter_before.return_value = Project.objects.none()

        response = self.client.get(f"{self.api_url}?start_before=2023-05-31")

        assert response.status_code == 200
        assert len(response.json()) == 0

    @mock.patch("lab.api_views.project.ProjectFilter.filter_before")
    def test_project_filering_before_july(self, mock_filter_before):
        # Setup mock to return only june project
        mock_filter_before.return_value = Project.objects.filter(
            id=self.june_project.id
        )

        response = self.client.get(f"{self.api_url}?start_before=2023-06-30")

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == self.june_project.name

    @mock.patch("lab.api_views.project.ProjectFilter.filter_before")
    def test_project_filering_before_september(self, mock_filter_before):
        # Setup mock to return all projects
        mock_filter_before.return_value = Project.objects.filter(
            id__in=[self.june_project.id, self.july_project.id, self.august_project.id]
        )

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

    @mock.patch("lab.api_views.project.ProjectFilter.filter_after")
    def test_project_filering_after_august(self, mock_filter_after):
        # Setup mock to return empty queryset
        mock_filter_after.return_value = Project.objects.none()

        response = self.client.get(f"{self.api_url}?end_after=2023-09-01")

        assert response.status_code == 200
        assert len(response.json()) == 0

    @mock.patch("lab.api_views.project.ProjectFilter.filter_after")
    def test_project_filering_after_may(self, mock_filter_after):
        # Setup mock to return all projects
        mock_filter_after.return_value = Project.objects.filter(
            id__in=[self.june_project.id, self.july_project.id, self.august_project.id]
        )

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


class TestProjectLeaderParticipationRetrieveCreateUpdateGroupView(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = auth_factories.LabAdminUserFactory()
        self.client.force_login(self.admin_user)
        self.project = factories.ProjectWithLeaderFactory()
        self.api_url = reverse(
            "api:project-leader-participation-retrieve-create-update",
            kwargs={"project_id": self.project.id},
        )

    def test_view_config(self):
        """Test that the view has correct configuration."""
        view = ProjectLeaderParticipationRetrieveCreateUpdateGroupView()
        assert view.serializer_class == OnPremisesParticipationSerializer

    @mock.patch(
        "lab.api_views.serializers.send_project_invitation_email", new=mock.MagicMock()
    )
    @mock.patch("lab.api_views.serializers.send_invitation_email", new=mock.MagicMock())
    def test_create_leader_participation(
        self,
    ):
        """Test creating a leader participation via API."""
        project = factories.ProjectFactory()
        api_url = reverse(
            "api:project-leader-participation-retrieve-create-update",
            kwargs={"project_id": project.id},
        )

        data = {
            "user": {"email": "leader@test.test"},
            "institution": {"name": "Test Institution", "country": "France"},
            "employer": {
                "first_name": "John",
                "last_name": "Doe",
                "email": "john.doe@test.test",
                "function": "Manager",
            },
        }

        response = self.client.post(api_url, data, content_type="application/json")
        assert response.status_code == 201

        project.refresh_from_db()
        assert project.leader is not None
        assert project.leader.user.email == "leader@test.test"
        assert project.leader.is_leader is True
        assert project.leader.on_premises is True

    def test_retrieve_leader_participation(self):
        """Test retrieving the leader participation via API."""
        response = self.client.get(self.api_url)

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == self.project.leader.user.email
        # Verify this is actually the leader participation
        assert data["id"] == self.project.leader.id

    @mock.patch("lab.api_views.serializers.send_project_invitation_email")
    def test_update_leader_participation(self, _):
        """Test updating the leader participation via API."""
        data = {
            "user": {"email": "newleader@test.test"},
        }

        response = self.client.patch(
            self.api_url, data, content_type="application/json"
        )
        assert response.status_code == 200

        self.project.leader.refresh_from_db()
        assert self.project.leader.user.email == "newleader@test.test"
        assert self.project.leader.is_leader is True
