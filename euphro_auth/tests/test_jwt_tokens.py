from django.test import TestCase

from lab.tests import factories as lab_factories

from ..jwt import tokens


class TestJWTToken(TestCase):
    def test_refresh_token_for_user(self):
        project = lab_factories.ProjectWithLeaderFactory()
        token = tokens.EuphroRefreshToken.for_user(project.leader.user)
        assert token.payload["user_id"] == project.leader.user.id
        assert token.payload["is_admin"] is False
        assert token.payload["projects"] == [
            {"id": project.id, "slug": project.slug, "name": project.name}
        ]

    def test_api_token_for_euphrosyne(self):
        token = tokens.EuphroToolsAPIToken.for_euphrosyne()
        assert token.payload["user_id"] == "euphrosyne"
        assert token.payload["is_admin"] is True
        assert isinstance(token.payload["projects"], list)
