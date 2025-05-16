import logging
from typing import Type, cast

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from certification.certifications.models import QuizResult
from lab.participations.models import Participation
from lab.runs.models import Run

from .constants import RADIATION_PROTECTION_CERTIFICATION_NAME
from .document import (
    fill_radiation_protection_documents,
    send_document_to_risk_advisor,
)

logger = logging.getLogger(__name__)


@receiver(post_save, sender=QuizResult)
def handle_radiation_protection_certification(
    sender: Type[QuizResult],  # pylint: disable=unused-argument
    instance: QuizResult,
    created: bool,
    **kwargs
):
    """
    Signal handler for when a QuizResult is created.
    If it's for the radiation protection certification and the user passed,
    generate and send the document to the risk advisor.
    """
    if not created:
        return

    try:
        # Check if this is for the radiation protection certification
        if instance.quiz.certification.name != RADIATION_PROTECTION_CERTIFICATION_NAME:
            return

        # Only proceed if the user passed the quiz
        if not instance.is_passed:
            return

        user_projects = Participation.objects.filter(user=instance.user).values_list(
            "project_id", flat=True
        )
        next_user_run = (
            Run.objects.filter(
                project__in=user_projects,
                start_date__gte=timezone.now(),
            )
            .order_by("start_date")
            .select_related("project")
            .first()
        )

        # Generate the document
        documents = fill_radiation_protection_documents(
            quiz_result=instance, next_user_run=next_user_run
        )
        if not documents or not all(documents):
            logger.error(
                "Failed to generate radiation protection document for user %s",
                instance.user.id,
            )
            return
        # After checking that all documents are not None,
        # we can cast to the correct type
        valid_documents = cast(list[tuple[str, bytes]], documents)

        # Send the document to the risk advisor
        if not send_document_to_risk_advisor(instance.user, valid_documents):
            logger.error(
                "Failed to send radiation protection document "
                "to risk advisor for user %s",
                instance.user.email,
            )
            return

        logger.info(
            "Successfully generated and sent radiation protection document for user %s",
            instance.user.email,
        )

    except Exception as e:
        logger.exception(
            "Error processing radiation protection certification for user %s",
            instance.user.email,
            exc_info=e,
        )
