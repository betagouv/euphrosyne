from django.contrib.postgres.fields import ArrayField
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


class ObjectGroup(TimestampedModel):
    c2rmf_id = models.CharField(
        _("C2RMF ID"),
        max_length=255,
        null=True,
        unique=True,
    )
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
