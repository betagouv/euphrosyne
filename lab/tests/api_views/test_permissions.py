from unittest.mock import MagicMock, patch

from lab.api_views.permissions import IsLabAdminUser


@patch("lab.api_views.permissions.is_lab_admin")
def test_is_lad_admin_permission(is_lab_admin_fn_mock: MagicMock):
    is_lab_admin_fn_mock.return_value = False
    assert not IsLabAdminUser().has_permission(request=MagicMock(), view=MagicMock())
    is_lab_admin_fn_mock.return_value = True
    assert IsLabAdminUser().has_permission(request=MagicMock(), view=MagicMock())
