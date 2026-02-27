import enum
import logging
from typing import Any

from django import forms
from django.forms import modelform_factory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from lab.widgets import ChoiceTag, TagsInput

from . import widgets
from .models import (
    Era,
    ExternalObjectReference,
    Location,
    ObjectGroup,
    ObjectGroupThumbnail,
    Period,
)
from .providers import ObjectProviderError, fetch_partial_objectgroup

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
            "dating_era",
            "dating_period",
            "materials",
            "discovery_place_location",
            "inventory",
            "collection",
        )
        help_texts = {
            "materials": _("Start typing to search for a material. \
                Click on suggestion or add a comma to add to the list."),
            "discovery_place_location": _("Start typing to search for a location"),
            "dating_period": _("Start typing to search for a period"),
        }
        widgets = {
            "materials": TagsInput(),
            "discovery_place_location": widgets.LocationAutoCompleteWidget(),
            "dating_period": widgets.PeriodDatingAutoCompleteWidget(),
            "dating_era": widgets.EraDatingAutoCompleteWidget(),
        }

    def __init__(self, *args, instance: ObjectGroup | None = None, **kwargs):
        super().__init__(*args, **kwargs, instance=instance)  # type: ignore[misc]
        if "materials" in self.fields:
            self.fields["materials"].required = False
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
            self.fields["dating_period"].widget.instance = instance.dating_period
            self.fields["dating_era"].widget.instance = instance.dating_era

    def full_clean(self):
        self.try_populate_discovery_place_location()
        self.try_populate_dating_models()
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

    def try_populate_dating_models(self):
        for field_name, theso_model in [("dating_period", Period), ("dating_era", Era)]:
            if not self.data.get(field_name) and self.data.get(f"{field_name}__label"):
                period, _ = theso_model.objects.get_or_create(
                    label=self.data[f"{field_name}__label"],
                    concept_id=self.data.get(f"{field_name}__concept_id"),
                )
                self.data = (
                    self.data.copy()
                )  # make a copy of the data because self.data is immutable
                self.data[field_name] = period.pk

    def is_multipart(self) -> Any:
        if not self.instance.id:
            # Enables file upload when adding new object group (CSV upload)
            return True
        return super().is_multipart()


class ObjectGroupImportBaseForm(forms.ModelForm):
    """Base class providing common functionality for importing object groups
    from external providers.
    Must define:
    provider_name: str - Provider identifier (e.g., 'c2rmf', 'pop')

    """

    provider_name: str

    class Meta:
        model = ExternalObjectReference
        fields = (
            "provider_object_id",
            "label",
        )
        widgets = {
            "label": forms.TextInput(attrs={"readonly": "readonly"}),
        }

    label = forms.CharField(
        label=_("Object label result"),
        max_length=255,
        disabled=True,
        required=False,
        help_text=_("Label fetched from provider database"),
    )

    def __init__(self, *args, **kwargs):
        if (
            not hasattr(self, "provider_name")
            or getattr(self, "provider_name", None) is None
        ):
            raise AttributeError(
                f"{self.__class__.__name__} is missing "
                "required property 'provider_name'"
            )
        super().__init__(*args, **kwargs)
        self.fields["provider_object_id"].widget = widgets.ImportFromInput(
            reverse(
                "api:objectgroup-provider-fetch",
                kwargs={"provider_name": self.provider_name},
            ),
            {"label": "id_label"},
        )
        self.fields["label"].widget.attrs["class"] = (
            self.fields["label"].widget.attrs.get("class", "") + " fr-mb-2w"
        )

    def _post_clean(self):
        # Skip _post_clean if we already have an existing instance
        if not self.instance.id:
            super()._post_clean()

    def clean(self) -> dict[str, Any]:
        """Fetch object data from provider and validate."""
        # Access form attributes (cleaned_data, instance) via self
        cleaned_data = getattr(self, "cleaned_data", {})

        object_id = cleaned_data.get("provider_object_id")

        if not object_id:
            return cleaned_data

        # First, check if objectgroup with this ID exists
        filter_kwargs = {"provider_object_id": object_id}
        instance = ExternalObjectReference.objects.filter(**filter_kwargs).first()
        if instance:
            setattr(self, "instance", instance)
            return cleaned_data

        try:
            provider_data = fetch_partial_objectgroup(
                self.provider_name, cleaned_data["provider_object_id"]
            )
        except ObjectProviderError as error:
            logger.error(
                "An error occurred when importing data from %s.\nID: %s\nError: %s",
                self.provider_name,
                cleaned_data["provider_object_id"],
                error,
            )
            raise forms.ValidationError(
                {
                    "label": "An error occurred when importing data "
                    f"from {self.provider_name.upper()}."
                }
            )

        if not provider_data:
            raise forms.ValidationError(
                {"label": f"This ID was not found in {self.provider_name.upper()}."}
            )

        data = {
            **cleaned_data,
            "object_group": provider_data,
        }
        return data

    def clean_provider_object_id(self):
        return self.cleaned_data["provider_object_id"].upper()

    def save(self, commit=True):
        if not self.instance.id:
            self.instance.provider_name = self.provider_name
            object_group = ObjectGroup.objects.create(
                **self.cleaned_data["object_group"], object_count=1
            )
            if object_group:
                self.instance.object_group = object_group
        return super().save(commit)


def provider_objectimport_form_factory(
    provider_name: str, form: type[forms.ModelForm] | None = None
):

    BaseForm: type[forms.ModelForm] = (  # pylint: disable=invalid-name
        form or ObjectGroupImportBaseForm
    )

    class ProviderImportForm(BaseForm):  # type: ignore
        def __init__(self, *args, **kwargs):
            self.provider_name = provider_name

            super().__init__(*args, **kwargs)

    return modelform_factory(
        ExternalObjectReference,
        ProviderImportForm,
    )


ObjectGroupImportErosForm = provider_objectimport_form_factory("eros")


class _POPImportForm(ObjectGroupImportBaseForm):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["provider_object_id"].help_text = _("POP Reference")
        self.fields["provider_object_id"].widget.attrs["placeholder"] = "50350100588"


ObjectGroupImportPOPForm = provider_objectimport_form_factory(
    "pop", form=_POPImportForm
)


class ObjectGroupImportExternalReadonlyForm(forms.ModelForm):
    class Meta:
        model = ObjectGroup
        fields = (
            "label",
            "object_count",
            "dating_era",
            "dating_period",
            "materials",
            "discovery_place_location",
            "inventory",
            "collection",
        )


class ObjectGroupThumbnailForm(forms.ModelForm):

    class Meta:
        model = ObjectGroupThumbnail
        fields = ("image", "copyright")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["copyright"].required = True
