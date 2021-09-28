from django.db import models
from django.utils.translation import gettext_lazy as _
from euphro_auth.models import User

from shared.model_mixins import TimestampedModelMixin


class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    first_name = models.CharField(_("first name"), max_length=150)
    last_name = models.CharField(_("last name"), max_length=150)
    profession = models.CharField(
        _("profession"), max_length=150, null=True, blank=True
    )


class UserInvitation(TimestampedModelMixin):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)
