from django.db import models
from django.utils.translation import gettext_lazy as _


class DataRequest(models.Model):

    class Meta:
        verbose_name = _("data request")
        verbose_name_plural = _("data requests")

    runs = models.ManyToManyField("lab.Run", related_name="data_requests")

    request_viewed = models.BooleanField(
        _("Viewed"), help_text=_("Has been viewed by an admin"), default=False
    )

    sent_at = models.DateTimeField(_("Sent at"), null=True, blank=True)

    user_email = models.EmailField(_("User email"))
    user_first_name = models.CharField(_("First name"), max_length=150)
    user_last_name = models.CharField(_("Last name"), max_length=150)
    user_institution = models.CharField(_("Institution"), max_length=255, blank=True)

    description = models.TextField(_("Description"), blank=True)

    created = models.DateTimeField(_("Created"), auto_now_add=True)
    modified = models.DateTimeField(_("Modified"), auto_now=True)
