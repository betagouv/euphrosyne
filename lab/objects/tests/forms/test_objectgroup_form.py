from django.forms import widgets

from ...forms import ObjectGroupAddChoices, ObjectGroupForm
from ...models import ObjectGroup


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
