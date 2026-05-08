from django import forms
from django.utils.translation import gettext_lazy as _

from .models import Employer


class EmployerCompletionForm(forms.ModelForm):
    class Meta:
        model = Employer
        fields = ("email", "first_name", "last_name", "function")
        labels = {
            "email": _("Email"),
            "first_name": _("First name"),
            "last_name": _("Last name"),
            "function": _("Function"),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "fr-input"
