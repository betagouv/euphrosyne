import pytest

from ...models import Run
from ...tests import factories


def test_next_action():
    assert Run().status == Run.Status.CREATED
    assert Run(status=Run.Status.CREATED).next_status() == Run.Status.ASK_FOR_EXECUTION
    assert Run(status=Run.Status.ASK_FOR_EXECUTION).next_status() == Run.Status.ONGOING
    assert Run(status=Run.Status.ONGOING).next_status() == Run.Status.FINISHED
    with pytest.raises(AttributeError):
        Run(status=Run.Status.FINISHED).next_status()


@pytest.mark.django_db
def test_not_embargoed_qs():
    factories.RunFactory()  # create embargoed run
    not_embargoed_run = factories.NotEmbargoedRun()

    qs = Run.objects.only_not_embargoed()
    assert qs.count() == 1
    assert qs.first() == not_embargoed_run
