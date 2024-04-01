import pytest

from ...models.participation import Institution
from ...widgets import InstitutionAutoCompleteWidget


def test_context_when_instance_is_none():
    widget = InstitutionAutoCompleteWidget()
    context = widget.get_context("name", None, {"attrs": "attrs"})
    assert context["widget"]["instance"] is None


def test_context_when_instance_is_not_none():
    institution = Institution()
    widget = InstitutionAutoCompleteWidget()
    widget.instance = institution
    context = widget.get_context("name", None, {"attrs": "attrs"})
    assert context["widget"]["instance"] == institution


@pytest.mark.django_db
def test_context_when_value():
    institution = Institution.objects.create(name="I", country="france")
    widget = InstitutionAutoCompleteWidget()
    context = widget.get_context("name", institution.pk, {"attrs": "attrs"})
    assert context["widget"]["instance"] == institution
