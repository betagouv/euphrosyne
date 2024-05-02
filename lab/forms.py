from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.forms.fields import EmailField
from django.forms.models import ModelForm
from django.forms.widgets import HiddenInput, Select
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User, UserInvitation

from . import models, widgets
from .emails import send_project_invitation_email


class BaseParticipationForm(ModelForm):
    user = EmailField(label=_("User"))

    def __init__(
        self, initial=None, instance: models.Participation = None, **kwargs
    ) -> None:
        if instance:
            initial = {**(initial or {}), "user": instance.user.email}
        super().__init__(initial=initial, instance=instance, **kwargs)
        self.fields["user"].widget.attrs["placeholder"] = _("Email")
        if instance:
            self.fields["institution"].widget.instance = instance.institution

    def try_populate_institution(self):
        if not self.data.get(f"{self.prefix}-institution") and self.data.get(
            f"{self.prefix}-institution__name"
        ):
            (
                institution,
                _,
            ) = models.Institution.objects.get_or_create(
                name=self.data[f"{self.prefix}-institution__name"],
                country=self.data.get(f"{self.prefix}-institution__country"),
                ror_id=self.data.get(f"{self.prefix}-institution__ror_id"),
            )
            self.data[f"{self.prefix}-institution"] = institution.pk

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if "user" in cleaned_data:
            # Try to find user with email, create it otherwise
            try:
                user = get_user_model().objects.get(email=cleaned_data["user"])
            except get_user_model().DoesNotExist:
                user = UserInvitation.create_user(email=cleaned_data["user"])
            return {**cleaned_data, "user": user}
        return cleaned_data

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
        fields = ("user", "institution")
        widgets = {"institution": widgets.InstitutionAutoCompleteWidget()}
        labels = {"institution": _("Institution")}


class LeaderParticipationForm(BaseParticipationForm):
    """Participation model form that automatically set `is_leader` to
    `True` when saving the instance.
    """

    is_leader = forms.BooleanField(widget=HiddenInput(), initial=True)

    class Meta:
        model = models.Participation
        fields = ("user", "institution")
        widgets = {
            "institution": widgets.InstitutionWidgetWrapper(
                Select(), models.Institution.participation_set.rel
            ),
        }

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.fields["user"].label = _("Leader")

    def save(self, commit: bool = ...) -> models.Participation:
        super().save(commit=False)
        self.instance.is_leader = True
        self.instance.save()
        self._save_m2m()
