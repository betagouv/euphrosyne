from unittest import mock

from django.test import Client, TestCase
from django.urls import reverse

from euphro_auth.tests import factories as auth_factories
from lab.objects.providers import ObjectProviderError


class TestProjectListView(TestCase):
    def setUp(self):
        self.client = client = Client()
        self.api_url = reverse(
            "api:objectgroup-provider-fetch", kwargs={"provider_name": "eros"}
        )

        client.force_login(auth_factories.LabAdminUserFactory())

    def test_route_auth(self):
        client = Client()
        response = client.post(self.api_url, {"query": "abc"})

        assert response.status_code == 403

    def test_call_eros(self):
        with mock.patch(
            "lab.api_views.objectgroup.fetch_partial_objectgroup"
        ) as mock_fn:
            obj = {"label": "atitle"}
            mock_fn.return_value = obj
            response = self.client.post(self.api_url, {"query": "abc"})

            mock_fn.assert_called_once_with("eros", "abc")
            assert response.status_code == 200
            assert response.json() == {
                "external_reference_id": "abc",
                "label": "atitle",
            }

    def test_eros_error_return_not_found(self):
        with mock.patch(
            "lab.api_views.objectgroup.fetch_partial_objectgroup"
        ) as mock_fn:
            mock_fn.side_effect = ObjectProviderError
            response = self.client.post(self.api_url, {"query": "abc"})

            mock_fn.assert_called_once_with("eros", "abc")
            assert response.status_code == 404

    def test_eros_return_none_return_not_found(self):
        with mock.patch(
            "lab.api_views.objectgroup.fetch_partial_objectgroup"
        ) as mock_fn:
            mock_fn.return_value = None
            response = self.client.post(self.api_url, {"query": "abc"})

            mock_fn.assert_called_once_with("eros", "abc")
            assert response.status_code == 404
