from django import forms
from django.utils.translation import gettext_lazy as _


class MFACodeForm(forms.Form):
    code = forms.CharField(
        label=_("Authentication code"),
        max_length=32,
        strip=True,
        widget=forms.TextInput(
            attrs={
                "autocomplete": "one-time-code",
                "autofocus": True,
                "class": "fr-input",
                "spellcheck": "false",
                "autocapitalize": "off",
            }
        ),
    )
