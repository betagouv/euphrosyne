import pytest
from django.forms import widgets

from lab.thesauri.models import Era

from ...forms import ObjectGroupAddChoices, ObjectGroupForm
from ...models import Location, ObjectGroup, Period


def test_form_render_single_object_initial_values():
    object_form = ObjectGroupForm()
    assert (
        object_form.fields["add_type"].initial
        == ObjectGroupAddChoices.SINGLE_OBJECT.value[0]
    )
    assert object_form.fields["object_count"].initial == 1


def test_disable_add_type_when_bound():
    object_form = ObjectGroupForm(instance=ObjectGroup(id=1, object_count=1))
    assert object_form.fields["add_type"].widget.attrs["disabled"]


def test_set_add_type_when_instance_is_group():
    object_form = ObjectGroupForm(instance=ObjectGroup(id=1, object_count=30))
    assert (
        object_form.fields["add_type"].initial
        == ObjectGroupAddChoices.OBJECT_GROUP.value[0]
    )


def test_set_object_count_widget_when_instance_is_group():
    object_form = ObjectGroupForm(instance=ObjectGroup(id=1, object_count=30))
    assert isinstance(object_form.fields["object_count"].widget, widgets.NumberInput)


@pytest.mark.django_db
def test_try_populate_discovery_place_location_find_discovery_place_location():
    discovery_place_location = Location.objects.create(
        label="Location, France", geonames_id=1234
    )

    form = ObjectGroupForm()
    form.data = {
        "discovery_place_location__label": "Location, France",
        "discovery_place_location__geonames_id": 1234,
    }

    form.try_populate_discovery_place_location()

    assert form.data["discovery_place_location"] == discovery_place_location.pk


@pytest.mark.django_db
def test_try_populate_discovery_place_location_create_discovery_place_location():
    label = "Location, France"
    geonames_id = 1234

    form = ObjectGroupForm()

    form.data = {
        "discovery_place_location__label": label,
        "discovery_place_location__geonames_id": geonames_id,
    }

    form.try_populate_discovery_place_location()

    discovery_place_location = Location.objects.get(
        label=label, geonames_id=geonames_id
    )
    assert form.data["discovery_place_location"] == discovery_place_location.pk


@pytest.mark.django_db
def test_try_populate_discovery_place_location_created_with_lat_and_long():
    label = "Location, France"
    geonames_id = 1234
    latitude = 48.8566
    longitude = 2.3522

    form = ObjectGroupForm()

    form.data = {
        "discovery_place_location__label": label,
        "discovery_place_location__geonames_id": geonames_id,
        "discovery_place_location__latitude": latitude,
        "discovery_place_location__longitude": longitude,
    }

    form.try_populate_discovery_place_location()

    assert Location.objects.get(
        label=label, geonames_id=geonames_id, latitude=latitude, longitude=longitude
    )


@pytest.mark.django_db
def test_try_populate_discovery_place_location_updates_lat_and_long():
    label = "Location, France"
    geonames_id = 1234
    latitude = 48.8566
    longitude = 2.3522

    Location.objects.create(label=label, geonames_id=geonames_id)

    form = ObjectGroupForm()

    form.data = {
        "discovery_place_location__label": label,
        "discovery_place_location__geonames_id": geonames_id,
        "discovery_place_location__latitude": latitude,
        "discovery_place_location__longitude": longitude,
    }

    form.try_populate_discovery_place_location()

    assert Location.objects.get(
        label=label, geonames_id=geonames_id, latitude=latitude, longitude=longitude
    )


@pytest.mark.django_db
def test_try_populate_dating_create_period():
    label = "Moyen âge"
    concept_id = 1234

    form = ObjectGroupForm()

    form.data = {
        "dating_period__label": label,
        "dating_period__concept_id": concept_id,
    }

    form.try_populate_dating_models()

    dating_period = Period.objects.get(label=label, concept_id=concept_id)
    assert form.data["dating_period"] == dating_period.pk


@pytest.mark.django_db
def test_try_populate_dating_find_period():
    dating = Period.objects.create(label="Moyen âge", concept_id=1234)

    form = ObjectGroupForm()
    form.data = {
        "dating_period__label": "Moyen âge",
        "dating_period__concept_id": 1234,
    }

    form.try_populate_dating_models()

    assert form.data["dating_period"] == dating.pk


@pytest.mark.django_db
def test_try_populate_dating_find_era():
    dating = Era.objects.create(label="IIe siècle", concept_id=1234)

    form = ObjectGroupForm()
    form.data = {
        "dating_era__label": "IIe siècle",
        "dating_era__concept_id": 1234,
    }

    form.try_populate_dating_models()

    assert form.data["dating_era"] == dating.pk
