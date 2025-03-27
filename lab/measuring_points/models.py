from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel

from ..objects.models import ObjectGroup, RunObjetGroupImage
from ..runs.models import Run


class MeasuringPoint(TimestampedModel):
    name = models.CharField(_("Name"), max_length=255)

    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE,
        related_name="measuring_points",
        verbose_name=_("Run"),
    )

    object_group = models.ForeignKey(
        ObjectGroup,
        on_delete=models.SET_NULL,
        related_name="measuring_points",
        verbose_name=_("Object group"),
        null=True,
    )

    comments = models.TextField(_("Comments"), blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["name", "run"], name="unique_name_per_run"),
        ]

    @property
    def is_meaningful(self) -> bool:
        """
        Check if the measuring point has meaningful data.

        A measuring point is considered meaningful if it has at least one of:
        - Comments
        - Associated object group
        - Associated standard

        Returns:
            bool: True if the measuring point has meaningful data, False otherwise
        """
        if self.comments.strip():
            return True

        if self.object_group is not None:
            return True

        try:
            if self.standard:
                return True
        except (AttributeError, ObjectDoesNotExist):
            pass

        return False


class MeasuringPointImage(TimestampedModel):
    measuring_point = models.OneToOneField(
        MeasuringPoint, on_delete=models.CASCADE, related_name="image"
    )
    run_object_group_image = models.ForeignKey(
        RunObjetGroupImage,
        on_delete=models.CASCADE,
        related_name="measuring_point_images",
    )

    # Store point location on image
    # like width, height, x, y properties
    point_location = models.JSONField(
        verbose_name=_("Point location of image"), null=True
    )
