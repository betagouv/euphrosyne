from unittest import mock

import pytest
from slugify import slugify

from lab.tests import factories

from ..catalog import (
    build_object_group_catalog_document,
    build_project_catalog_document,
)


@pytest.mark.django_db
def test_build_project_catalog_document():
    run = factories.RunFactory(project=factories.ProjectWithLeaderFactory())
    project = run.project
    objectgroups = factories.ObjectGroupFactory.create_batch(3)
    for objectgroup in objectgroups:
        run.run_object_groups.add(objectgroup)

    document = build_project_catalog_document(
        project=project,
        materials=["or", "verre"],
        leader=project.leader,
        object_groups=objectgroups,
        object_group_locations=[{"lat": 0, "lon": 0}],
        runs=[run],
    )

    assert document.id == f"project-{project.id}"
    assert document.category == "project"
    assert document.name == project.name
    assert document.slug == project.slug
    assert document.materials == ["or", "verre"]
    assert document.comments == project.comments
    assert document.status == str(project.status)
    assert document.created == project.created
    assert document.project_page_data.leader == {
        "user_first_name": document.project_page_data.leader.user_first_name,
        "user_last_name": document.project_page_data.leader.user_last_name,
    }
    assert document.project_page_data.runs == [
        {
            "id": run.id,
            "beamline": run.beamline,
            "start_date": run.start_date,
            "label": run.label,
            "energy_in_kev": run.energy_in_keV,
            "particle_type": run.particle_type,
            "project_slug": run.project.slug,
        }
    ]
    assert document.project_page_data.object_groups == [
        {
            "c2rmf_id": objectgroup.c2rmf_id,
            "collection": objectgroup.collection,
            "dating_era_label": objectgroup.dating_era.label,
            "dating_period_label": objectgroup.dating_period.label,
            "discovery_place_label": (
                objectgroup.discovery_place.label
                if objectgroup.discovery_place
                else None
            ),
            "id": objectgroup.id,
            "inventory": objectgroup.inventory,
            "label": objectgroup.label,
            "materials": objectgroup.materials,
            "objects": [
                {
                    "label": object.label,
                    "inventory": object.inventory,
                    "collection": object.collection,
                }
                for object in objectgroup.object_set.all()
            ],
        }
        for objectgroup in objectgroups
    ]
    assert document.discovery_place_points == [{"lat": 0, "lon": 0}]
    assert document.is_data_available == project.is_data_available


@pytest.mark.django_db
def test_build_object_group_catalog_document():
    dating_period = factories.PeriodFactory(concept_id=123)
    dating_era = factories.EraFactory(concept_id=345)
    discovery_place = factories.LocationFactory()
    object_group = factories.ObjectGroupFactory(
        dating_period=dating_period,
        dating_era=dating_era,
        discovery_place_location=discovery_place,
        inventory="123",
    )
    factories.ObjectFactory.create_batch(3, group=object_group, inventory="456")

    project = factories.ProjectWithLeaderFactory()
    run = factories.RunFactory(project=project)
    run.run_object_groups.add(object_group)

    with mock.patch(
        "lab.elasticsearch.catalog.fetch_period_parent_ids_from_id",
        return_value=[345, 567],
    ) as fetch_period_mock:
        with mock.patch(
            "lab.elasticsearch.catalog.fetch_era_parent_ids_from_id",
            return_value=[890, 445],
        ) as fetch_era_mock:
            document = build_object_group_catalog_document(
                object_group=object_group,
                runs=[run],
                projects=[run.project],
                is_data_available=True,
            )

    fetch_period_mock.assert_called_once_with(123)
    fetch_era_mock.assert_called_once_with(345)

    assert document.object_page_data.runs == [
        {
            "id": run.id,
            "beamline": run.beamline,
            "start_date": run.start_date,
            "label": run.label,
            "energy_in_kev": run.energy_in_keV,
            "particle_type": run.particle_type,
            "project_slug": run.project.slug,
        }
    ]
    assert document.object_page_data.projects == [
        {
            "name": project.name,
            "slug": project.slug,
            "leader": {
                "user_first_name": project.leader.user.first_name,
                "user_last_name": project.leader.user.last_name,
            },
        }
    ]

    assert document.meta.id == f"object-{object_group.id}"
    assert document.id == f"object-{object_group.id}"
    assert document.category == "object"
    assert document.slug == slugify(object_group.label) + f"-{object_group.id}"
    assert document.is_data_available is True
    assert document.materials == object_group.materials
    assert document.collection == object_group.collection
    assert document.c2rmf_id == object_group.c2rmf_id
    assert document.inventory_number == object_group.inventory
    assert set(document.inventory_numbers) == set(["456", "123"])
    assert document.name == object_group.label
    assert len(document.objects) == object_group.object_set.count()
    assert all(
        field in doc
        for doc in document.objects
        for field in ["label", "inventory", "collection"]
    )

    assert document.discovery_place_label == object_group.discovery_place_location.label
    assert document.discovery_place_point == {
        "lat": object_group.discovery_place_location.latitude,
        "lon": object_group.discovery_place_location.longitude,
    }
    assert document.discovery_place_points == [
        {
            "lat": object_group.discovery_place_location.latitude,
            "lon": object_group.discovery_place_location.longitude,
        }
    ]

    assert document.dating_period_label == dating_period.label
    assert document.dating_period_theso_huma_num_id == 123
    assert document.dating_period_theso_huma_num_parent_ids == [345, 567]

    assert document.dating_era_label == dating_era.label
    assert document.dating_era_theso_huma_num_id == 345
    assert document.dating_era_theso_huma_num_parent_ids == [890, 445]
