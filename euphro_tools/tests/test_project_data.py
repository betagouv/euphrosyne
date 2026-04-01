from unittest import mock

from django.test import TestCase

from euphro_tools.project_data import post_delete_project_source_data


class TestProjectData(TestCase):
    def setUp(self):
        patcher = mock.patch("euphro_tools.project_data.requests.post")
        self.requests_post_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch("euphro_tools.utils._get_euphrosyne_token")
        self.token_mock = patcher.start()
        self.addCleanup(patcher.stop)

        patcher = mock.patch.dict(
            "os.environ",
            {
                "EUPHROSYNE_TOOLS_API_URL": "http://example.com",
            },
        )
        patcher.start()
        self.addCleanup(patcher.stop)

        self.token_mock.return_value = "access"

    def test_post_delete_project_source_data(self):
        post_delete_project_source_data(
            project_slug="project slug",
            storage_role="HOT",
            operation_id="operation-id",
            timeout=10,
        )

        url = self.requests_post_mock.call_args[0][0]
        assert (
            url
            == "http://example.com/data/projects/project%20slug/delete/HOT?operation_id=operation-id"  # pylint: disable=line-too-long
        )
        assert self.requests_post_mock.call_args[1]["timeout"] == 10
        assert self.requests_post_mock.call_args[1]["headers"] == {
            "Authorization": "Bearer access"
        }
