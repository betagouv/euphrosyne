import factory

from certification.certifications.models import CertificationType
from certification.certifications.tests.factories import (
    QuizResult,
)
from certification.models import Certification, QuizCertification

from ..constants import (
    RADIATION_PROTECTION_CERTIFICATION_NAME,
    RADIATION_PROTECTION_CERTIFICATION_NUM_DAYS_VALID,
)


class RadiationProtectionCertificationFactory(factory.django.DjangoModelFactory):
    num_days_valid = RADIATION_PROTECTION_CERTIFICATION_NUM_DAYS_VALID
    name = RADIATION_PROTECTION_CERTIFICATION_NAME
    type_of = CertificationType.QUIZ

    class Meta:
        model = Certification
        django_get_or_create = ("name",)


class RadiationProtectionQuizCertificationFactory(factory.django.DjangoModelFactory):
    certification = factory.SubFactory(RadiationProtectionCertificationFactory)
    passing_score = 100
    url = factory.Faker("url")

    class Meta:
        model = QuizCertification
        django_get_or_create = ("certification",)


class RadiationProtectionQuizResult(factory.django.DjangoModelFactory):
    """
    Factory for creating quiz results related to radiation protection certification.
    """

    quiz = factory.SubFactory(RadiationProtectionQuizCertificationFactory)
    user = factory.SubFactory("lab.tests.factories.StaffUserFactory")

    class Meta:
        model = QuizResult
