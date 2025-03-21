from django.test import TestCase
from django.utils import timezone

from ...models import Project
from ..factories import ProjectFactory, ProjectWithLeaderFactory, RunFactory


class ProjectModelTestCase(TestCase):
    def test_project_only_finished(self):
        finished_project = ProjectFactory(name="Test Project")
        finished_project.runs.create(
            start_date=timezone.now() - timezone.timedelta(days=2),
            end_date=timezone.now() - timezone.timedelta(days=1),
        )
        not_finished_project = ProjectFactory(name="Not Finished Project")
        not_finished_project.runs.create(
            start_date=timezone.now() - timezone.timedelta(days=1),
            end_date=timezone.now() + timezone.timedelta(days=1),
        )
        self.assertEqual(Project.objects.only_finished().count(), 1)

    def test_project_only_public_confidential(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=None):
            public = ProjectWithLeaderFactory(confidential=False)
            confidential = Project.objects.create(
                name="Confidential Project", confidential=True
            )
            for p in [public, confidential]:  # both have runs over embargo date
                RunFactory(
                    project=p,
                    embargo_date=timezone.now() - timezone.timedelta(days=1),
                )
            self.assertEqual(Project.objects.only_public().count(), 1)

    def test_project_only_public_when_no_run(self):
        with self.settings(FORCE_LAST_CGU_ACCEPTANCE_DT=None):
            public_project = ProjectWithLeaderFactory(
                name="Public Project", confidential=False
            )
            RunFactory(
                project=public_project,
                embargo_date=timezone.now() - timezone.timedelta(days=1),
            )
            Project.objects.create(name="No run Project", confidential=False)

            qs = Project.objects.only_public()
            self.assertEqual(qs.count(), 1)
            self.assertEqual(qs.first().id, public_project.id)

    def test_project_only_public_when_has_not_accepted_cgu(self):
        with self.settings(
            FORCE_LAST_CGU_ACCEPTANCE_DT=timezone.now() - timezone.timedelta(days=1)
        ):
            leader_has_accepted_cgu_project = ProjectWithLeaderFactory(
                confidential=False
            )
            RunFactory(
                project=leader_has_accepted_cgu_project,
                embargo_date=timezone.now() - timezone.timedelta(days=1),
            )
            user = leader_has_accepted_cgu_project.leader.user
            user.cgu_accepted_at = timezone.now()
            user.save()

            leader_has_not_accepted_cgu_project = ProjectWithLeaderFactory(
                confidential=False
            )
            RunFactory(
                project=leader_has_not_accepted_cgu_project,
                embargo_date=timezone.now() - timezone.timedelta(days=1),
            )
            user = leader_has_not_accepted_cgu_project.leader.user
            user.cgu_accepted_at = None
            user.save()

            qs = Project.objects.only_public()
            assert qs.count() == 1
            assert leader_has_accepted_cgu_project in qs

    def test_filter_by_status(self):
        to_schedule_ids = [
            r.project.id for r in RunFactory.create_batch(5, start_date=None)
        ]
        scheduled_ids = [
            r.project.id
            for r in RunFactory.create_batch(
                5, start_date=timezone.now() + timezone.timedelta(days=1)
            )
        ]
        ongoing_ids = [
            r.project.id
            for r in RunFactory.create_batch(
                5,
                start_date=timezone.now() - timezone.timedelta(days=1),
                end_date=timezone.now() + timezone.timedelta(days=1),
            )
        ]
        finished_ids = [
            r.project.id
            for r in RunFactory.create_batch(
                5,
                start_date=timezone.now() - timezone.timedelta(days=2),
                end_date=timezone.now() - timezone.timedelta(days=1),
                project__is_data_available=False,
            )
        ]
        data_available_ids = [
            r.project.id
            for r in RunFactory.create_batch(
                5,
                start_date=timezone.now() - timezone.timedelta(days=2),
                end_date=timezone.now() - timezone.timedelta(days=1),
                project__is_data_available=True,
            )
        ]

        self.assertListEqual(
            list(
                Project.objects.filter_by_status(
                    Project.Status.TO_SCHEDULE
                ).values_list("id", flat=True)
            ),
            to_schedule_ids,
        )
        self.assertListEqual(
            list(
                Project.objects.filter_by_status(Project.Status.SCHEDULED).values_list(
                    "id", flat=True
                )
            ),
            scheduled_ids,
        )
        self.assertListEqual(
            list(
                Project.objects.filter_by_status(Project.Status.ONGOING).values_list(
                    "id", flat=True
                )
            ),
            ongoing_ids,
        )
        self.assertListEqual(
            list(
                Project.objects.filter_by_status(Project.Status.FINISHED).values_list(
                    "id", flat=True
                )
            ),
            finished_ids,
        )
        self.assertListEqual(
            list(
                Project.objects.filter_by_status(
                    Project.Status.DATA_AVAILABLE
                ).values_list("id", flat=True)
            ),
            data_available_ids,
        )

    def test_annotate_first_run_date(self):
        project = ProjectFactory()
        first_run = RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=1), project=project
        )
        RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=2),
            project=project,
        )  # later run to test

        queried_project = Project.objects.annotate_first_run_date().get(id=project.id)

        assert hasattr(queried_project, "first_run_date")
        assert queried_project.first_run_date == first_run.start_date

    def test_only_to_schedule(self):
        # pylint: disable=expression-not-assigned
        RunFactory(
            start_date=timezone.now() + timezone.timedelta(days=1),
        ).project
        to_schedule_projects = [ProjectFactory(), RunFactory(start_date=None).project]
        assert Project.objects.only_to_schedule().count() == 2
        self.assertListEqual(
            list(Project.objects.only_to_schedule()), to_schedule_projects
        )
