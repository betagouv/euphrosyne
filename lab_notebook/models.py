from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _

from lab import models as lab_models


class RunNotebook(models.Model):
    run = models.OneToOneField(
        lab_models.Run,
        on_delete=models.CASCADE,
        related_name="run_notebook",
        verbose_name="Run",
    )

    comments = models.TextField(_("Comments"), blank=True)


@receiver(post_save, sender=lab_models.Run)
def create_favorites(
    sender, instance, created, **kwargs
):  # pylint: disable=unused-argument
    if created:
        RunNotebook.objects.create(run=instance)
