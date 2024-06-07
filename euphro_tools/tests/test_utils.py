from ..utils import _get_project_path, _get_run_path, get_run_data_path


def test_get_project_path():
    assert _get_project_path("test-project") == "projects/test-project"


def test_get_run_path():
    assert (
        _get_run_path("test-project", "test-run")
        == "projects/test-project/runs/test-run"
    )


def test_get_run_data_path():
    assert (
        get_run_data_path("test-project", "test-run", "raw_data")
        == "projects/test-project/runs/test-run/raw_data"
    )
    assert (
        get_run_data_path("test-project", "test-run", "processed_data")
        == "projects/test-project/runs/test-run/processed_data"
    )
