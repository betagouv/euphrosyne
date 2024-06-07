from unittest import mock

import pytest
from pytest import fixture

from lab.tests import factories as lab_factories

from ..client import CatalogClient
from ._mock import BASE_SEARCH_PARAMS, BASE_SEARCH_PARAMS_RELATED_QUERY


@fixture(name="catalog_client", scope="function")
def catalog_client_fixture():
    with mock.patch("lab.elasticsearch.client.OpenSearch"):
        yield CatalogClient()


@fixture(autouse=True)
def set_es_settings(settings):
    settings.ELASTICSEARCH_USERNAME = "user"
    settings.ELASTICSEARCH_PASSWORD = "password"
    settings.ELASTICSEARCH_HOST = "http://localhost:9200"


def test_search(catalog_client: CatalogClient):
    catalog_client.search(**BASE_SEARCH_PARAMS)
    catalog_client.client.search.assert_called_with(
        index="catalog",
        body={
            **BASE_SEARCH_PARAMS_RELATED_QUERY,
            "sort": [{"created": {"order": "asc"}}],
        },
    )


def test_aggregate_terms(catalog_client: CatalogClient):
    catalog_client.aggregate_terms("field", query="query", exclude=["exclude"])
    catalog_client.client.search.assert_called_with(
        {
            "size": 0,
            "aggs": {
                "field": {
                    "terms": {
                        "field": "field",
                        "include": ".*query.*",
                        "exclude": "exclude",
                    }
                }
            },
        }
    )


def test_aggregate_date(catalog_client: CatalogClient):
    catalog_client.aggregate_date("field", "interval")
    catalog_client.client.search.assert_called_with(
        {
            "size": 0,
            "aggs": {
                "field": {
                    "date_histogram": {
                        "field": "field",
                        "calendar_interval": "interval",
                    }
                }
            },
        }
    )


@pytest.mark.django_db
def test_index_from_projects(catalog_client: CatalogClient):
    dating = lab_factories.PeriodFactory(theso_joconde_id=123)
    discovery_place = lab_factories.LocationFactory()
    object_group = lab_factories.ObjectGroupFactory(
        dating=dating,
        discovery_place_location=discovery_place,
        inventory="123",
    )
    lab_factories.ObjectFactory.create_batch(3, group=object_group, inventory="456")

    project = lab_factories.ProjectWithLeaderFactory()
    run = lab_factories.RunFactory(project=project)
    run.run_object_groups.add(object_group)

    with mock.patch(
        "lab.elasticsearch.client.build_object_group_catalog_document"
    ) as build_object_group_mock:
        with mock.patch(
            "lab.elasticsearch.client.build_project_catalog_document"
        ) as build_project_group_mock:
            catalog_client.index_from_projects(projects=[project])

    build_project_group_mock.assert_called_once_with(
        project=project,
        materials=list(set(object_group.materials)),
        leader=project.leader,
        object_groups=[object_group],
        object_group_locations=[
            {
                "lat": float(discovery_place.latitude),
                "lon": float(discovery_place.longitude),
            }
        ],
        runs=[run],
    )

    build_object_group_mock.assert_called_once_with(
        object_group=object_group,
        projects=[project],
        runs=[run],
        is_data_available=project.is_data_available,
    )
