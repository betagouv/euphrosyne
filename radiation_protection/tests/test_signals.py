from datetime import timedelta
from unittest import mock

from django.test import TestCase
from django.utils import timezone

from certification.certifications.models import QuizResult
from certification.certifications.tests.factories import (
    QuizResultFactory,
)
from euphro_auth.tests import factories as auth_factories
from lab.participations.models import Participation
from lab.tests import factories as lab_factories
from radiation_protection.models import RiskPreventionPlan
from radiation_protection.signals import (
    handle_radiation_protection_certification,
    handle_radiation_protection_on_participation,
    handle_radiation_protection_on_schedule_run,
)
from radiation_protection.tests.factories import RadiationProtectionQuizResult


class TestHandleRadiationProtectionCertification(TestCase):
    """Test cases for handle_radiation_protection_certification signal handler."""

    def test_not_created_returns_early(self):
        """Test that handler returns early when quiz result is not newly created."""
        initial_count = RiskPreventionPlan.objects.count()
        result = RadiationProtectionQuizResult(is_passed=True, score=95)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=result,
            created=False,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_wrong_certification_returns_early(self):
        """Test that handler returns early for non-radiation
        protection certification."""
        initial_count = RiskPreventionPlan.objects.count()
        other_quiz_result = QuizResultFactory(is_passed=True, score=95)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=other_quiz_result,
            created=True,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_failed_quiz_returns_early(self):
        """Test that handler returns early when user failed the quiz."""
        initial_count = RiskPreventionPlan.objects.count()
        result = RadiationProtectionQuizResult(is_passed=False, score=10)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=result,
            created=True,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_no_on_premises_participations(self):
        """Test handler when user has no on-premises participations."""
        initial_count = RiskPreventionPlan.objects.count()

        user = auth_factories.StaffUserFactory()
        user.participation_set.all().delete()  # Ensure no participations

        lab_factories.ParticipationFactory(user=user, on_premises=False)

        result = RadiationProtectionQuizResult(is_passed=True, score=95, user=user)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=result,
            created=True,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_no_upcoming_runs(self):
        """Test handler when user has participations but no upcoming runs."""
        initial_count = RiskPreventionPlan.objects.count()

        user = auth_factories.StaffUserFactory()
        user.participation_set.all().delete()  # Ensure no participations

        to_schedule_run = lab_factories.RunFactory(start_date=None)
        past_run = lab_factories.RunFactory(
            start_date=timezone.now() - timedelta(days=1)
        )

        lab_factories.ParticipationFactory(
            user=user, on_premises=True, project=to_schedule_run.project
        )
        lab_factories.ParticipationFactory(
            user=user, on_premises=True, project=past_run.project
        )

        quiz_result = RadiationProtectionQuizResult(is_passed=True, score=95, user=user)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=quiz_result,
            created=True,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_all_runs_have_plans(self):
        """Test handler when all upcoming runs already have risk prevention plans."""
        # Create existing risk prevention plan
        user = auth_factories.StaffUserFactory()
        user.participation_set.all().delete()  # Ensure no participations

        run = lab_factories.RunFactory(start_date=timezone.now() + timedelta(days=7))
        participation = lab_factories.ParticipationFactory(
            user=user, on_premises=True, project=run.project
        )

        RiskPreventionPlan.objects.create(
            participation=participation,
            run=run,
        )
        initial_count = RiskPreventionPlan.objects.count()

        quiz_result = RadiationProtectionQuizResult(is_passed=True, score=95, user=user)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=quiz_result,
            created=True,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_success_case_creates_plan(self):
        """Test successful creation of risk prevention plan."""
        user = auth_factories.StaffUserFactory()
        user.participation_set.all().delete()  # Ensure no participations

        run = lab_factories.RunFactory(start_date=timezone.now() + timedelta(days=7))
        run_participation = lab_factories.ParticipationFactory(
            user=user, on_premises=True, project=run.project
        )
        other_run = lab_factories.RunFactory(
            start_date=timezone.now() + timedelta(days=14)
        )
        other_run_participation = lab_factories.ParticipationFactory(
            user=user, on_premises=True, project=other_run.project
        )

        initial_count = RiskPreventionPlan.objects.count()

        quiz_result = RadiationProtectionQuizResult(is_passed=True, score=95, user=user)

        handle_radiation_protection_certification(
            sender=QuizResult,
            instance=quiz_result,
            created=True,
        )

        assert RiskPreventionPlan.objects.count() == initial_count + 2
        assert RiskPreventionPlan.objects.filter(
            participation=run_participation, run=run
        ).exists()
        assert RiskPreventionPlan.objects.filter(
            participation=other_run_participation, run=other_run
        ).exists()

    @mock.patch("radiation_protection.signals.logger")
    def test_exception_handling(self, mock_logger):
        """Test that exceptions are logged and don't crash the handler."""
        # Create scenario that will cause an exception
        quiz_result = RadiationProtectionQuizResult(is_passed=True, score=95)

        with mock.patch(
            "radiation_protection.signals.Participation.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            # Should not raise an exception
            handle_radiation_protection_certification(
                sender=QuizResult,
                instance=quiz_result,
                created=True,
            )

            # Verify exception was logged
            mock_logger.exception.assert_called_once()
            args = mock_logger.exception.call_args[0]
            assert "Error processing radiation protection certification" in args[0]
            assert quiz_result.user.email in args
            assert quiz_result.id in args


class TestHandleRadiationProtectionOnScheduleRun(TestCase):
    """Test cases for handle_radiation_protection_on_schedule_run signal handler."""

    def test_no_participations(self):
        """Test handler when run has no participations."""
        run = lab_factories.RunFactory()
        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_schedule_run(
            None,
            run,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_no_on_premises_participations(self):
        """Test handler when run has no on-premises participations."""
        run = lab_factories.RunFactory()
        run.project.participation_set.all().delete()  # Ensure no participations
        lab_factories.ParticipationFactory(project=run.project, on_premises=False)

        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_schedule_run(
            None,
            run,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_user_without_certification(self, mock_check):
        """Test handler when user doesn't have radiation protection certification."""
        user = auth_factories.StaffUserFactory()
        run = lab_factories.RunFactory(
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )
        run.project.participation_set.all().delete()  # Ensure no participations
        mock_check.return_value = False

        initial_count = RiskPreventionPlan.objects.count()

        participation = lab_factories.ParticipationFactory(
            user=user, project=run.project, on_premises=True
        )

        assert RiskPreventionPlan.objects.count() == initial_count
        mock_check.assert_called_once_with(participation.user)

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_user_with_certification(self, mock_check):
        """Test handler when user has radiation protection certification."""
        user = auth_factories.StaffUserFactory()
        run = lab_factories.RunFactory(
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )
        run.project.participation_set.all().delete()  # Ensure no participations

        mock_check.return_value = True

        initial_count = RiskPreventionPlan.objects.count()

        participation = lab_factories.ParticipationFactory(
            user=user, project=run.project, on_premises=True
        )

        assert RiskPreventionPlan.objects.count() == initial_count + 1
        plan = RiskPreventionPlan.objects.get(
            participation=participation,
            run=run,
        )
        assert plan.participation == participation
        assert plan.run == run
        mock_check.assert_called_once_with(participation.user)

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_multiple_participations_mixed_certification(self, mock_check):
        """Test handler with multiple participations and mixed certification status."""
        user1 = auth_factories.StaffUserFactory()
        user2 = auth_factories.StaffUserFactory()

        # Only user1 has certification
        def check_certification(user):
            return user == user1

        mock_check.side_effect = check_certification

        run = lab_factories.RunFactory(
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )
        run.project.participation_set.all().delete()  # Ensure no participations

        initial_count = RiskPreventionPlan.objects.count()

        participation1 = lab_factories.ParticipationFactory(
            user=user1, project=run.project, on_premises=True
        )
        participation2 = lab_factories.ParticipationFactory(
            user=user2, project=run.project, on_premises=True
        )

        assert RiskPreventionPlan.objects.count() == initial_count + 1
        assert RiskPreventionPlan.objects.filter(
            participation=participation1, run=run
        ).exists()
        assert not RiskPreventionPlan.objects.filter(
            participation=participation2, run=run
        ).exists()

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_plan_already_exists(self, mock_check):
        """Test handler when risk prevention plan already exists."""
        user = auth_factories.StaffUserFactory()
        project = lab_factories.ProjectFactory()
        participation = lab_factories.ParticipationFactory(
            user=user, project=project, on_premises=True
        )
        upcoming_run = lab_factories.RunFactory(
            project=project,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )

        mock_check.return_value = True

        # Create existing plan
        RiskPreventionPlan.objects.create(
            participation=participation,
            run=upcoming_run,
        )
        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_schedule_run(
            None,
            instance=upcoming_run,
        )

        # Should not create duplicate
        assert RiskPreventionPlan.objects.count() == initial_count

    @mock.patch("radiation_protection.signals.logger")
    def test_exception_handling(self, mock_logger):
        """Test that exceptions are logged and don't crash the handler."""
        project = lab_factories.ProjectFactory()
        upcoming_run = lab_factories.RunFactory(
            project=project,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )

        with mock.patch(
            "radiation_protection.signals.Participation.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            handle_radiation_protection_on_schedule_run(
                None,
                instance=upcoming_run,
            )

            mock_logger.exception.assert_called_once()
            args = mock_logger.exception.call_args[0]
            assert "Error checking radiation protection for scheduled run" in args[0]
            assert upcoming_run.label in args
            assert upcoming_run.project.name in args


class TestHandleRadiationProtectionOnParticipation(TestCase):
    """Test cases for handle_radiation_protection_on_participation signal handler."""

    def test_not_on_premises_returns_early(self):
        """Test that handler returns early for non-on-premises participation."""
        user = auth_factories.StaffUserFactory()
        project = lab_factories.ProjectFactory()
        off_premises_participation = lab_factories.ParticipationFactory(
            user=user, project=project, on_premises=False
        )

        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_participation(
            sender=None,
            instance=off_premises_participation,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    def test_no_scheduled_runs(self):
        """Test handler when project has no scheduled or upcoming runs."""
        user = auth_factories.StaffUserFactory()
        run = lab_factories.RunFactory(start_date=None)
        lab_factories.RunFactory(start_date=timezone.now() - timedelta(days=1))
        participation = lab_factories.ParticipationFactory(
            user=user, project=run.project, on_premises=True
        )

        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_participation(
            sender=None,
            instance=participation,
        )

        assert RiskPreventionPlan.objects.count() == initial_count

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_user_without_certification(self, mock_check):
        """Test handler when user doesn't have radiation protection certification."""
        user = auth_factories.StaffUserFactory()
        upcoming_run = lab_factories.RunFactory(
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )

        mock_check.return_value = False
        initial_count = RiskPreventionPlan.objects.count()

        participation = lab_factories.ParticipationFactory(
            user=user, project=upcoming_run.project, on_premises=True
        )

        assert RiskPreventionPlan.objects.count() == initial_count
        mock_check.assert_called_once_with(participation.user)

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_user_with_certification(self, mock_check):
        """Test handler when user has radiation protection certification."""
        user = auth_factories.StaffUserFactory()
        upcoming_run = lab_factories.RunFactory(
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )

        mock_check.return_value = True
        initial_count = RiskPreventionPlan.objects.count()

        participation = lab_factories.ParticipationFactory(
            user=user, project=upcoming_run.project, on_premises=True
        )

        assert RiskPreventionPlan.objects.count() == initial_count + 1
        plan = RiskPreventionPlan.objects.get(
            participation=participation,
            run=upcoming_run,
        )
        assert plan.participation == participation
        assert plan.run == upcoming_run
        mock_check.assert_called_once_with(participation.user)

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_multiple_upcoming_runs(self, mock_check):
        """Test handler with multiple upcoming runs."""
        user = auth_factories.StaffUserFactory()
        project = lab_factories.ProjectFactory()
        participation = Participation.objects.create(
            user=user, project=project, on_premises=True
        )

        mock_check.return_value = True

        # Create multiple upcoming runs
        run1 = lab_factories.RunFactory(
            project=project,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )
        run2 = lab_factories.RunFactory(
            project=project,
            start_date=timezone.now() + timedelta(days=21),
            end_date=timezone.now() + timedelta(days=28),
        )

        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_participation(
            sender=None,
            instance=participation,
        )

        assert RiskPreventionPlan.objects.count() == initial_count + 2
        assert RiskPreventionPlan.objects.filter(
            participation=participation, run=run1
        ).exists()
        assert RiskPreventionPlan.objects.filter(
            participation=participation, run=run2
        ).exists()

    @mock.patch("radiation_protection.signals.check_radio_protection_certification")
    def test_plan_already_exists(self, mock_check):
        """Test handler when risk prevention plan already exists for some runs."""
        user = auth_factories.StaffUserFactory()
        project = lab_factories.ProjectFactory()
        participation = Participation.objects.create(
            user=user, project=project, on_premises=True
        )
        upcoming_run = lab_factories.RunFactory(
            project=project,
            start_date=timezone.now() + timedelta(days=7),
            end_date=timezone.now() + timedelta(days=14),
        )

        mock_check.return_value = True

        # Create second upcoming run
        run2 = lab_factories.RunFactory(
            project=participation.project,
            start_date=timezone.now() + timedelta(days=21),
            end_date=timezone.now() + timedelta(days=28),
        )

        # Create existing plan for first run
        RiskPreventionPlan.objects.create(
            participation=participation,
            run=upcoming_run,
        )
        initial_count = RiskPreventionPlan.objects.count()

        handle_radiation_protection_on_participation(
            sender=None,
            instance=participation,
        )

        # Should create plan only for second run
        assert RiskPreventionPlan.objects.count() == initial_count + 1
        assert RiskPreventionPlan.objects.filter(
            participation=participation, run=run2
        ).exists()

    @mock.patch("radiation_protection.signals.logger")
    def test_exception_handling(self, mock_logger):
        """Test that exceptions are logged and don't crash the handler."""
        user = auth_factories.StaffUserFactory()
        project = lab_factories.ProjectFactory()
        participation = Participation.objects.create(
            user=user, project=project, on_premises=True
        )

        with mock.patch(
            "radiation_protection.signals.Run.objects.filter"
        ) as mock_filter:
            mock_filter.side_effect = Exception("Database error")

            handle_radiation_protection_on_participation(
                sender=None,
                instance=participation,
            )

            mock_logger.exception.assert_called_once()
            args = mock_logger.exception.call_args[0]
            assert "Error checking radiation protection for participation" in args[0]
            assert participation.id in args
