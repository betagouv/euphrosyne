import logging
from typing import TypedDict

from slugify import slugify

from lab.methods.dto import method_model_to_dto
from lab.models import ObjectGroup, ObjectGroupThumbnail, Project
from lab.objects.c2rmf import ErosHTTPError, fetch_full_objectgroup_from_eros
from lab.participations.models import Participation
from lab.runs.models import Run
from lab.thesauri.opentheso import (
    fetch_era_parent_ids_from_id,
    fetch_period_parent_ids_from_id,
)

from .documents import (
    CatalogItem,
    ImageDoc,
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


class DatingDict(TypedDict, total=False):
    dating_period_label: str | None
    dating_period_theso_huma_num_id: str | None
    dating_period_theso_huma_num_parent_ids: list[str] | None
    dating_era_label: str | None
    dating_era_theso_huma_num_id: str | None
    dating_era_theso_huma_num_parent_ids: list[str] | None


def _get_thumbnail_from_object_groups(
    object_groups: list[ObjectGroup],
) -> ImageDoc | None:
    for object_group in object_groups:
        try:
            return ImageDoc(
                url=object_group.thumbnail.image.url,
                copyright=object_group.thumbnail.copyright,
            )
        except ObjectGroupThumbnail.DoesNotExist:
            pass
    return None


def _create_leader_doc(leader: Participation):
    doc = LeaderDoc(
        user_first_name=leader.user.first_name,
        user_last_name=leader.user.last_name,
    )
    if leader.institution:
        doc.institution_name = leader.institution.name  # type: ignore[assignment]
        doc.institution_country = leader.institution.country  # type: ignore[assignment]
    return doc


def _create_project_page_data(
    runs: list[Run],
    object_groups: list[ObjectGroup],
    leader: Participation | None,
    skip_eros: bool = False,
):
    page_data = ProjectPageData(leader=_create_leader_doc(leader) if leader else None)
    for run in runs:
        page_data.add_run(
            run=RunDoc(
                id=run.id,
                label=run.label,
                start_date=run.start_date,
                particle_type=run.particle_type,
                energy_in_kev=run.energy_in_keV,
                beamline=run.beamline,
                project_slug=run.project.slug,
                is_data_embargoed=run.is_data_embargoed,
            ),
            methods=method_model_to_dto(run),
        )
    for object_group in object_groups:
        discovery_place_label: str | None = None
        dating_era_label: str | None = None
        dating_period_label: str | None = None
        if object_group.c2rmf_id and not skip_eros:
            # Fetch object group from EROS
            try:
                object_group = (
                    fetch_full_objectgroup_from_eros(
                        c2rmf_id=object_group.c2rmf_id, object_group=object_group
                    )
                    or object_group
                )
            except ErosHTTPError as error:
                logger.error(
                    "Failed to fetch object group %s from EROS: %s",
                    object_group.id,
                    error,
                    exc_info=True,
                )
        else:
            # Fetch thesauri information for non-EROS object groups
            if object_group.dating_period:
                dating_period_label = object_group.dating_period.label
            if object_group.dating_era:
                dating_era_label = object_group.dating_era.label

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
                    "inventory": object_group.inventory,
                    "dating_period_label": dating_period_label,
                    "dating_era_label": dating_era_label,
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
                id=run.id,
                label=run.label,
                start_date=run.start_date,
                particle_type=run.particle_type,
                energy_in_kev=run.energy_in_keV,
                beamline=run.beamline,
                project_slug=run.project.slug,
                is_data_embargoed=run.is_data_embargoed,
            ),
            methods=method_model_to_dto(run),
        )
    for project in projects:
        page_data.add_project(
            name=project.name,
            slug=project.slug,
            leader=_create_leader_doc(project.leader) if project.leader else None,
        )
    return page_data


# pylint: disable=too-many-arguments
def build_project_catalog_document(
    project: Project,
    materials: list[str],
    leader: Participation | None,
    object_groups: list[ObjectGroup],
    object_group_locations: list[LocationDict],
    runs: list[Run],
    skip_eros: bool = False,
):
    page_data = _create_project_page_data(
        leader=leader, runs=runs, object_groups=object_groups, skip_eros=skip_eros
    )

    _id = f"project-{project.id}"

    is_data_embargoed = all(run.is_data_embargoed for run in runs)

    if project.slug == "2025-itineris":
        print(is_data_embargoed)

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
        is_data_embargoed=is_data_embargoed,
        thumbnail=_get_thumbnail_from_object_groups(object_groups=object_groups),
    )
    return catalog_item


# pylint: disable=too-many-arguments, too-many-locals
def build_object_group_catalog_document(  # noqa: C901
    object_group: ObjectGroup,
    projects: list[Project],
    runs: list[Run],
    is_data_embargoed: bool,
    skip_eros: bool = False,
):
    # Page data
    page_data = _create_object_group_page_data(projects=projects, runs=runs)

    # Location
    location_geopoint: LocationDict | None = None
    location_label: str | None = None
    locations = []

    if object_group.c2rmf_id and not skip_eros:
        # Fetch object group from EROS
        object_group = _fetch_object_group_from_eros(
            c2rmf_id=object_group.c2rmf_id, object_group=object_group
        )

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
    dating_dict: DatingDict = {}
    for field_name in ["dating_period", "dating_era"]:
        fetch_parent_ids_fn = (
            fetch_era_parent_ids_from_id
            if field_name == "dating_era"
            else fetch_period_parent_ids_from_id
        )
        if getattr(object_group, field_name):
            theso_huma_num_parent_ids = None
            if getattr(getattr(object_group, field_name), "concept_id"):
                theso_huma_num_parent_ids = fetch_parent_ids_fn(
                    getattr(object_group, field_name).concept_id
                )
            dating_dict = {
                **dating_dict,
                f"{field_name}_label": getattr(  # type: ignore
                    object_group, field_name
                ).label,
                f"{field_name}_theso_huma_num_id": getattr(  # type: ignore
                    object_group, field_name
                ).concept_id,
                # type: ignore
                f"{field_name}_theso_huma_num_parent_ids": theso_huma_num_parent_ids,
            }

    # Thumbnail
    thumbnail: ImageDoc | None = None
    try:
        thumbnail = ImageDoc(
            url=object_group.thumbnail.image.url,
            copyright=object_group.thumbnail.copyright,
        )
    except ObjectGroupThumbnail.DoesNotExist:
        pass

    _id = f"object-{object_group.id}"
    catalog_item = CatalogItem(
        meta={"id": _id},
        id=_id,
        category="object",
        name=object_group.label,
        slug=slugify(object_group.label) + f"-{object_group.id}",
        is_data_embargoed=is_data_embargoed,
        thumbnail=thumbnail,
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
        **dating_dict,
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

    catalog_item.collections = list(set(collections))  # type: ignore[assignment]
    catalog_item.inventory_numbers = list(
        set(inventory_numbers)
    )  # type: ignore[assignment]

    return catalog_item


def _fetch_object_group_from_eros(
    c2rmf_id: str, object_group: ObjectGroup
) -> ObjectGroup:
    try:
        object_group_with_eros_information = fetch_full_objectgroup_from_eros(
            c2rmf_id=c2rmf_id,
            object_group=object_group,
        )
    except ErosHTTPError as error:
        logger.error("Failed to fetch object group from EROS: %s", error, exc_info=True)
        return object_group
    return object_group_with_eros_information or object_group
