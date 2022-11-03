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


class LowerCharField(models.CharField):
    """Like CharField but format chars to be lowercase before saving
    into DB."""

    def get_prep_value(self, value: str | None):
        if isinstance(value, str):
            return value.lower()
        return value
