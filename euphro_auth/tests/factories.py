import factory
import factory.fuzzy
from django.contrib.auth import get_user_model


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


class LabAdminUserFactory(StaffUserFactory):
    is_lab_admin = True
