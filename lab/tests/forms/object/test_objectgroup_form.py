from lab.models.run import ObjectGroup

from ....forms import ObjectGroupAddChoices, ObjectGroupForm


def test_empty_label_group_for_object_group_raise_validation():
    form = ObjectGroupForm(
        data={
            "add_type": ObjectGroupAddChoices.OBJECT_GROUP.value[0],
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        }
    )
    form.full_clean()
    assert form.has_error("label")


def test_empty_label_group_for_single_object_is_allowed():
    form = ObjectGroupForm(
        data={
            "add_type": ObjectGroupAddChoices.SINGLE_OBJECT.value[0],
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        }
    )
    form.full_clean()
    assert not form.has_error("label")


def test_update_object_has_disabled_add_type_field():
    form = ObjectGroupForm(
        data={
            "add_type": ObjectGroupAddChoices.SINGLE_OBJECT.value[0],
            "label": "",
            "materials": "wood,stone",
            "dating": "XIXe",
        },
        instance=ObjectGroup(id=1),
    )
    assert form.fields["add_type"].disabled
