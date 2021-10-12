from django import forms
from django.forms.models import ModelForm

from euphro_auth.models import User
from lab.emails import send_project_invitation_email

from . import models


class ProjectFormForNonAdmins(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ("name",)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ("name", "leader")


class ParticipationWithEmailInvitForm(ModelForm):
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
