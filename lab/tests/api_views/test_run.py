from django.test import Client, TestCase
from django.urls import reverse

from .. import factories


class TestRunView(TestCase):
    def setUp(self):
        self.run = run = factories.RunFactory()
        self.client = client = Client()
        self.api_url = reverse("api:run-detail-methods", args=[run.id])

        client.force_login(factories.LabAdminUserFactory())

        self.june_project = factories.RunFactory(
            start_date="2023-06-01 10:00:00", end_date="2023-06-30 10:00:00"
        ).project
        self.july_project = factories.RunFactory(
            start_date="2023-07-01 10:00:00", end_date="2023-07-30 10:00:00"
        ).project
        self.august_project = factories.RunFactory(
            start_date="2023-08-01 10:00:00", end_date="2023-08-30 10:00:00"
        ).project

    def test_run_detail_methods(self):
        response = self.client.get(self.api_url)

        assert response.status_code == 200
        assert response.json() == {
            "method_PIXE": self.run.method_PIXE,
            "method_PIGE": self.run.method_PIGE,
            "method_IBIL": self.run.method_IBIL,
            "method_FORS": self.run.method_FORS,
            "method_RBS": self.run.method_RBS,
            "method_ERDA": self.run.method_ERDA,
            "method_NRA": self.run.method_NRA,
            "detector_LE0": self.run.detector_LE0,
            "detector_HE1": self.run.detector_HE1,
            "detector_HE2": self.run.detector_HE2,
            "detector_HE3": self.run.detector_HE3,
            "detector_HE4": self.run.detector_HE4,
            "detector_HPGe20": self.run.detector_HPGe20,
            "detector_HPGe70": self.run.detector_HPGe70,
            "detector_HPGe70N": self.run.detector_HPGe70N,
            "detector_IBIL_QE65000": self.run.detector_IBIL_QE65000,
            "detector_FORS_QE65000": self.run.detector_FORS_QE65000,
            "detector_PIPS130": self.run.detector_PIPS130,
            "detector_PIPS150": self.run.detector_PIPS150,
            "detector_IBIL_other": self.run.detector_IBIL_other,
            "detector_FORS_other": self.run.detector_FORS_other,
            "detector_ERDA": self.run.detector_ERDA,
            "detector_NRA": self.run.detector_NRA,
            "filters_for_detector_LE0": self.run.filters_for_detector_LE0,
            "filters_for_detector_HE1": self.run.filters_for_detector_HE1,
            "filters_for_detector_HE2": self.run.filters_for_detector_HE2,
            "filters_for_detector_HE3": self.run.filters_for_detector_HE3,
            "filters_for_detector_HE4": self.run.filters_for_detector_HE4,
        }
