from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from shared.models import TimestampedModel


class Run(TimestampedModel):
    label = models.CharField(_("Run label"), max_length=255, unique=True)
    date = models.DateTimeField(
        _("Run date"),
        blank=True,
    )
    project = models.ForeignKey("lab.Project", null=False, on_delete=models.PROTECT)

    def __str__(self):
        return f"Run {self.label} on {self.date}"


class Project(TimestampedModel):
    """A project is a collection of runs done by the same team"""

    name = models.CharField(_("Project name"), max_length=255, unique=True)
    # Caveat: we might want to allow CASCADE in on_delete. But we might want
    # also to add a pre_delete signal handler to abort deletion (or fallback to
    # a default project leader?) in case the Project is not finished (depending
    # if the Runs are all finished or not).
    leader = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        on_delete=models.PROTECT,
        related_name="projects_as_leader",
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="lab.Participation"
    )

    def __str__(self):
        return f"{self.name}"


class Participation(TimestampedModel):
    """JOIN table between User and Project

    A user who participates in a project is a project member (possibly leader).
    """

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    project = models.ForeignKey("lab.Project", on_delete=models.PROTECT)

    def __str__(self):
        return f"{self.user} participation in {self.project}"
