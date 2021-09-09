from django.db import models
from django.utils.translation import gettext_lazy as _


class Experiment(models.Model):
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

    name = models.CharField(_("Experiment name"), max_length=255, unique=True)

    date = models.DateTimeField(
        _("Experiment date"),
        blank=True,
        help_text=_("Date of the experiment."),
    )

    PROTON_PARTICLE = 1
    ALPHA_PARTICLE = 2
    DEUTON_PARTICLE = 3
    PARTICLES_CHOICES = (
        (PROTON_PARTICLE, _("Proton")),
        (ALPHA_PARTICLE, _("Alpha particle")),
        (DEUTON_PARTICLE, _("Deuton")),
    )
    particle_type = models.IntegerField(
        _("Particle type"),
        choices=PARTICLES_CHOICES,
    )
