import pytest
from django.test import RequestFactory
from django.urls import reverse

from euphro_auth.tests import factories as auth_factories
from euphrosyne.admin import AdminSite
from lab.tests import factories

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

    inline = inlines.OnPremisesParticipationInline(
        Participation, admin_site=AdminSite()
    )
    formset_class = inline.get_formset(request, project)
    formset = formset_class(data, instance=project)

    assert formset.is_valid(), formset.errors
    formset.save(commit=True)

    assert project.participation_set.filter(on_premises=True).count() == 2


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
