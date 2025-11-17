"""
Django signals for radiation protection certification handling.

This module contains signal handlers that manage the creation and maintenance
of Risk Prevention Plans based on radiation protection certification events.
It responds to quiz results, run scheduling, and participation changes to
ensure proper radiation protection compliance for on-premises activities.
"""

import logging
from typing import Type

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from certification.certifications.models import QuizResult
from lab.participations.models import Participation
from lab.runs.models import Run
from lab.runs.signals import run_scheduled
from radiation_protection.certification import check_radio_protection_certification

from .constants import RADIATION_PROTECTION_CERTIFICATION_NAME
from .email import notify_additional_emails
from .models import RiskPreventionPlan

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

        # Get all upcoming runs that do not have a risk prevention plan
        # for the user
        participations = Participation.objects.filter(
            user=instance.user, on_premises=True
        ).values("project_id", "id")
        user_prevention_plan_run_ids = RiskPreventionPlan.objects.filter(
            participation__user=instance.user,
        ).values_list("run_id", flat=True)
        next_user_runs = (
            Run.objects.filter(
                project__in=[
                    participation["project_id"] for participation in participations
                ],
                start_date__gte=timezone.now(),
            )
            .exclude(id__in=user_prevention_plan_run_ids)
            .select_related("project")
        )

        for next_user_run in next_user_runs:
            # Create a risk prevention plan for the user
            participation_id = next(
                participation["id"]
                for participation in participations
                if participation["project_id"] == next_user_run.project_id
            )
            RiskPreventionPlan.objects.get_or_create(
                participation_id=participation_id,
                run=next_user_run,
            )

        # Notify additional emails about the radiation protection certification
        notify_additional_emails(instance.user)

    except Exception as e:
        logger.exception(
            "Error processing radiation protection certification for user %s and quiz result %s",  # pylint: disable=line-too-long
            instance.user.email,
            instance.id,
            exc_info=e,
        )


@receiver(run_scheduled)
def handle_radiation_protection_on_schedule_run(
    sender, instance: Run, **kwargs  # pylint: disable=unused-argument
):
    """
    When a run is scheduled, check participations to check if users have passed
    the radiation protection certification.
    If so, create a risk prevention plan for the user if it does not already exist.
    This is only done for runs that are upcoming
    and do not have a risk prevention plan yet
    """
    if instance.start_date and instance.start_date < timezone.now():
        return
    try:
        participations = Participation.objects.filter(
            project=instance.project, on_premises=True
        )

        for participation in participations:
            if check_radio_protection_certification(participation.user):
                # Create a risk prevention plan for the user
                # if it does not already exist
                RiskPreventionPlan.objects.get_or_create(
                    participation=participation,
                    run=instance,
                )

    except Exception as e:
        logger.exception(
            "Error checking radiation protection for scheduled run %s for project %s",
            instance.label,
            instance.project.name,
            exc_info=e,
        )


@receiver(post_save, sender=Participation)
def handle_radiation_protection_on_participation(
    sender: Type[Participation],  # pylint: disable=unused-argument,
    instance: Participation,
    **kwargs
):
    """
    When a participation to a project is added, check if any run has been scheduled if
    so create a risk prevention plan for the user if it does not already exist.
    This is only done for runs that are upcoming and do not have a risk prevention
    plan yet
    """
    if not instance.on_premises:
        return
    try:
        project_runs = Run.objects.filter(
            project=instance.project,
            start_date__gte=timezone.now(),
        ).all()

        # Check if the user has passed the radiation protection certification
        if not check_radio_protection_certification(instance.user):
            return

        for run in project_runs:
            # Create a risk prevention plan for the user if it does not already exist
            RiskPreventionPlan.objects.get_or_create(
                participation=instance,
                run=run,
            )

    except Exception as e:
        logger.exception(
            "Error checking radiation protection for participation %s",
            instance.id,
            exc_info=e,
        )
