from django.db import models
from django.forms import ValidationError
from django.utils.translation import gettext_lazy as _
from lab.measuring_points.models import MeasuringPoint


class Standard(models.Model):
    label = models.CharField(_("Label"), max_length=255)

    class Meta:
        verbose_name = _("standard")
        verbose_name_plural = _("standards")
        constraints = [
            models.UniqueConstraint(fields=["label"], name="unique_standard_label")
        ]


class MeasuringPointStandard(models.Model):
    standard = models.ForeignKey(
        Standard,
        on_delete=models.PROTECT,
        related_name="measuring_points",
    )
    measuring_point = models.OneToOneField(
        MeasuringPoint,
        on_delete=models.PROTECT,
        related_name="standard",
    )

    class Meta:
        verbose_name = _("measuring point standard")
        verbose_name_plural = _("measuring point standards")
        constraints = [
            models.UniqueConstraint(
                fields=["standard", "measuring_point"],
                name="unique_measuring_point_standard",
            )
        ]

    def clean(self):
        if self.measuring_point.object_group:
            raise ValidationError(
                _("Standard measuring point must not belong to an object group.")
            )
