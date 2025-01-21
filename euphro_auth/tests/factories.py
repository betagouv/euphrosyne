import factory
import factory.fuzzy
from django.contrib.auth import get_user_model
from django.utils import timezone


class StaffUserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = get_user_model()

    first_name = factory.Faker("first_name")
    last_name = factory.Faker("last_name")
    email = factory.LazyAttribute(
        lambda u: f"{u.first_name}.{u.last_name}@example.com".lower()
    )
    password = factory.Faker("password")
    is_staff = True
    cgu_accepted_at = timezone.now()


class LabAdminUserFactory(StaffUserFactory):
    is_lab_admin = True
