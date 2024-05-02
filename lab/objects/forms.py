import enum
import logging
from typing import Any

from django import forms
from django.utils.translation import gettext_lazy as _

from lab.widgets import ChoiceTag, TagsInput

from . import widgets
from .c2rmf import ErosHTTPError, fetch_partial_objectgroup_from_eros
from .models import Location, ObjectGroup, Period

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
        widget=ChoiceTag(),
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
            "discovery_place_location",
            "inventory",
            "collection",
        )
        help_texts = {
            "materials": _(
                "Start typing to search for a material. \
                Click on suggestion or add a comma to add to the list."
            ),
            "discovery_place_location": _("Start typing to search for a location"),
            "dating": _("Start typing to search for a period"),
        }
        widgets = {
            "materials": TagsInput(),
            "discovery_place_location": widgets.LocationAutoCompleteWidget(),
            "dating": widgets.DatingAutoCompleteWidget(),
        }

    def __init__(
        self, *args, instance: ObjectGroup | None = None, **kwargs: dict[str, Any]
    ):
        super().__init__(*args, instance=instance, **kwargs)
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

        if instance:
            self.fields["discovery_place_location"].widget.instance = (
                instance.discovery_place_location
            )
            self.fields["dating"].widget.instance = instance.dating

    def full_clean(self):
        self.try_populate_discovery_place_location()
        self.try_populate_dating()
        return super().full_clean()

    def try_populate_discovery_place_location(self):
        if not self.data.get("discovery_place_location") and self.data.get(
            "discovery_place_location__label"
        ):
            (
                location,
                _,
            ) = Location.objects.get_or_create(
                label=self.data["discovery_place_location__label"],
                geonames_id=self.data.get("discovery_place_location__geonames_id"),
            )
            latitude = self.data.get("discovery_place_location__latitude")
            longitude = self.data.get("discovery_place_location__longitude")
            if (
                latitude
                and longitude
                and not location.latitude
                and not location.longitude
            ):
                location.latitude = float(latitude)
                location.longitude = float(longitude)
                location.save()
            self.data = (
                self.data.copy()
            )  # make a copy of the data because self.data is immutable
            self.data["discovery_place_location"] = location.pk

    def try_populate_dating(self):
        if not self.data.get("dating") and self.data.get("dating__label"):
            period, _ = Period.objects.get_or_create(
                label=self.data["dating__label"],
                theso_joconde_id=self.data.get("dating__theso_joconde_id"),
            )
            self.data = (
                self.data.copy()
            )  # make a copy of the data because self.data is immutable
            self.data["dating"] = period.pk

    def is_multipart(self) -> Any:
        if not self.instance.id:
            # Enables file upload when adding new object group (CSV upload)
            return True
        return super().is_multipart()


class ObjectGroupImportC2RMFForm(forms.ModelForm):
    class Meta:
        model = ObjectGroup
        fields = ("c2rmf_id", "label", "object_count")
        widgets = {
            "object_count": forms.HiddenInput(),
            "c2rmf_id": widgets.ImportFromInput(
                "api:objectgroup-c2rmf-fetch", {"label": "id_label"}
            ),
        }

    def __init__(self, *args, **kwargs: dict[str, Any]):
        super().__init__(*args, **kwargs)
        self.fields["c2rmf_id"].widget.attrs["placeholder"] = "C2RMF00000"
        self.fields["object_count"].initial = 1
        self.fields["label"].disabled = True
        self.fields["label"].required = False

    def _post_clean(self):
        # Skip _post_clean if we already have an existing instance
        if not self.instance.id:
            super()._post_clean()

    def clean(self) -> dict[str, Any]:
        # First, check if objectgroup with this c2rmf id exists.
        instance = ObjectGroup.objects.filter(
            c2rmf_id=self.cleaned_data["c2rmf_id"]
        ).first()
        if instance:
            self.instance = instance
            return self.cleaned_data
        # If it does not exist, then fetch data from Eros
        try:
            eros_data = fetch_partial_objectgroup_from_eros(
                self.cleaned_data["c2rmf_id"]
            )
        except ErosHTTPError as error:
            logger.error(
                "An error occured when importing data from Eros.\nID: %s\nResponse: %s",
                self.cleaned_data["c2rmf_id"],
                error.response,
            )
            raise forms.ValidationError(
                {"c2rmf_id": _("An error occured when importing data from Eros.")}
            )
        if not eros_data:
            raise forms.ValidationError(
                {"c2rmf_id": _("This ID was not found in Eros.")}
            )
        data = {
            **eros_data,
            "object_count": 1,
        }
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
            "discovery_place_location",
            "inventory",
            "collection",
        )
