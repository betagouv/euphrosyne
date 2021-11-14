from django.contrib.auth.models import AnonymousUser
from django.test import SimpleTestCase

from ..permissions import is_lab_admin


class TestIsLabAdmin(SimpleTestCase):
    def setUp(self):
        self.anonymous_user = AnonymousUser()

    def test_anonymous_user_is_not_lab_admin(self):
        assert not is_lab_admin(self.anonymous_user)
