import logging
from typing import Generic, TypedDict, TypeVar, Unpack

from django.conf import settings
from opensearchpy import OpenSearch

from lab.elasticsearch import queries
from lab.objects.models import ObjectGroup
from lab.projects.models import Project
from lab.runs.models import Run

from .catalog import (
    LocationDict,
    build_object_group_catalog_document,
    build_project_catalog_document,
)
from .documents import CatalogItem

logger = logging.getLogger(__name__)

_T = TypeVar("_T")

INDEX_NAME = "catalog"


class Singleton(type, Generic[_T]):
    _instances: dict["Singleton[_T]", _T] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class ObjectGroupExtraDict(TypedDict):
    projects: list[Project]
    runs: list[Run]
    is_data_available: bool


class CatalogClient(metaclass=Singleton):
    def __init__(self, index_name: str = INDEX_NAME):
        self.index_name = index_name
        for setting in [
            "ELASTICSEARCH_USERNAME",
            "ELASTICSEARCH_PASSWORD",
            "ELASTICSEARCH_HOST",
        ]:
            if getattr(settings, setting, None) is None:
                raise ValueError(
                    "Incorrect elasticsearch configuration. %s is missing" % setting
                )
        user, password, (protocol, host) = (
            settings.ELASTICSEARCH_USERNAME,
            settings.ELASTICSEARCH_PASSWORD,
            settings.ELASTICSEARCH_HOST.split("://"),  # type: ignore
        )
        self.client = client = OpenSearch(
            hosts=[f"{protocol}://{user}:{password}@{host}"],
            http_compress=True,  # enables gzip compression for request bodies
            use_ssl=False,
            ssl_assert_hostname=False,
            ssl_show_warn=False,
        )
        CatalogItem.init(using=client)

    def search(self, **kwargs: Unpack[queries.QueryParams]):
        query = queries.filter_query(kwargs)
        return self.client.search(index=self.index_name, body=query)

    def aggregate_terms(
        self, field: str, query: str | None = None, exclude: list[str] | None = None
    ):
        return self.client.search(
            queries.terms_agg(field, query=query, exclude=exclude)
        )

    def aggregate_date(self, field: str, interval: str):
        return self.client.search(queries.date_historiogram_agg(field, interval))

    def index_from_projects(self, projects: list[Project], skip_eros: bool = False):
        """Index projects and related object groups"""
        objectgroups_dict: dict[ObjectGroup, ObjectGroupExtraDict] = {}
        for project in projects:
            leader = project.leader
            runs = list(project.runs.all())
            objectgroups = list(
                set(obj for run in runs for obj in run.run_object_groups.all())
            )
            materials = []
            locations: list[LocationDict] = []
            for objectgroup in objectgroups:
                materials.extend(objectgroup.materials)
                if (
                    objectgroup.discovery_place_location
                    and objectgroup.discovery_place_location.latitude
                    and objectgroup.discovery_place_location.longitude
                ):
                    locations.append(
                        {
                            "lat": objectgroup.discovery_place_location.latitude,
                            "lon": objectgroup.discovery_place_location.longitude,
                        }
                    )
                if objectgroup not in objectgroups_dict:
                    objectgroups_dict[objectgroup] = {
                        "projects": [project],
                        "runs": runs,
                        "is_data_available": project.is_data_available,
                    }
                else:
                    objectgroups_dict[objectgroup]["runs"].extend(runs)
                    objectgroups_dict[objectgroup]["projects"].append(project)
                    objectgroups_dict[objectgroup][
                        "is_data_available"
                    ] |= project.is_data_available
            logger.debug("Saving project %s", str(project))
            item = build_project_catalog_document(
                project=project,
                materials=list(set(materials)),
                leader=leader,
                object_groups=objectgroups,
                object_group_locations=locations,
                runs=runs,
                skip_eros=skip_eros,
            )
            item.save(using=self.client)
        for obj, extra in objectgroups_dict.items():
            logger.debug("Saving object group %s", str(obj))
            item = build_object_group_catalog_document(
                object_group=obj,
                projects=extra["projects"],
                runs=extra["runs"],
                is_data_available=extra["is_data_available"],
                skip_eros=skip_eros,
            )
            item.save(using=self.client)

    def delete_index(self):
        """Delete an index by name"""
        if self.client.indices.exists(index=self.index_name):
            self.client.indices.delete(index=self.index_name)
            logger.info("Deleted index: %s", self.index_name)
        else:
            logger.warning("Index %s does not exist. Skipping delete.", self.index_name)
