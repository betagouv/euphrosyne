from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse

from lab.objects.c2rmf import ErosHTTPError

from .. import factories


class TestProjectListView(TestCase):
    def setUp(self):
        self.client = client = Client()
        self.api_url = reverse("api:objectgroup-c2rmf-fetch")

        client.force_login(factories.LabAdminUserFactory())

    def test_route_auth(self):
        client = Client()
        response = client.post(self.api_url, {"query": "abc"})

        assert response.status_code == 403

    def test_call_eros(self):
        with mock.patch(
            "lab.api_views.objects.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            obj = {"label": "atitle", "c2rmf_id": "1"}
            mock_fn.return_value = obj
            response = self.client.post(self.api_url, {"query": "abc"})

            mock_fn.assert_called_once_with("abc")
            assert response.status_code == 200
            assert response.json() == obj

    def test_eros_error_return_not_found(self):
        with mock.patch(
            "lab.api_views.objects.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            mock_fn.side_effect = ErosHTTPError
            response = self.client.post(self.api_url, {"query": "abc"})

            mock_fn.assert_called_once_with("abc")
            assert response.status_code == 404

    def test_eros_return_none_return_not_found(self):
        with mock.patch(
            "lab.api_views.objects.fetch_partial_objectgroup_from_eros"
        ) as mock_fn:
            mock_fn.return_value = None
            response = self.client.post(self.api_url, {"query": "abc"})

            mock_fn.assert_called_once_with("abc")
            assert response.status_code == 404
