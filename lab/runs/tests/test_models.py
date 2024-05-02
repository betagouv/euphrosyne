import pytest

from ...models import Run


def test_next_action():
    assert Run().status == Run.Status.CREATED
    assert Run(status=Run.Status.CREATED).next_status() == Run.Status.ASK_FOR_EXECUTION
    assert Run(status=Run.Status.ASK_FOR_EXECUTION).next_status() == Run.Status.ONGOING
    assert Run(status=Run.Status.ONGOING).next_status() == Run.Status.FINISHED
    with pytest.raises(AttributeError):
        Run(status=Run.Status.FINISHED).next_status()
