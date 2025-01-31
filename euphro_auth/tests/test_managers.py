from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from ..models import User
from ..tests import factories


class TestUserQuerySet(TestCase):
    def test_queryset_filter_has_accepted_cgu_when_no_settings(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=None):
            u1 = factories.StaffUserFactory(cgu_accepted_at=None)
            u2 = factories.StaffUserFactory(cgu_accepted_at=None)

            qs = User.objects.filter_has_accepted_cgu()

            assert u1 in qs
            assert u2 in qs

    def test_queryset_filter_has_accepted_cgu_when_dt(self):
        with self.settings(
            FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now() - timedelta(days=1)
        ):
            u1 = factories.StaffUserFactory(cgu_accepted_at=timezone.now())
            u2 = factories.StaffUserFactory(
                cgu_accepted_at=timezone.now() - timedelta(days=2)
            )

            qs = User.objects.filter_has_accepted_cgu()

            assert u1 in qs
            assert u2 not in qs
