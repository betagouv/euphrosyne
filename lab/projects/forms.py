from typing import Any, Protocol

from django import forms
from django.utils.datastructures import MultiValueDict
from django.utils.translation import gettext_lazy as _

from lab.models import Institution
from lab.widgets import CounterTextarea

from . import models, widgets


class PrefixFormProtocol(Protocol):
    prefix: str

    def add_prefix(self, field_name: str) -> str: ...  # noqa: E704

    data: MultiValueDict | Any


class InstitutionFormMixin:
    def try_populate_institution(self: PrefixFormProtocol):
        if not self.data.get(self.add_prefix("institution")) and self.data.get(
            self.add_prefix("institution__name")
        ):
            (
                institution,
                _,
            ) = Institution.objects.get_or_create(
                name=self.data[self.add_prefix("institution__name")],
                country=self.data.get(self.add_prefix("institution__country")),
                ror_id=self.data.get(self.add_prefix("institution__ror_id")),
            )
            self.data = self.data.copy()
            self.data[self.add_prefix("institution")] = institution.pk


class BeamTimeRequestForm(forms.ModelForm):
    class Meta:
        model = models.BeamTimeRequest
        fields = ("request_type", "request_id", "form_type", "problem_statement")
        widgets = {"problem_statement": CounterTextarea()}


class BaseProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ["name", "confidential", "comments"]
        widgets = {"comments": CounterTextarea()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["comments"].max_length = 560
        self.fields["comments"].widget.attrs["maxlength"] = 560
        self.fields["comments"].widget.attrs["placeholder"] = _(
            "Describe your project in a few words (max 560 characters)."
        )

    def clean_comments(self):
        comments = self.cleaned_data.get("comments", "").strip()
        if len(comments) > 560:
            raise forms.ValidationError(
                _("This field must be less than 560 characters.")
            )
        return comments


class MemberProjectForm(BaseProjectForm, InstitutionFormMixin):
    has_accepted_cgu = forms.BooleanField(
        required=True,
        label=_("I have read and accepted the general conditions of Euphrosyne."),
    )
    institution = forms.ModelChoiceField(
        queryset=Institution.objects.all(),
        required=True,
        label=_("Institution"),
        widget=widgets.InstitutionAutoCompleteWidget(),
    )

    employer_first_name = forms.CharField(label=_("First name"), max_length=150)
    employer_last_name = forms.CharField(label=_("Last name"), max_length=150)
    employer_email = forms.EmailField(label=_("Email"), max_length=150)
    employer_function = forms.CharField(label=_("Function"), max_length=150)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            **kwargs,
        )
        self.fields["comments"].required = True

    def full_clean(self):
        self.try_populate_institution()
        return super().full_clean()
