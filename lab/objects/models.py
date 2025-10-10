from django.contrib.postgres.fields import ArrayField
from django.core.files.storage import storages
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

from ..thesauri.models import Era, Period


class Location(models.Model):
    label = models.CharField(_("Name"), max_length=255)
    latitude = models.FloatField(_("Latitude"), blank=True, null=True)
    longitude = models.FloatField(_("Longitude"), blank=True, null=True)

    geonames_id = models.IntegerField("Geonames ID", blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["label"], name="unique_label"),
            models.UniqueConstraint(
                fields=["latitude", "longitude"], name="unique_lat_long"
            ),
            models.UniqueConstraint(fields=["geonames_id"], name="unique_geonames_id"),
        ]

    def __str__(self) -> str:
        return str(self.label)


def get_thumbnail_path(instance: "ObjectGroupThumbnail", *args):
    return f"ogs/thumbnails/{instance.object_group_id}/thumbnail"


def get_thumbnail_storage():  # prevent migration credentials leak
    return storages["objectstorage"]


class ObjectGroupThumbnail(models.Model):
    object_group = models.OneToOneField(
        "lab.ObjectGroup",
        on_delete=models.CASCADE,
        related_name="thumbnail",
    )
    image = models.ImageField(
        storage=get_thumbnail_storage,
        verbose_name=_("Image"),
        upload_to=get_thumbnail_path,
    )
    copyright = models.CharField(
        _("Copyright"),
        max_length=255,
        blank=True,
    )


class ObjectGroup(TimestampedModel):
    label = models.CharField(
        _("Label"),
        max_length=255,
    )
    object_count = models.PositiveIntegerField(
        _("Number of objects"),
    )
    inventory = models.CharField(
        _("Inventory number"),
        max_length=255,
        blank=True,
    )
    dating_period = models.ForeignKey(
        Period,
        on_delete=models.SET_NULL,
        verbose_name=_("Period"),
        blank=True,
        null=True,
    )
    dating_era = models.ForeignKey(
        Era,
        on_delete=models.SET_NULL,
        verbose_name=_("Era"),
        blank=True,
        null=True,
    )
    materials = ArrayField(
        models.CharField(max_length=255),
        verbose_name=_("Materials"),
        default=list,
    )
    discovery_place_location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        verbose_name=_("Place of discovery"),
        blank=True,
        null=True,
    )
    collection = models.CharField(
        _("Collection"),
        max_length=255,
        blank=True,
    )
    external_reference: "ExternalObjectReference"

    @property
    def discovery_place(self) -> str:
        if not self.discovery_place_location:
            return ""
        return self.discovery_place_location.label

    def __str__(self) -> str:
        label = self.label
        if self.object_count > 1:
            count_str = _("%(object_count)s objects") % {
                "object_count": self.object_count
            }
            label = "({}) {}".format(count_str, label)
        if self.materials:
            materials = ", ".join(self.materials)
            label = f"{label} - {materials}"
        return label

    class Meta:
        verbose_name = _("Object / Sample")
        verbose_name_plural = _("Object(s) / Sample(s")

    @property
    def c2rmf_id(self) -> str | None:
        # DEPRECATED. This is kept for backward compatibility but should
        # not be used in new code. Use is_from_provider("eros") and
        # external_reference.provider_object_id instead.
        if hasattr(self, "external_reference") and self.external_reference:
            if self.external_reference.provider_name == "eros":
                return self.external_reference.provider_object_id
        return None

    @property
    def is_external(self) -> bool:
        return (
            hasattr(self, "external_reference") and self.external_reference is not None
        )

    def is_from_provider(self, provider_name: str) -> bool:
        return (
            self.is_external and self.external_reference.provider_name == provider_name
        )


class Object(models.Model):
    group = models.ForeignKey(ObjectGroup, on_delete=models.CASCADE)
    label = models.CharField(_("Label"), max_length=255)
    inventory = models.CharField(
        _("Inventory"),
        max_length=255,
        blank=True,
    )
    collection = models.CharField(
        _("Collection"),
        max_length=255,
        blank=True,
    )


class ExternalObjectReference(TimestampedModel):
    """Links an ObjectGroup to an external provider's object data."""

    object_group = models.OneToOneField(
        ObjectGroup,
        on_delete=models.CASCADE,
        related_name="external_reference",
        verbose_name=_("Object Group"),
    )
    provider_name = models.CharField(
        _("Provider Name"),
        max_length=50,
        help_text=_("Provider identifier (e.g., 'eros', 'pop')"),
    )
    provider_object_id = models.CharField(
        _("Provider Object ID"),
        max_length=255,
        help_text=_("Unique identifier in the provider's system"),
    )

    class Meta:
        verbose_name = _("External Object Reference")
        verbose_name_plural = _("External Object References")
        constraints = [
            models.UniqueConstraint(
                fields=["provider_name", "provider_object_id"],
                name="unique_provider_object",
            )
        ]

    def __str__(self) -> str:
        return f"{self.provider_name} - {self.provider_object_id}"


class RunObjectGroup(TimestampedModel):
    """Many to many ObjectGroup - Run JOIN model"""

    objectgroup = models.ForeignKey(ObjectGroup, on_delete=models.CASCADE)
    run = models.ForeignKey("lab.Run", on_delete=models.CASCADE)


class RunObjetGroupImage(TimestampedModel):
    run_object_group = models.ForeignKey(
        RunObjectGroup, on_delete=models.CASCADE, related_name="images"
    )

    path = models.CharField(max_length=256, verbose_name=_("Path"))
    transform = models.JSONField(verbose_name=_("Image transformation"), null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["path", "transform", "run_object_group"],
                name="run_object_group_image_unique_path_transform_perrun_object_group",
            ),
        ]

    @property
    def file_name(self) -> str:
        if (
            self.path.startswith("C2RMF")
            or self.path.startswith("FZ")
            or self.path.startswith("F")
        ) and len(self.path.split("/")) == 2:
            image_id = self.path.split("/")[1]
            return f"{image_id}.tiff"
        return self.path.rsplit("/", maxsplit=1)[-1].split("?")[0]


def construct_image_url_from_path(
    path: str, storage_base_url: str, storage_token: str | None = None
) -> str:
    # pylint: disable=import-outside-toplevel
    from .providers import construct_image_url

    if (
        path.startswith("C2RMF") or path.startswith("FZ") or path.startswith("F")
    ) and len(path.split("/")) == 2:
        return construct_image_url("eros", path)

    return (
        f"{storage_base_url}{path}?{storage_token}"
        if storage_token
        else f"{storage_base_url}{path}"
    )
