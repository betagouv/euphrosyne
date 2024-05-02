from django import forms
from django.forms.utils import ErrorList
from django.utils.translation import gettext_lazy as _

from lab import widgets

from . import models


class BeamTimeRequestForm(forms.ModelForm):
    class Meta:
        model = models.BeamTimeRequest
        fields = ("request_type", "request_id", "form_type", "problem_statement")
        widgets = {"problem_statement": widgets.CounterTextarea()}


class BaseProjectForm(forms.ModelForm):
    class Meta:
        model = models.Project
        fields = ["name", "confidential"]


class MemberProjectForm(BaseProjectForm):
    has_accepted_cgu = forms.BooleanField(
        required=True,
        label=_("I have read and accepted the general conditions of Euphrosyne."),
    )


class ChangeLeaderForm(forms.Form):
    leader_participation = forms.ModelChoiceField(
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
        self.fields["leader_participation"].queryset = project.participation_set
