import pytest

from lab.models import Institution

from ...forms import BaseParticipationForm
from ...widgets import InstitutionAutoCompleteWidget


@pytest.mark.django_db
def test_form_institution_widget_choices():
    Institution.objects.create(name="I2", country="france")
    Institution.objects.create(name="I1", country="spain")

    form = BaseParticipationForm()

    assert isinstance(form.fields["institution"].widget, InstitutionAutoCompleteWidget)

    choices = list(form.fields["institution"].widget.choices)
    assert len(choices) == 3
    assert choices[0] == ("", "---------")
    assert choices[1][1] == ("i2, france")
    assert choices[2][1] == ("i1, spain")


@pytest.mark.django_db
def test_try_populate_institution_find_institution():
    institution = Institution.objects.create(name="institution", country="france")

    form = BaseParticipationForm()
    form.prefix = prefix = "inst"
    form.data = {
        f"{prefix}-institution__name": "institution",
        f"{prefix}-institution__country": "france",
    }

    form.try_populate_institution()

    assert form.data[f"{prefix}-institution"] == institution.pk


@pytest.mark.django_db
def test_try_populate_institution_create_institution():
    name = "some_institution"
    country = "azerty"

    form = BaseParticipationForm()
    form.prefix = prefix = "inst"

    form.data = {
        f"{prefix}-institution__name": name,
        f"{prefix}-institution__country": country,
    }

    form.try_populate_institution()

    institution = Institution.objects.get(name=name, country=country)
    assert form.data[f"{prefix}-institution"] == institution.pk
