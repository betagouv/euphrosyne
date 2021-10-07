from django.db import models
from django.utils.translation import gettext_lazy as _


class TimestampedModel(models.Model):
    created = models.DateTimeField(
        _("Created"),
        auto_now_add=True,
        help_text=_("Date this entry was first created"),
    )
    modified = models.DateTimeField(
        _("Modified"),
        auto_now=True,
        help_text=_("Date this entry was most recently changed."),
    )

    class Meta:
        abstract = True
