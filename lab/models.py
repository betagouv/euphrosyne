from django.db import models
from django.utils.translation import ugettext_lazy as _, ugettext


class Experiement(models.Model):
    OPEN_STATUS = 1
    CLOSED_STATUS = 2
    STATUS_CHOICES = (
        (OPEN_STATUS, _("Open")),
        (CLOSED_STATUS, _("Closed")),
    )
    status = models.IntegerField(
        _("Status"),
        choices=STATUS_CHOICES,
        default=OPEN_STATUS,
    )

    created = models.DateTimeField(
        _("Created"),
        blank=True,
        help_text=_("Date this ticket was first created"),
    )
    modified = models.DateTimeField(
        _("Modified"),
        blank=True,
        help_text=_("Date this ticket was most recently changed."),
    )
