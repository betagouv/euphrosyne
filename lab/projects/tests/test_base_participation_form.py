import pytest

from lab.models import Institution
from lab.tests.factories import ParticipationFactory
from lab.widgets import InstitutionAutoCompleteWidget

from ..forms import BaseParticipationForm


@pytest.mark.django_db
def test_form_institution_widget_instance_when_editing():
    participation = ParticipationFactory()

    form = BaseParticipationForm(instance=participation)

    assert isinstance(form.fields["institution"].widget, InstitutionAutoCompleteWidget)
    assert form.fields["institution"].widget.instance == participation.institution


def test_form_institution_widget_instance_when_creating():
    form = BaseParticipationForm()

    assert isinstance(form.fields["institution"].widget, InstitutionAutoCompleteWidget)
    assert form.fields["institution"].widget.instance is None


@pytest.mark.django_db
def test_try_populate_institution_find_institution():
    institution = Institution.objects.create(
        name="institution", country="france", ror_id="test"
    )

    form = BaseParticipationForm()
    form.prefix = prefix = "inst"
    form.data = {
        f"{prefix}-institution__name": "institution",
        f"{prefix}-institution__country": "france",
        f"{prefix}-institution__ror_id": "test",
    }

    form.try_populate_institution()

    assert form.data[f"{prefix}-institution"] == institution.pk


@pytest.mark.django_db
def test_try_populate_institution_create_institution():
    name = "some_institution"
    country = "azerty"
    ror_id = "test"

    form = BaseParticipationForm()
    form.prefix = prefix = "inst"

    form.data = {
        f"{prefix}-institution__name": name,
        f"{prefix}-institution__country": country,
        f"{prefix}-institution__ror_id": ror_id,
    }

    form.try_populate_institution()

    institution = Institution.objects.get(name=name, country=country, ror_id=ror_id)
    assert form.data[f"{prefix}-institution"] == institution.pk
