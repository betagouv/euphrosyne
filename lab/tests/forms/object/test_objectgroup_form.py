from unittest.mock import MagicMock

from ....forms import ObjectGroupAddChoices, ObjectGroupForm
from ....models import ObjectGroup


def test_empty_label_group_for_object_group_raise_validation():
    form = ObjectGroupForm(
        data={
            "add_type": ObjectGroupAddChoices.OBJECT_GROUP.value[0],
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        }
    )
    assert form.has_error("label", code="label-required-for-mulitple-objects")


def test_empty_label_group_for_single_object_is_allowed():
    form = ObjectGroupForm(
        data={
            "add_type": ObjectGroupAddChoices.SINGLE_OBJECT.value[0],
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        }
    )
    assert not form.has_error("label", code="label-required-for-mulitple-objectss")


def test_update_object_disables_add_type_field():
    instance = MagicMock(side_effect=ObjectGroup(id=1))
    instance.object_set.count.return_value = 1

    form = ObjectGroupForm(
        data={
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        },
        instance=instance,
    )
    assert not form.fields["add_type"].required
    assert form.fields["add_type"].widget.attrs["disabled"]
    assert not form.has_error("add_type")


def test_update_object_set_add_type_depending_on_object_count():
    single_object_instance = MagicMock(side_effect=ObjectGroup(id=1))
    single_object_instance.object_set.count.return_value = 1
    multi_object_instance = MagicMock(side_effect=ObjectGroup(id=2))
    multi_object_instance.object_set.count.return_value = 3

    single_object_form = ObjectGroupForm(
        data={
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        },
        instance=single_object_instance,
    )
    multi_object_form = ObjectGroupForm(
        data={
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        },
        instance=multi_object_instance,
    )
    assert (
        single_object_form.fields["add_type"].initial
        == ObjectGroupAddChoices.SINGLE_OBJECT.value[0]
    )
    assert (
        multi_object_form.fields["add_type"].initial
        == ObjectGroupAddChoices.OBJECT_GROUP.value[0]
    )
