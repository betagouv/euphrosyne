from unittest import mock

from django.test import TestCase

from certification.certifications.models import QuizResult
from euphro_auth.tests import factories as auth_factories
from lab.api_views.permissions import IsLabAdminUser
from radiation_protection.api_views import (
    UserRadiationProtectionResultRetrieveSerializer,
    UserRadiationProtectionResultRetrieveView,
)


class TestUserRadiationProtectionResultRetrieveSerializer(TestCase):
    def test_serializer_fields(self):
        serializer = UserRadiationProtectionResultRetrieveSerializer()
        assert "id" in serializer.fields
        assert "created" in serializer.fields
        assert len(serializer.fields) == 2


class TestUserRadiationProtectionResultRetrieveView(TestCase):
    def test_view_configuration(self):
        view = UserRadiationProtectionResultRetrieveView()
        assert view.serializer_class == UserRadiationProtectionResultRetrieveSerializer
        assert IsLabAdminUser in view.permission_classes

    @mock.patch("radiation_protection.api_views.get_radioprotection_certification")
    @mock.patch.object(QuizResult.objects, "filter_valid_results_for_user")
    def test_get_queryset(
        self, mock_filter_valid_results, mock_get_radioprotection_certification
    ):
        user = auth_factories.StaffUserFactory()
        mock_certification = mock.MagicMock()
        mock_get_radioprotection_certification.return_value = mock_certification
        mock_queryset = mock.MagicMock()
        mock_filter_valid_results.return_value = mock_queryset
        mock_queryset.order_by.return_value = mock_queryset

        view = UserRadiationProtectionResultRetrieveView()
        view.kwargs = {"user_id": user.id}

        view.get_queryset()

        mock_filter_valid_results.assert_called_once_with(
            user=user, certification=mock_certification
        )
        mock_queryset.order_by.assert_called_once_with("-created")

    @mock.patch("radiation_protection.api_views.get_object_or_404")
    def test_get_object(self, mock_get_object_or_404):
        user = auth_factories.StaffUserFactory()
        mock_queryset = mock.MagicMock()
        mock_result = mock.MagicMock()
        mock_get_object_or_404.return_value = mock_result

        view = UserRadiationProtectionResultRetrieveView()
        view.kwargs = {"user_id": user.id}
        view.get_queryset = mock.MagicMock(return_value=mock_queryset)

        result = view.get_object()

        mock_get_object_or_404.assert_called_once_with(mock_queryset)
        assert result == mock_result
