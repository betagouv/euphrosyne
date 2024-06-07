import logging
from typing import TypedDict

from slugify import slugify

from lab.methods.dto import method_model_to_dto
from lab.models import ObjectGroup, Project
from lab.opentheso import fetch_epoques_parent_ids_from_id
from lab.participations.models import Participation
from lab.runs.models import Run

from .documents import (
    CatalogItem,
    LeaderDoc,
    ObjectGroupDoc,
    ObjectPageData,
    ProjectPageData,
    RunDoc,
)

logger = logging.getLogger(__name__)


class LocationDict(TypedDict):
    lat: float
    lon: float


def _create_leader_doc(leader: Participation):
    doc = LeaderDoc(
        user_first_name=leader.user.first_name,
        user_last_name=leader.user.last_name,
    )
    if leader.institution:
        doc.institution_name = leader.institution.name
        doc.institution_country = leader.institution.country
    return doc


def _create_project_page_data(
    runs: list[Run], object_groups: list[ObjectGroup], leader: Participation | None
):
    page_data = ProjectPageData(leader=_create_leader_doc(leader) if leader else None)
    for run in runs:
        page_data.add_run(
            run=RunDoc(
                label=run.label,
                start_date=run.start_date,
                particle_type=run.particle_type,
                energy_in_kev=run.energy_in_keV,
                beamline=run.beamline,
                project_slug=run.project.slug,
            ),
            methods=method_model_to_dto(run),
        )
    for object_group in object_groups:

        dating_label: str | None = None
        if object_group.dating:
            dating_label = object_group.dating.label

        discovery_place_label: str | None = None
        if object_group.discovery_place_location:
            discovery_place_label = object_group.discovery_place_location.label
        page_data.add_object_group(
            object_group=ObjectGroupDoc(
                **{
                    "id": object_group.id,
                    "c2rmf_id": object_group.c2rmf_id,
                    "label": object_group.label,
                    "materials": object_group.materials,
                    "discovery_place_label": discovery_place_label,
                    "collection": object_group.collection,
                    "dating_label": dating_label,
                    "inventory": object_group.inventory,
                }
            ),
            objects=list(
                object_group.object_set.values("label", "inventory", "collection")
            ),
        )
    return page_data


def _create_object_group_page_data(projects: list[Project], runs: list[Run]):
    page_data = ObjectPageData()
    for run in runs:
        page_data.add_run(
            run=RunDoc(
                label=run.label,
                start_date=run.start_date,
                particle_type=run.particle_type,
                energy_in_kev=run.energy_in_keV,
                beamline=run.beamline,
                project_slug=run.project.slug,
            ),
            methods=method_model_to_dto(run),
        )
    for project in projects:
        page_data.add_project(
            name=project.name,
            slug=project.slug,
            leader=_create_leader_doc(project.leader),
        )
    return page_data


# pylint: disable=too-many-arguments
def build_project_catalog_document(
    project: Project,
    materials: list[str],
    leader: Participation,
    object_groups: list[ObjectGroup],
    object_group_locations: list[LocationDict],
    runs: list[Run],
):
    page_data = _create_project_page_data(
        leader=leader, runs=runs, object_groups=object_groups
    )
    _id = f"project-{project.id}"
    catalog_item = CatalogItem(
        meta={"id": _id},
        category="project",
        id=_id,
        name=project.name,
        slug=project.slug,
        materials=materials,
        comments=project.comments,
        status=str(project.status),
        created=project.created,
        project_page_data=page_data,
        discovery_place_points=object_group_locations,
        is_data_available=project.is_data_available,
    )
    return catalog_item


# pylint: disable=too-many-arguments, too-many-locals
def build_object_group_catalog_document(
    object_group: ObjectGroup,
    projects: list[Project],
    runs: list[Run],
    is_data_available: bool,
):
    # Page data
    page_data = _create_object_group_page_data(projects=projects, runs=runs)

    # Location
    location_geopoint: LocationDict | None = None
    location_label: str | None = None
    locations = []
    if (
        object_group.discovery_place_location
        and object_group.discovery_place_location.latitude
        and object_group.discovery_place_location.longitude
    ):
        location_geopoint = {
            "lat": object_group.discovery_place_location.latitude,
            "lon": object_group.discovery_place_location.longitude,
        }
        location_label = object_group.discovery_place_location.label
        locations = [location_geopoint]

    # Dating
    dating_label: str | None = None
    dating_theso_huma_num_id: str | None = None
    dating_theso_huma_num_parent_ids: list[str] | None = []
    if object_group.dating:
        dating_label = object_group.dating.label
        dating_theso_huma_num_id = object_group.dating.theso_joconde_id
        dating_theso_huma_num_parent_ids = fetch_epoques_parent_ids_from_id(
            object_group.dating.theso_joconde_id
        )
    _id = f"object-{object_group.id}"
    catalog_item = CatalogItem(
        meta={"id": _id},
        id=_id,
        category="object",
        name=object_group.label,
        slug=slugify(object_group.label) + f"-{object_group.id}",
        is_data_available=is_data_available,
        created=object_group.created,
        materials=object_group.materials,
        object_page_data=page_data,
        c2rmf_id=object_group.c2rmf_id,
        collection=object_group.collection,
        inventory_number=object_group.inventory,
        inventory_numbers=[object_group.object_set.values_list("inventory", flat=True)],
        discovery_place_label=location_label,
        discovery_place_point=location_geopoint,
        discovery_place_points=locations,
        dating_label=dating_label,
        dating_theso_huma_num_id=dating_theso_huma_num_id,
        dating_theso_huma_num_parent_ids=dating_theso_huma_num_parent_ids,
    )

    collections = []
    inventory_numbers = []
    if object_group.collection:
        collections.append(object_group.collection)
    if object_group.inventory:
        inventory_numbers.append(object_group.inventory)
    for obj in object_group.object_set.all():
        catalog_item.add_object(
            label=obj.label,
            collection=obj.collection,
            inventory=obj.inventory,
        )
        if obj.collection:
            collections.append(obj.collection)
        if obj.inventory:
            inventory_numbers.append(obj.inventory)
    catalog_item.collections = list(set(collections))
    catalog_item.inventory_numbers = list(set(inventory_numbers))

    return catalog_item
