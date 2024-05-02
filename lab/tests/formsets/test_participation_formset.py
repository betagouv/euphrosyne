from unittest import mock

from django.contrib.auth import get_user_model
from django.forms.models import inlineformset_factory
from django.test.testcases import TestCase

from lab.forms import BaseParticipationForm
from lab.models import Participation, Project
from lab.projects.admin import ParticipationFormSet


class TestParticipationFormSet(TestCase):
    def setUp(self):
        project = Project.objects.create(name="Projet Test")
        project.participation_set.create(
            user=get_user_model().objects.create(
                email="member@test.test",
            ),
            is_leader=False,
        )
        project.participation_set.create(
            user=get_user_model().objects.create(
                email="leader@test.test",
            ),
            is_leader=True,
        )
        formset_class = inlineformset_factory(
            Project,
            Participation,
            form=BaseParticipationForm,
            extra=0,
            min_num=1,
            # On creation, only leader participation can be added
            max_num=1000,
            can_delete=True,
            formset=ParticipationFormSet,
        )
        self.formset = formset_class(
            instance=project, queryset=project.participation_set.all()
        )

    def test_leader_participation_delete_field_is_disabled(self):
        for form in self.formset:
            if form.instance.is_leader:
                assert form.fields["DELETE"].disabled
            else:
                assert not form.fields["DELETE"].disabled

    def test_qs_is_ordered_by_is_leader(self):
        assert self.formset.get_queryset().query.order_by[0] == "-is_leader"

    @mock.patch.object(BaseParticipationForm, "try_populate_institution")
    def test_call_try_populate_institution_on_full_clean(
        self, mock_method: mock.MagicMock
    ):
        self.formset.full_clean()
        mock_method.assert_called()
