import functools
from unittest import mock

import pytest
from django.test import RequestFactory
from django.urls import reverse

from euphro_auth.tests import factories as auth_factories
from euphrosyne.admin import AdminSite
from lab.tests import factories
from radiation_protection import certification as radiation_protection

from .. import inlines
from ..models import Participation


@pytest.mark.django_db
def test_leader_participation_inline_save():
    project = factories.ProjectFactory()
    user = factories.StaffUserFactory()
    institution = factories.InstitutionFactory()
    data = {
        "participation_set-TOTAL_FORMS": 1,
        "participation_set-INITIAL_FORMS": 0,
        "participation_set-0-id": "",
        "participation_set-0-project": project.id,
        "participation_set-0-user": user.email,
        "participation_set-0-institution": institution.id,
    }

    request = RequestFactory().post(
        reverse("admin:lab_project_change", args=(project.id,)), data=data
    )

    inline = inlines.LeaderParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    formset.save(commit=True)

    assert project.leader.user == user
    assert project.leader.on_premises is True
    assert project.leader.institution == institution


@pytest.mark.django_db
def test_leader_participation_inline_only_accept_one():
    project = factories.ProjectFactory()
    user = factories.StaffUserFactory()
    institution = factories.InstitutionFactory()
    data = {
        "participation_set-TOTAL_FORMS": 1,
        "participation_set-INITIAL_FORMS": 0,
        "participation_set-0-id": "",
        "participation_set-0-project": project.id,
        "participation_set-0-user": user.email,
        "participation_set-0-institution": institution.id,
        "participation_set-1-project": project.id,
        "participation_set-1-user": factories.StaffUserFactory().email,
        "participation_set-1-institution": institution.id,
    }

    request = RequestFactory().post(
        reverse("admin:lab_project_change", args=(project.id,)), data=data
    )

    inline = inlines.LeaderParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    formset.save(commit=True)

    assert project.leader.user == user


@pytest.mark.django_db
def test_on_premises_participation_inline_save():
    project = factories.ProjectFactory()
    institution = factories.InstitutionFactory()
    users = [factories.StaffUserFactory(), factories.StaffUserFactory()]
    data = {
        "participation_set-TOTAL_FORMS": 2,
        "participation_set-INITIAL_FORMS": 0,
        "participation_set-0-id": "",
        "participation_set-0-project": project.id,
        "participation_set-0-user": users[0].email,
        "participation_set-0-institution": institution.id,
        "participation_set-1-id": "",
        "participation_set-1-project": project.id,
        "participation_set-1-user": users[1].email,
        "participation_set-1-institution": institution.id,
    }

    request = RequestFactory().post(
        reverse("admin:lab_project_change", args=(project.id,)), data=data
    )

    inline = inlines.OnPremisesParticipationInline(
        Participation, admin_site=AdminSite()
    )
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    with mock.patch("lab.projects.inlines.transaction") as module_mock:
        formset.save(commit=True)

    assert project.participation_set.filter(on_premises=True).count() == 2

    # Check that the on_commit hook was called for each user
    assert module_mock.on_commit.call_count == 2
    assert all(
        isinstance(c[0][0], functools.partial)
        for c in module_mock.on_commit.call_args_list
    )
    assert all(
        c[0][0].func is radiation_protection.check_radio_protection_certification
        for c in module_mock.on_commit.call_args_list
    )
    assert all(
        c[0][0].args == (users[i],)
        for (i, c) in enumerate(module_mock.on_commit.call_args_list)
    )


@pytest.mark.django_db
def test_leader_user_change_triggers_radioprotection_check():
    project = factories.ProjectFactory()
    institution = factories.InstitutionFactory()
    participation = Participation.objects.create(
        project=project,
        user=factories.StaffUserFactory(),
        institution=institution,
        is_leader=True,
        on_premises=True,
    )

    new_leader = factories.StaffUserFactory()

    data = {
        "participation_set-TOTAL_FORMS": 1,
        "participation_set-INITIAL_FORMS": 1,
        "participation_set-0-id": participation.id,
        "participation_set-0-project": project.id,
        "participation_set-0-user": new_leader.email,
        "participation_set-0-institution": institution.id,
    }

    request = RequestFactory().post(
        reverse("admin:lab_project_change", args=(project.id,)), data=data
    )

    inline = inlines.LeaderParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    with mock.patch("lab.projects.inlines.transaction") as module_mock:
        formset.save(commit=True)

    # Check that the on_commit hook was called
    assert module_mock.on_commit.call_count == 1
    assert all(
        isinstance(c[0][0], functools.partial)
        for c in module_mock.on_commit.call_args_list
    )
    assert all(
        c[0][0].func is radiation_protection.check_radio_protection_certification
        for c in module_mock.on_commit.call_args_list
    )
    assert all(
        c[0][0].args == (new_leader,)
        for (i, c) in enumerate(module_mock.on_commit.call_args_list)
    )


@pytest.mark.django_db
def test_change_leader_participaiton_same_user_no_trigger_radioprotection_check():
    project = factories.ProjectFactory()
    institution = factories.InstitutionFactory()
    participation = Participation.objects.create(
        project=project,
        user=factories.StaffUserFactory(),
        institution=institution,
        is_leader=True,
        on_premises=True,
    )

    data = {
        "participation_set-TOTAL_FORMS": 1,
        "participation_set-INITIAL_FORMS": 1,
        "participation_set-0-id": participation.id,
        "participation_set-0-project": project.id,
        "participation_set-0-user": participation.user.email,
        "participation_set-0-institution": factories.InstitutionFactory().id,
    }

    request = RequestFactory().post(
        reverse("admin:lab_project_change", args=(project.id,)), data=data
    )

    inline = inlines.LeaderParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    with mock.patch("lab.projects.inlines.transaction") as module_mock:
        formset.save(commit=True)

    assert module_mock.on_commit.call_count == 0


@pytest.mark.django_db
def test_on_premises_participation_inline_queryset():
    project = factories.ProjectFactory()
    factories.ParticipationFactory.create_batch(
        size=2, project=project, on_premises=False
    )
    on_premises_participations = factories.ParticipationFactory.create_batch(
        size=2, project=project, on_premises=True
    )

    request = RequestFactory().get(
        reverse("admin:lab_project_change", args=(project.id,))
    )
    request.user = auth_factories.LabAdminUserFactory()

    inline = inlines.OnPremisesParticipationInline(
        Participation, admin_site=AdminSite()
    )
    qs = inline.get_queryset(request)

    assert set(qs) == set(on_premises_participations)


@pytest.mark.django_db
def test_on_premises_participation_inline_formset():
    project = factories.ProjectFactory()
    participation = factories.ParticipationFactory(project=project, on_premises=True)

    with mock.patch(
        "lab.projects.inlines.radiation_protection.user_has_active_certification",
        mock.MagicMock(return_value=True),
    ) as mock_fn:
        formset = inlines.OnPremisesParticipationInline(
            Participation, admin_site=AdminSite()
        ).get_formset(
            RequestFactory().get(
                reverse("admin:lab_project_change", args=(project.id,))
            ),
            project,
        )
        assert any(
            form.instance.user == participation.user
            and form.fields["has_radiation_protection_certification"].initial is True
            for form in formset(instance=project)
        )
        mock_fn.assert_called_once_with(participation.user)


@pytest.mark.django_db
def test_remote_participation_inline_save():
    project = factories.ProjectFactory()
    institution = factories.InstitutionFactory()
    data = {
        "participation_set-TOTAL_FORMS": 2,
        "participation_set-INITIAL_FORMS": 0,
        "participation_set-0-id": "",
        "participation_set-0-project": project.id,
        "participation_set-0-user": factories.StaffUserFactory().email,
        "participation_set-0-institution": institution.id,
        "participation_set-1-id": "",
        "participation_set-1-project": project.id,
        "participation_set-1-user": factories.StaffUserFactory().email,
        "participation_set-1-institution": institution.id,
    }

    request = RequestFactory().post(
        reverse("admin:lab_project_change", args=(project.id,)), data=data
    )

    inline = inlines.RemoteParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    formset.save(commit=True)

    assert project.participation_set.filter(on_premises=False).count() == 2


@pytest.mark.django_db
def test_remote_participation_inline_queryset():
    project = factories.ProjectFactory()
    factories.ParticipationFactory.create_batch(
        size=2, project=project, on_premises=True
    )
    remote_participations = factories.ParticipationFactory.create_batch(
        size=2, project=project, on_premises=False
    )

    request = RequestFactory().get(
        reverse("admin:lab_project_change", args=(project.id,))
    )
    request.user = auth_factories.LabAdminUserFactory()

    inline = inlines.RemoteParticipationInline(Participation, admin_site=AdminSite())
    qs = inline.get_queryset(request)

    assert set(qs) == set(remote_participations)
