from django.test import TestCase
from euphro_auth.tests import factories as auth_factories
from lab.tests import factories as lab_factories
from ..models import Standard, MeasuringPointStandard
from lab.measuring_points.models import MeasuringPoint

import json


class TestStandardAPIView(TestCase):

    def test_list(self):
        Standard.objects.create(label="test")
        Standard.objects.create(label="test2")

        self.client.force_login(auth_factories.StaffUserFactory())

        response = self.client.get("/api/standard/standards")

        assert response.status_code == 200
        assert response.json() == [
            {"label": "test"},
            {"label": "test2"},
        ]


class TestMeasuringPointStandardAPIView(TestCase):

    def setUp(self):
        self.standard = Standard.objects.create(label="test")
        self.run = lab_factories.RunFactory()
        self.point = MeasuringPoint.objects.create(run=self.run)

        self.url = f"/api/standard/measuring-points/{self.point.id}/standard"

    def test_create(self):

        self.client.force_login(auth_factories.LabAdminUserFactory())
        response = self.client.post(
            self.url,
            data=json.dumps({"standard": {"label": self.standard.label}}),
            content_type="application/json",
        )

        assert response.status_code == 201
        assert MeasuringPointStandard.objects.get(
            standard=self.standard, measuring_point=self.point
        )

    def test_update(self):
        MeasuringPointStandard.objects.create(
            standard=self.standard, measuring_point=self.point
        )
        self.client.force_login(auth_factories.LabAdminUserFactory())
        another_standard = Standard.objects.create(label="another")
        response = self.client.patch(
            self.url,
            data=json.dumps({"standard": {"label": another_standard.label}}),
            content_type="application/json",
        )

        assert response.status_code == 200
        assert MeasuringPointStandard.objects.get(
            standard=another_standard, measuring_point=self.point
        )

    def test_delete(self):
        MeasuringPointStandard.objects.create(
            standard=self.standard, measuring_point=self.point
        )
        self.client.force_login(auth_factories.LabAdminUserFactory())
        response = self.client.delete(
            self.url,
        )

        assert response.status_code == 204
        assert not MeasuringPointStandard.objects.filter(
            measuring_point=self.point
        ).exists()

    def test_retrieve(self):
        measuring_point_standard = MeasuringPointStandard.objects.create(
            standard=self.standard, measuring_point=self.point
        )
        self.client.force_login(auth_factories.LabAdminUserFactory())
        response = self.client.get(
            self.url,
        )

        assert response.status_code == 200
        assert response.json() == {
            "id": measuring_point_standard.id,
            "standard": {
                "label": self.standard.label,
            },
        }

    def test_permission(self):
        self.client.force_login(auth_factories.StaffUserFactory())
        MeasuringPointStandard.objects.create(
            standard=self.standard, measuring_point=self.point
        )
        response = self.client.get(
            self.url,
        )

        assert response.status_code == 403
