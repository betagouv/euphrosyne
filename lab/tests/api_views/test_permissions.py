from unittest.mock import MagicMock, patch

from lab.api_views.permissions import IsLabAdminOrEuphrosyneBackend, IsLabAdminUser


@patch("lab.api_views.permissions.is_lab_admin")
def test_is_lab_admin_permission(is_lab_admin_fn_mock: MagicMock):
    is_lab_admin_fn_mock.return_value = False
    assert not IsLabAdminUser().has_permission(request=MagicMock(), view=MagicMock())
    is_lab_admin_fn_mock.return_value = True
    assert IsLabAdminUser().has_permission(request=MagicMock(), view=MagicMock())


@patch("lab.api_views.permissions.IsLabAdminUser.has_permission")
def test_is_lab_admin_or_euphrosyne_backend_falls_back_to_lab_admin_permission(
    is_lab_admin_permission_mock: MagicMock,
):
    request = MagicMock()
    view = MagicMock()
    request.user.email = "staff@example.com"
    is_lab_admin_permission_mock.return_value = True

    assert IsLabAdminOrEuphrosyneBackend().has_permission(request=request, view=view)
    is_lab_admin_permission_mock.assert_called_once_with(request, view)
