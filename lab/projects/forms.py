from typing import Any

from django import forms
from django.contrib.auth import get_user_model
from django.db.models.fields.reverse_related import ManyToOneRel
from django.forms.fields import EmailField
from django.forms.models import ModelForm
from django.forms.utils import ErrorList
from django.forms.widgets import HiddenInput, Select
from django.utils.translation import gettext_lazy as _

from euphro_auth.models import User, UserInvitation
from lab.models import Institution
from lab.widgets import CounterTextarea

from ..emails import send_project_invitation_email
from . import models, widgets


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


class MemberProjectForm(BaseProjectForm):
    has_accepted_cgu = forms.BooleanField(
        required=True,
        label=_("I have read and accepted the general conditions of Euphrosyne."),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(
            *args,
            **kwargs,
        )
        self.fields["comments"].required = True


class ChangeLeaderForm(forms.Form):
    leader_participation: forms.ModelChoiceField = forms.ModelChoiceField(
        queryset=None, empty_label=_("No leader"), label=_("Leader")
    )

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        project: models.Project,
        data=None,
        files=None,
        auto_id="id_%s",
        prefix=None,
        initial=None,
        error_class=ErrorList,
        label_suffix=None,
        empty_permitted=False,
        field_order=None,
        use_required_attribute=None,
        renderer=None,
    ) -> None:
        initial = {"leader_participation": project.leader}
        super().__init__(
            data=data,
            files=files,
            auto_id=auto_id,
            prefix=prefix,
            initial=initial,
            error_class=error_class,
            label_suffix=label_suffix,
            empty_permitted=empty_permitted,
            field_order=field_order,
            use_required_attribute=use_required_attribute,
            renderer=renderer,
        )
        self.fields["leader_participation"].queryset = (  # type: ignore
            project.participation_set
        )


class BaseParticipationForm(ModelForm):
    user = EmailField(label=_("User"))

    def __init__(
        self, initial=None, instance: models.Participation | None = None, **kwargs
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
            ) = Institution.objects.get_or_create(
                name=self.data[f"{self.prefix}-institution__name"],
                country=self.data.get(f"{self.prefix}-institution__country"),
                ror_id=self.data.get(f"{self.prefix}-institution__ror_id"),
            )
            self.data[f"{self.prefix}-institution"] = institution.pk

    def clean(self) -> dict[str, Any]:
        cleaned_data = super().clean()
        if cleaned_data and "user" in cleaned_data:
            # Try to find user with email, create it otherwise
            try:
                user = get_user_model().objects.get(email=cleaned_data["user"])
            except get_user_model().DoesNotExist:
                user = UserInvitation.create_user(email=cleaned_data["user"])
            return {**cleaned_data, "user": user}
        return cleaned_data or {}

    def save(self, commit: bool = True) -> models.Participation:
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.fields["user"].label = _("Leader")
        rel: ManyToOneRel = Institution.participation_set.rel  # type: ignore[attr-defined] # pylint: disable=line-too-long
        self.fields["institution"].widget = widgets.InstitutionWidgetWrapper(
            Select(), rel
        )

    def save(self, commit: bool = True) -> models.Participation:
        super().save(commit=False)
        self.instance.is_leader = True
        self.instance.save()
        self._save_m2m()  # type: ignore[attr-defined]
        return self.instance
