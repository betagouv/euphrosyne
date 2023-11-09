from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel


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
    dating = models.CharField(
        _("Dating"),
        max_length=255,
        blank=True,
    )
    materials = ArrayField(
        models.CharField(max_length=255),
        verbose_name=_("Materials"),
        default=list,
    )
    discovery_place = models.CharField(
        _("Place of discovery"),
        max_length=255,
        blank=True,
    )
    collection = models.CharField(
        _("Collection"),
        max_length=255,
        blank=True,
    )

    def __str__(self) -> str:
        label = self.label
        if self.object_count > 1:
            count_str = _("%(object_count)s objects") % {
                "object_count": self.object_count
            }
            label = "({}) {}".format(count_str, label)
        materials = ", ".join(self.materials)

        return f"{label} - {self.dating} - {materials}"

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
