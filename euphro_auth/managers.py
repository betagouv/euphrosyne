from django.conf import settings
from django.contrib.auth.base_user import BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManagerQuerySet(models.QuerySet):
    """Prevent deletion, rather update is_active to False"""

    def delete(self):
        self.update(is_active=False)

    def filter_has_accepted_cgu(self):
        if not settings.FORCE_LAST_CGU_ACCEPTANCE_DT:
            return self
        return self.filter(cgu_accepted_at__gte=settings.FORCE_LAST_CGU_ACCEPTANCE_DT)


class UserManager(BaseUserManager):
    """Custom user model manager with email as identifier and no deletion."""

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Superuser must have is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Superuser must have is_superuser=True."))
        return self.create_user(email, password, **extra_fields)

    def get_queryset(self):
        return UserManagerQuerySet(self.model, using=self._db)

    def filter_has_accepted_cgu(self):
        return self.get_queryset().filter_has_accepted_cgu()
