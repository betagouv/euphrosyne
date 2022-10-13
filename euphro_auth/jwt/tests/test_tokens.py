from ..tokens import EuphroToolsAPIToken


def test_euphrotools_api_token():
    assert (
        EuphroToolsAPIToken.for_euphrosyne().access_token.payload["user_id"]
        == "euphrosyne"
    )
