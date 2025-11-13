import factory

from certification.certifications.models import CertificationType
from certification.certifications.tests.factories import (
    QuizResult,
)
from certification.models import Certification, QuizCertification
from lab.tests import factories as lab_factories

from ..constants import (
    RADIATION_PROTECTION_CERTIFICATION_NAME,
    RADIATION_PROTECTION_CERTIFICATION_NUM_DAYS_VALID,
)
from ..models import ElectricalSignatureProcess, RiskPreventionPlan


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


class RiskPreventionPlanFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating risk prevention plans.
    """

    participation = factory.SubFactory(lab_factories.ParticipationFactory)
    run = factory.SubFactory(lab_factories.RunFactory)
    risk_advisor_notification_sent = False

    class Meta:
        model = RiskPreventionPlan


class ElectricalSignatureProcessFactory(factory.django.DjangoModelFactory):
    """
    Factory for creating electrical signature processes.
    """

    label = factory.Faker("sentence")
    risk_prevention_plan = factory.SubFactory(RiskPreventionPlanFactory)
    provider_name = "goodflag"
    provider_workflow_id = factory.Faker("uuid4")
    is_completed = False

    class Meta:
        model = ElectricalSignatureProcess
