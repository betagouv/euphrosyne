from datetime import timedelta
from unittest import mock

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from lab.api_views.calendar import CalendarSerializer, CalendarView
from lab.tests.factories import LabAdminUserFactory, RunFactory, StaffUserFactory


class CalendarViewTestCase(TestCase):
    def setUp(self):
        self.request = RequestFactory().get("/api/lab/calendar")
        self.request.query_params = mock.MagicMock()

        self.view = CalendarView()
        self.view.request = self.request

    def test_queryset_filtering_when_regular_user(self):
        run_1 = RunFactory()
        run_2 = RunFactory()

        staff_user = StaffUserFactory()
        run_1.project.members.add(staff_user)
        self.request.user = staff_user

        queryset = self.view.get_queryset()

        assert run_1 in queryset
        assert run_2 not in queryset

    def test_queryset_filtering_when_admin(self):
        run_1 = RunFactory()
        run_2 = RunFactory()

        lab_admin = LabAdminUserFactory()
        self.request.user = lab_admin

        queryset = self.view.get_queryset()

        assert run_1 in queryset
        assert run_2 in queryset

    def test_queryset_datetime_filtering(self):
        now = timezone.now()
        run_1 = RunFactory(
            start_date=now + timedelta(days=31),
            end_date=now + timedelta(days=32),
        )
        run_2 = RunFactory(
            start_date=now + timedelta(days=1),
            end_date=now + timedelta(days=2),
        )
        run_3 = RunFactory(
            start_date=now + timedelta(days=61),
            end_date=now + timedelta(days=62),
        )

        lab_admin = LabAdminUserFactory()
        self.request.user = lab_admin
        self.request.query_params = {
            "start": now + timedelta(days=31),
            "end": now + timedelta(days=32),
        }

        queryset = self.view.get_queryset()

        assert run_1 in queryset
        assert run_2 not in queryset
        assert run_3 not in queryset


class CalendarSerializerTestCase(TestCase):
    def test_run_serializaition(self):
        date = timezone.datetime(2023, 3, 2, 16, 56)
        run = RunFactory(
            label="run",
            project__name="project",
            start_date=date,
            end_date=date + timedelta(days=1),
        )

        serialized_run = CalendarSerializer(run).data

        assert serialized_run
        assert serialized_run["id"] == run.id
        assert serialized_run["group_id"] == run.project.id
        assert serialized_run["title"] == "run [project]"
        assert serialized_run["start"] == "2023-03-02T16:56:00+01:00"
        assert serialized_run["end"] == "2023-03-03T16:56:00+01:00"
        assert serialized_run["url"] == reverse("admin:lab_run_change", args=[run.id])
