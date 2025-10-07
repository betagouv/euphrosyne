from unittest import mock

import pytest
from django.test import TestCase
from slugify import slugify

from lab.objects import ObjectProviderError
from lab.objects.models import ObjectGroupThumbnail
from lab.tests import factories

from ..catalog import (
    _create_project_page_data,
    _fetch_object_group_from_eros,
    _get_thumbnail_from_object_groups,
    build_object_group_catalog_document,
    build_project_catalog_document,
)


class TestProjectCatalogDocument(TestCase):
    def setUp(self):
        self.run = factories.NotEmbargoedRun(
            project=factories.ProjectWithLeaderFactory()
        )
        self.project = self.run.project
        self.objectgroups = factories.ObjectGroupFactory.create_batch(3)
        for objectgroup in self.objectgroups:
            self.run.run_object_groups.add(objectgroup)

    def test_build_project_catalog_document(self):
        document = build_project_catalog_document(
            project=self.project,
            materials=["or", "verre"],
            leader=self.project.leader,
            object_groups=self.objectgroups,
            object_group_locations=[{"lat": 0, "lon": 0}],
            runs=[self.run],
        )

        assert document.id == f"project-{self.project.id}"
        assert document.category == "project"
        assert document.name == self.project.name
        assert document.slug == self.project.slug
        assert document.materials == ["or", "verre"]
        assert document.comments == self.project.comments
        assert "thumbnail" in document
        assert document.status == str(self.project.status)
        assert document.created == self.project.created
        assert document.project_page_data.leader == {
            "user_first_name": document.project_page_data.leader.user_first_name,
            "user_last_name": document.project_page_data.leader.user_last_name,
        }
        assert document.project_page_data.runs == [
            {
                "id": self.run.id,
                "beamline": self.run.beamline,
                "start_date": self.run.start_date,
                "label": self.run.label,
                "energy_in_kev": self.run.energy_in_keV,
                "particle_type": self.run.particle_type,
                "project_slug": self.run.project.slug,
                "is_data_embargoed": self.run.is_data_embargoed,
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
            for objectgroup in self.objectgroups
        ]
        assert document.discovery_place_points == [{"lat": 0, "lon": 0}]
        assert document.is_data_embargoed is False


class TestObjectGroupCatalogDocument(TestCase):
    def setUp(self):
        self.dating_period = factories.PeriodFactory(concept_id=123)
        self.dating_era = factories.EraFactory(concept_id=345)
        self.discovery_place = factories.LocationFactory()
        self.object_group = factories.ObjectGroupFactory(
            dating_period=self.dating_period,
            dating_era=self.dating_era,
            discovery_place_location=self.discovery_place,
            inventory="123",
        )
        factories.ObjectFactory.create_batch(
            3, group=self.object_group, inventory="456"
        )

        self.project = factories.ProjectWithLeaderFactory()
        self.run = factories.RunFactory(project=self.project)
        self.run.run_object_groups.add(self.object_group)

    def test_build_object_group_catalog_document(self):
        with mock.patch(
            "lab.elasticsearch.catalog.fetch_period_parent_ids_from_id",
            return_value=[345, 567],
        ) as fetch_period_mock:
            with mock.patch(
                "lab.elasticsearch.catalog.fetch_era_parent_ids_from_id",
                return_value=[890, 445],
            ) as fetch_era_mock:
                document = build_object_group_catalog_document(
                    object_group=self.object_group,
                    runs=[self.run],
                    projects=[self.run.project],
                    is_data_embargoed=True,
                )

        fetch_period_mock.assert_called_once_with(123)
        fetch_era_mock.assert_called_once_with(345)

        assert document.object_page_data.runs == [
            {
                "id": self.run.id,
                "beamline": self.run.beamline,
                "start_date": self.run.start_date,
                "label": self.run.label,
                "energy_in_kev": self.run.energy_in_keV,
                "particle_type": self.run.particle_type,
                "project_slug": self.run.project.slug,
                "is_data_embargoed": self.run.is_data_embargoed,
            }
        ]
        assert document.object_page_data.projects == [
            {
                "name": self.project.name,
                "slug": self.project.slug,
                "leader": {
                    "user_first_name": self.project.leader.user.first_name,
                    "user_last_name": self.project.leader.user.last_name,
                },
            }
        ]

        assert document.meta.id == f"object-{self.object_group.id}"
        assert document.id == f"object-{self.object_group.id}"
        assert document.category == "object"
        assert (
            document.slug
            == slugify(self.object_group.label) + f"-{self.object_group.id}"
        )
        assert document.is_data_embargoed is True
        assert "thumbnail" in document
        assert document.materials == self.object_group.materials
        assert document.collection == self.object_group.collection
        assert document.c2rmf_id == self.object_group.c2rmf_id
        assert document.inventory_number == self.object_group.inventory
        assert set(document.inventory_numbers) == set(["456", "123"])
        assert document.name == self.object_group.label
        assert len(document.objects) == self.object_group.object_set.count()
        assert all(
            field in doc
            for doc in document.objects
            for field in ["label", "inventory", "collection"]
        )

        assert (
            document.discovery_place_label
            == self.object_group.discovery_place_location.label
        )
        assert document.discovery_place_point == {
            "lat": self.object_group.discovery_place_location.latitude,
            "lon": self.object_group.discovery_place_location.longitude,
        }
        assert document.discovery_place_points == [
            {
                "lat": self.object_group.discovery_place_location.latitude,
                "lon": self.object_group.discovery_place_location.longitude,
            }
        ]

        assert document.dating_period_label == self.dating_period.label
        assert document.dating_period_theso_huma_num_id == 123
        assert document.dating_period_theso_huma_num_parent_ids == [345, 567]

        assert document.dating_era_label == self.dating_era.label
        assert document.dating_era_theso_huma_num_id == 345
        assert document.dating_era_theso_huma_num_parent_ids == [890, 445]

    def test_no_call_era_thesaurus_if_no_concept_id(self):
        self.object_group.dating_era.concept_id = None
        self.object_group.save()

        with mock.patch(
            "lab.elasticsearch.catalog.fetch_period_parent_ids_from_id",
        ):
            with mock.patch(
                "lab.elasticsearch.catalog.fetch_era_parent_ids_from_id",
            ) as fetch_era_mock:
                build_object_group_catalog_document(
                    object_group=self.object_group,
                    runs=[self.run],
                    projects=[self.run.project],
                    is_data_embargoed=True,
                )

        fetch_era_mock.assert_not_called()

    def test_no_call_period_thesaurus_if_no_concept_id(self):
        self.object_group.dating_period.concept_id = None
        self.object_group.save()

        with mock.patch(
            "lab.elasticsearch.catalog.fetch_period_parent_ids_from_id",
        ) as fetch_period_mock:
            with mock.patch(
                "lab.elasticsearch.catalog.fetch_era_parent_ids_from_id",
            ):
                build_object_group_catalog_document(
                    object_group=self.object_group,
                    runs=[self.run],
                    projects=[self.run.project],
                    is_data_embargoed=True,
                )

        fetch_period_mock.assert_not_called()


@pytest.mark.django_db
@mock.patch("lab.elasticsearch.catalog.fetch_full_objectgroup")
def test_build_object_group_calls_eros_if_c2rmf_id(eros_mock: mock.MagicMock):
    object_group = factories.ObjectGroupFactory(
        c2rmf_id="abc",
    )
    eros_mock.return_value = object_group
    build_object_group_catalog_document(
        object_group=object_group,
        runs=[],
        projects=[],
        is_data_embargoed=True,
    )

    eros_mock.assert_called_once_with("c2rmf", "abc", object_group)


@pytest.mark.django_db
@mock.patch("lab.elasticsearch.catalog.fetch_full_objectgroup")
def test_create_project_page_data_calls_eros_if_c2rmf_id(eros_mock: mock.MagicMock):
    object_group = factories.ObjectGroupFactory(
        c2rmf_id="abc",
    )
    eros_mock.return_value = object_group
    _create_project_page_data(
        runs=[factories.RunFactory()], object_groups=[object_group], leader=None
    )

    eros_mock.assert_called_once_with("c2rmf", "abc", object_group)


@pytest.mark.django_db
@mock.patch("lab.elasticsearch.catalog.fetch_full_objectgroup")
def test_fetch_object_group_from_eros_if_eros_fails_returns_og(
    eros_mock: mock.MagicMock,
):
    object_group = factories.ObjectGroupFactory(
        c2rmf_id="abc",
    )
    eros_mock.side_effect = ObjectProviderError
    assert (
        _fetch_object_group_from_eros(
            c2rmf_id="abc",
            object_group=object_group,
        )
        == object_group
    )


def test_get_thumbnail_from_object_groups():
    object_group_with_thumbnail = mock.Mock()
    object_group_with_thumbnail.thumbnail.image.url = "http://example.com/thumbnail.jpg"
    object_group_with_thumbnail.thumbnail.copyright = "Copyright"

    object_group_without_thumbnail = mock.Mock()
    type(object_group_without_thumbnail).thumbnail = mock.PropertyMock(
        side_effect=ObjectGroupThumbnail.DoesNotExist
    )

    object_groups = [object_group_without_thumbnail, object_group_with_thumbnail]

    thumbnail = _get_thumbnail_from_object_groups(object_groups)
    assert thumbnail.url == "http://example.com/thumbnail.jpg"
    assert thumbnail.copyright == "Copyright"


def test_get_thumbnail_from_object_groups_no_thumbnail():
    object_group_without_thumbnail = mock.Mock()
    type(object_group_without_thumbnail).thumbnail = mock.PropertyMock(
        side_effect=ObjectGroupThumbnail.DoesNotExist
    )

    object_groups = [object_group_without_thumbnail]

    thumbnail_url = _get_thumbnail_from_object_groups(object_groups)
    assert thumbnail_url is None
