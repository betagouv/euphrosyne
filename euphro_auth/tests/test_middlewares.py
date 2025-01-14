from datetime import timedelta

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from ..middlewares import CGUAcceptanceMiddleware
from .factories import StaffUserFactory


class CGUAcceptanceMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CGUAcceptanceMiddleware(get_response=lambda r: r)
        self.user = StaffUserFactory()
        self.user.cgu_accepted_at = None

    def test_authenticated_user_when_not_force_to_cgu_acceptance(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=None):
            request = self.factory.get("/")
            request.user = self.user
            response = self.middleware(request)
            assert response == request

    def test_authenticated_user_when_has_cgu_acceptance(self):
        self.user.cgu_accepted_at = timezone.now()
        self.user.save()
        with self.settings(
            FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now() - timedelta(days=1)
        ):
            request = self.factory.get("/")
            request.user = self.user
            response = self.middleware(request)
            assert response == request

    def test_authenticated_user_when_expired_cgu_acceptance(self):
        self.user.cgu_accepted_at = timezone.now() - timedelta(days=1)
        self.user.save()
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now()):
            request = self.factory.get("/")
            request.user = self.user
            response = self.middleware(request)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("cgu_acceptance"))

    def test_authenticated_user_when_no_cgu_acceptance(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now()):
            request = self.factory.get("/")
            request.user = self.user
            response = self.middleware(request)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse("cgu_acceptance"))

    def test_authenticated_user_on_cgu_acceptance_page(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now()):
            request = self.factory.get(reverse("cgu_acceptance"))
            request.user = self.user
            response = self.middleware(request)
            assert response == request

    def test_authenticated_user_on_admin_logout_page(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now()):
            request = self.factory.get(reverse("admin:logout"))
            request.user = self.user
            response = self.middleware(request)
            assert response == request
