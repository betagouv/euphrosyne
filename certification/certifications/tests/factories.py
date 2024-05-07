import factory
import factory.random

from lab.tests.factories import StaffUserFactory

from ..models import Certification, CertificationType, QuizCertification, QuizResult


class CertificationFactory(factory.django.DjangoModelFactory):
    num_days_valid = 365

    class Meta:
        model = Certification


class CertificationOfTypeQuizFactory(factory.django.DjangoModelFactory):
    type_of = CertificationType.QUIZ

    class Meta:
        model = Certification


class QuizCertificationFactory(factory.django.DjangoModelFactory):
    certification = factory.SubFactory(
        CertificationOfTypeQuizFactory, type_of=CertificationType.QUIZ
    )
    passing_score = 100
    url = factory.Faker("url")

    class Meta:
        model = QuizCertification


class QuizResultFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = QuizResult

    user = factory.SubFactory(StaffUserFactory)
    quiz = factory.SubFactory(QuizCertificationFactory)
