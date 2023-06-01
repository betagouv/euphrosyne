import enum
import logging
from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from lab import widgets

from .c2rmf import ErosHTTPError, fetch_partial_objectgroup_from_eros
from .models import ObjectGroup

logger = logging.getLogger(__name__)


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
        # Default fields but can be overridden in admin view.
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

    def __init__(self, *args, **kwargs: dict[str, Any]):
        super().__init__(*args, **kwargs)
        # We must check if attribute is in self.fields because it can be removed
        # in admin view when page is readlonly.
        if "dating" in self.fields:
            self.fields["dating"].required = True
        # Set object count initial value
        if "object_count" in self.fields:
            self.fields["object_count"].initial = 1
        # Set add type initial value
        if "add_type" in self.fields:
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


class ObjectGroupImportC2RMFForm(forms.ModelForm):
    class Meta:
        model = ObjectGroup
        fields = ("c2rmf_id",)

    def __init__(self, *args, **kwargs: dict[str, Any]) -> None:
        super().__init__(*args, **kwargs)
        self.fields["c2rmf_id"].widget.attrs["placeholder"] = "C2RMF00000"

    def full_clean(self):
        super().full_clean()
        self.instance.object_count = 1
        self.instance.label = self.cleaned_data["label"]

    def clean(self) -> dict[str, Any]:
        # Disable unique check
        try:
            data = fetch_partial_objectgroup_from_eros(self.cleaned_data["c2rmf_id"])
        except ErosHTTPError as error:
            logger.error(
                "An error occured when importing data from Eros.\nID: %s\nResponse: %s",
                self.cleaned_data["c2rmf_id"],
                error.response,
            )
            raise forms.ValidationError(
                {"c2rmf_id": _("An error occured when importing data from Eros.")}
            )
        if not data:
            raise forms.ValidationError(
                {"c2rmf_id": _("This ID was not found in Eros.")}
            )
        return data


class ObjectGroupImportC2RMFReadonlyForm(forms.ModelForm):
    class Meta:
        model = ObjectGroup
        fields = (
            "c2rmf_id",
            "label",
            "object_count",
            "dating",
            "materials",
            "discovery_place",
            "inventory",
            "collection",
        )
