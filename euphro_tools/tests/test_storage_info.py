from unittest import mock

import pytest

from euphro_tools.download_urls import get_storage_info_for_project_images
from euphro_tools.exceptions import EuphroToolsException


@pytest.fixture(autouse=True)
def tools_token():
    with mock.patch(
        "euphro_tools.utils._get_euphrosyne_token", return_value="test-jwt"
    ):
        yield


@mock.patch("shared.http.requests.get")
def test_storage_info_uses_configured_tools_origin_without_redirects(mock_get):
    data = {"base_url": "https://account.blob.core.windows.net", "token": "test-sas"}
    response = mock.Mock(status_code=200)
    response.json.return_value = data
    mock_get.return_value = response
    assert get_storage_info_for_project_images("project") == data
    mock_get.assert_called_once_with(
        "https://tools/images/projects/project/signed-url",
        timeout=5,
        headers={"Authorization": "Bearer test-jwt"},
        allow_redirects=False,
    )
    response.close.assert_called_once()


@mock.patch("shared.http.requests.get")
def test_storage_info_encodes_project_slug_as_one_path_segment(mock_get):
    response = mock.Mock(status_code=200)
    response.json.return_value = {"base_url": "https://storage", "token": "test-sas"}
    mock_get.return_value = response
    get_storage_info_for_project_images("project/other?query=value#fragment")
    assert mock_get.call_args.args[0] == (
        "https://tools/images/projects/"
        "project%2Fother%3Fquery%3Dvalue%23fragment/signed-url"
    )


@pytest.mark.parametrize("status", [301, 302, 303, 307, 308])
@mock.patch("shared.http.requests.get")
def test_storage_info_does_not_redirect_tools_credentials(mock_get, status):
    response = mock.Mock(
        status_code=status, headers={"Location": "http://169.254.169.254/"}
    )
    mock_get.return_value = response
    with pytest.raises(EuphroToolsException):
        get_storage_info_for_project_images("project")
    assert mock_get.call_count == 1
    assert mock_get.call_args.kwargs["allow_redirects"] is False
    response.json.assert_not_called()
    response.close.assert_called_once()


@pytest.mark.parametrize(
    "data",
    [None, [], {}, {"base_url": "https://storage"}, {"base_url": 3, "token": "test"}],
)
@mock.patch("shared.http.requests.get")
def test_storage_info_rejects_malformed_response(mock_get, data):
    response = mock.Mock(status_code=200)
    response.json.return_value = data
    mock_get.return_value = response
    with pytest.raises(EuphroToolsException):
        get_storage_info_for_project_images("project")
    response.close.assert_called_once()


@mock.patch("shared.http.requests.get")
def test_storage_info_rejects_invalid_json_without_disclosing_response(mock_get):
    response = mock.Mock(status_code=200)
    response.json.side_effect = ValueError("private-test-token")
    mock_get.return_value = response
    with pytest.raises(EuphroToolsException) as exc:
        get_storage_info_for_project_images("project")
    assert "private-test-token" not in str(exc.value)
    assert exc.value.__suppress_context__
    response.close.assert_called_once()
