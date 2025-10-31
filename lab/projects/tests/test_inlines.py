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
    request.user = user

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
    request.user = user

    inline = inlines.LeaderParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    formset.save(commit=True)

    assert project.leader.user == user


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
    request.user = new_leader

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
    request.user = participation.user

    inline = inlines.LeaderParticipationInline(Participation, admin_site=AdminSite())
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    with mock.patch("lab.projects.inlines.transaction") as module_mock:
        formset.save(commit=True)

    assert module_mock.on_commit.call_count == 0
