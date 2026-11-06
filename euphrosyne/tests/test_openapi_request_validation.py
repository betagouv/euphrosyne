from unittest import mock

import pytest

from .openapi_request_validation import OpenAPIRequestValidationError, get_schema

AGGREGATE_URL = "/api/lab/catalog/aggregate"
SEARCH_URL = "/api/lab/catalog/search"


@pytest.fixture(autouse=True)
def catalog_client():
    with mock.patch("lab.elasticsearch.api_views.CatalogClient") as client_cls:
        client_cls.return_value.aggregate_terms.return_value = {}
        client_cls.return_value.search.return_value = {}
        yield client_cls


def test_conforming_requests_pass(client):
    assert client.get(AGGREGATE_URL, {"field": "materials"}).status_code == 200
    assert (
        client.post(
            SEARCH_URL,
            {"q": "vase", "from": 10, "location": {"top_left": {"lat": 1, "lon": 2}}},
            content_type="application/json",
        ).status_code
        == 200
    )


@pytest.mark.parametrize(
    "query",
    [
        {},  # missing required parameter
        {"field": "materials", "unknown": "1"},  # undeclared parameter
    ],
)
def test_non_conforming_query_parameters_fail(client, query):
    with pytest.raises(OpenAPIRequestValidationError):
        client.get(AGGREGATE_URL, query)


@pytest.mark.parametrize(
    "body",
    [
        {"size": "ten"},  # wrong type
        {"category": "person"},  # not in enum
        {"q": "vase", "unknown": 1},  # undeclared field
    ],
)
def test_non_conforming_bodies_fail(client, body):
    with pytest.raises(OpenAPIRequestValidationError):
        client.post(SEARCH_URL, body, content_type="application/json")


def test_undocumented_method_fails(client):
    with pytest.raises(OpenAPIRequestValidationError):
        client.put(SEARCH_URL, {}, content_type="application/json")


@pytest.mark.openapi_invalid_request
def test_marker_disables_validation(client):
    assert client.get(AGGREGATE_URL).status_code == 400


# Operations that take no request body.
BODYLESS_OPERATIONS = {
    ("post", "/api/auth/token/"),  # session authenticated
    ("post", "/api/data-management/projects/{project_id}/cool"),
    ("post", "/api/data-management/projects/{project_id}/restore"),
}


def test_every_write_operation_documents_its_body():
    schema = get_schema()
    missing = [
        (method, path)
        for path, operations in schema["paths"].items()
        for method, operation in operations.items()
        if method in ("post", "put", "patch")
        and "requestBody" not in operation
        and (method, path) not in BODYLESS_OPERATIONS
    ]
    assert not missing
