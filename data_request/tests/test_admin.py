from unittest import mock

from django.contrib.admin.sites import AdminSite
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from euphro_auth.tests import factories as auth_factories
from euphro_tools.exceptions import EuphroToolsException

from ..admin import BeenSeenListFilter, DataRequestAdmin, action_send_links
from ..models import DataRequest
from . import factories


class TestAdminActionSendLink(TestCase):
    def setUp(self):
        self.admin = DataRequestAdmin(DataRequest, admin_site=AdminSite())
        patcher = mock.patch("data_request.admin.send_links")
        self.send_links_mock = patcher.start()
        self.addCleanup(patcher.stop)

    def test_send_links(self):
        # Test calls send_links with the correct arguments
        # Test set sent_at to the current time
        dr = factories.DataRequestWithRunsFactory(sent_at=None, request_viewed=False)

        action_send_links(
            self.admin, RequestFactory(), DataRequest.objects.filter(id=dr.id)
        )

        self.send_links_mock.assert_called_with(dr)
        dr.refresh_from_db()
        assert dr.sent_at is not None
        assert dr.request_viewed is True

    def test_send_links_when_euphro_tools_exception(self):
        model_admin_mock = mock.MagicMock()
        dr = factories.DataRequestWithRunsFactory(sent_at=None, request_viewed=False)
        self.send_links_mock.side_effect = EuphroToolsException()

        action_send_links(
            model_admin_mock, RequestFactory(), DataRequest.objects.filter(id=dr.id)
        )

        self.send_links_mock.reset_mock()
        model_admin_mock.message_user.assert_called_once()
        dr.refresh_from_db()
        assert dr.sent_at is None
        assert dr.request_viewed is False


class TestAdminFilterBeenSeen(TestCase):
    def setUp(self):
        self.admin = DataRequestAdmin(DataRequest, admin_site=AdminSite())
        self.dr_sent = factories.DataRequestFactory(sent_at=timezone.now())
        self.dr_not_sent = factories.DataRequestFactory(sent_at=None)

    def test_filter_when_no_value(self):
        request = RequestFactory()
        f = BeenSeenListFilter(
            request=request, params={}, model=DataRequest, model_admin=self.admin
        )
        assert f.queryset(request, DataRequest.objects.all()).count() == 2

    def test_filter_when_value_is_0(self):
        request = RequestFactory()
        f = BeenSeenListFilter(
            request=request,
            params={"been_sent": "0"},
            model=DataRequest,
            model_admin=self.admin,
        )
        assert list(f.queryset(request, DataRequest.objects.all()).all()) == [
            self.dr_not_sent
        ]

    def test_filter_when_value_is_1(self):
        request = RequestFactory()
        f = BeenSeenListFilter(
            request=request,
            params={"been_sent": "1"},
            model=DataRequest,
            model_admin=self.admin,
        )
        assert list(f.queryset(request, DataRequest.objects.all()).all()) == [
            self.dr_sent
        ]


class TestAdminDataRequest(TestCase):
    def setUp(self):
        self.admin = DataRequestAdmin(DataRequest, admin_site=AdminSite())

    def test_change_view_set_request_viewed(self):
        data_request = factories.DataRequestFactory(request_viewed=False)
        request = RequestFactory().get(
            reverse("admin:data_request_datarequest_change", args=[data_request.id])
        )
        request.user = auth_factories.LabAdminUserFactory()
        self.admin.change_view(
            request,
            str(data_request.id),
        )

        data_request.refresh_from_db()
        assert data_request.request_viewed

    def test_display_is_sent(self):
        assert (
            self.admin.is_sent(factories.DataRequestFactory(sent_at=timezone.now()))
            is True
        )
        assert self.admin.is_sent(factories.DataRequestFactory(sent_at=None)) is False

    def test_display_viewed(self):
        assert (
            '<p class="fr-badge fr-badge--new fr-badge--sm">'
            in self.admin.display_viewed(
                factories.DataRequestFactory(request_viewed=False)
            )
        )
        assert (
            self.admin.display_viewed(factories.DataRequestFactory(request_viewed=True))
            == ""
        )
