import pytest
from rest_framework_simplejwt.exceptions import AuthenticationFailed

from ...tests import factories
from ..authentication import EuphrosyneAdminJWTAuthentication
from ..tokens import EuphroToolsAPIToken


@pytest.mark.django_db
def test_euphrosyne_admin_jwt_authentication():
    auth = EuphrosyneAdminJWTAuthentication()

    assert auth.get_user(EuphroToolsAPIToken.for_euphrosyne())

    with pytest.raises(AuthenticationFailed):
        auth.get_user(EuphroToolsAPIToken.for_user(factories.StaffUserFactory()))
