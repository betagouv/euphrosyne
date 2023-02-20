import enum
from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from lab import widgets

from .models import ObjectGroup


class ObjectGroupAddChoices(enum.Enum):
    SINGLE_OBJECT = "SINGLE_OBJECT", _("One object")
    OBJECT_GROUP = "OBJECT_GROUP", _("Group of objects")

    @classmethod
    def to_choices(cls):
        return (choice.value for choice in cls)


class ObjectGroupForm(forms.ModelForm):
    add_type = forms.ChoiceField(
        label="",
        choices=ObjectGroupAddChoices.to_choices(),
        widget=widgets.ChoiceTag(),
        required=False,
        initial=ObjectGroupAddChoices.SINGLE_OBJECT.value[0],
    )

    class Meta:
        model = ObjectGroup
        fields = (
            "add_type",
            "label",
            "object_count",
            "dating",
            "materials",
            "discovery_place",
            "inventory",
            "collection",
        )
        help_texts = {"materials": _("Separate each material with a comma")}
        widgets = {
            "materials": widgets.TagsInput(),
        }

    def __init__(self, *args, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self.fields["object_count"].initial = 1
        self.fields["add_type"].initial = (
            ObjectGroupAddChoices.OBJECT_GROUP.value[0]
            if self.instance.id and self.instance.object_count > 1
            else ObjectGroupAddChoices.SINGLE_OBJECT.value[0]
        )
        if self.instance.id:
            self.fields["add_type"].widget.attrs["disabled"] = "disabled"

    def is_multipart(self) -> Any:
        if not self.instance.id:
            # Enables file upload when adding new object group (CSV upload)
            return True
        return super().is_multipart()
