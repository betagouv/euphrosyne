import json
from unittest import mock

from django.test import Client, SimpleTestCase

from ._mock import BASE_SEARCH_PARAMS

BASE_API_URL = "/api/lab/catalog"


class TestProjectListView(SimpleTestCase):
    def setUp(self):
        self.client = Client()

    @mock.patch("lab.elasticsearch.api_views.CatalogClient")
    def test_search_view(self, mock_cls: mock.MagicMock):
        mock_cls.return_value.search.return_value = {"results": []}
        params = BASE_SEARCH_PARAMS
        response = self.client.post(
            f"{BASE_API_URL}/search",
            json.dumps(params),
            content_type="application/json",
        )

        mock_cls.return_value.search.assert_called_once_with(**params)

        assert response.status_code == 200
        assert response.json() == {"results": []}

    def test_aggregate_field_view(self):
        with mock.patch("lab.elasticsearch.api_views.CatalogClient") as mock_cls:
            mock_cls.return_value.aggregate_terms.return_value = {"results": []}
            response = self.client.get(
                f"{BASE_API_URL}/aggregate"
                + "?field=field"
                + "&query=query"
                + "&exclude=exclude1,exclude2"
            )

        mock_cls.return_value.aggregate_terms.assert_called_once_with(
            "field",
            query="query",
            exclude=["exclude1", "exclude2"],
        )

        assert response.status_code == 200

    def test_aggregate_field_view_when_field_is_missing(self):
        response = self.client.get(f"{BASE_API_URL}/aggregate")
        assert response.status_code == 400
        assert response.json() == {"error": "'field' query param is required"}

    def test_aggregate_created_view(self):
        with mock.patch("lab.elasticsearch.api_views.CatalogClient") as mock_cls:
            mock_cls.return_value.aggregate_date.return_value = {"results": []}
            response = self.client.get(f"{BASE_API_URL}/aggregate-created")

        mock_cls.return_value.aggregate_date.assert_called_once_with(
            "created",
            "year",
        )

        assert response.status_code == 200
        assert response.json() == {"results": []}
