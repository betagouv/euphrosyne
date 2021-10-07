from django import forms

from . import models


class ProjectFormForNonAdmins(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ("name",)


class ProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ("name", "leader")
