import pytest

from ...participations.models import Institution
from ...widgets import AutoCompleteWidget


def test_context_when_instance_is_none():
    widget = AutoCompleteWidget()
    context = widget.get_context("name", None, {"attrs": "attrs"})
    assert context["widget"]["instance"] is None


def test_context_when_instance_is_not_none():
    institution = Institution()
    widget = AutoCompleteWidget()
    widget.instance = institution
    context = widget.get_context("name", None, {"attrs": "attrs"})
    assert context["widget"]["instance"] == institution


@pytest.mark.django_db
def test_context_when_value():
    institution = Institution.objects.create(name="I", country="france")
    widget = AutoCompleteWidget()
    widget.model = Institution
    context = widget.get_context("name", institution.pk, {"attrs": "attrs"})
    assert context["widget"]["instance"] == institution
