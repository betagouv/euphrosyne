from django import forms
from django.forms.models import ModelForm
from django.forms.widgets import HiddenInput, Select
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User
from lab.emails import send_project_invitation_email

from . import models, widgets


class BaseParticipationForm(ModelForm):
    def save(self, commit: bool = ...) -> models.Participation:
        is_new = self.instance.pk is None
        instance = super().save(commit=commit)
        if is_new:
            user: User = instance.user
            send_project_invitation_email(
                email=user.email,
                project=instance.project,
            )
        return instance

    class Meta:
        model = models.Participation
        fields = ("user",)
        widgets = {
            "user": widgets.UserWidgetWrapper(
                Select(),
                User.participation_set.rel,
            ),
        }


class LeaderParticipationForm(BaseParticipationForm):
    """Participation model form that automatically set `is_leader` to
    `True` when saving the instance.
    """

    is_leader = forms.BooleanField(widget=HiddenInput(), initial=True)

    class Meta:
        model = models.Participation
        fields = ("user",)
        widgets = {
            "user": widgets.UserWidgetWrapper(
                Select(),
                User.participation_set.rel,
            ),
        }
        labels = {
            "user": _("Leader"),
        }

    def save(self, commit: bool = ...) -> models.Participation:
        self.instance.is_leader = True
        return super().save(commit=commit)
