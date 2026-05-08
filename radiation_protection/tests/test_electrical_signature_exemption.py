from unittest import mock

import pytest
from django.test import override_settings

from lab.tests import factories as lab_factories
from radiation_protection.electrical_signature.policy import (
    participation_has_required_employer_for_risk_prevention,
    should_exempt_institution,
)
from radiation_protection.models import RiskPreventionPlan


@override_settings(
    PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS=["https://ror.org/123456789"]
)
def test_should_exempt_institution_matches_ror_id():
    assert (
        should_exempt_institution(mock.MagicMock(ror_id="https://ror.org/123456789"))
        is True
    )
    assert (
        should_exempt_institution(mock.MagicMock(ror_id="https://ror.org/987654321"))
        is False
    )


@pytest.mark.django_db
@override_settings(
    PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS=["https://ror.org/123456789"]
)
def test_participation_has_required_employer_with_employer_or_exempt_institution():
    exempt_institution = lab_factories.InstitutionFactory(
        ror_id="https://ror.org/123456789"
    )

    assert (
        participation_has_required_employer_for_risk_prevention(
            lab_factories.ParticipationFactory(
                employer=lab_factories.EmployerFactory(),
            )
        )
        is True
    )
    assert (
        participation_has_required_employer_for_risk_prevention(
            lab_factories.ParticipationFactory(
                employer=None,
                institution=exempt_institution,
            )
        )
        is True
    )
    assert (
        participation_has_required_employer_for_risk_prevention(
            lab_factories.ParticipationFactory(
                employer=None,
                institution=None,
            )
        )
        is False
    )


@pytest.mark.django_db
@override_settings(
    PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS=["https://ror.org/123456789"]
)
def test_risk_prevention_plan_sets_exempt_on_create():
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory(ror_id="https://ror.org/123456789")
    employer = lab_factories.EmployerFactory()
    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    plan = RiskPreventionPlan.objects.create(participation=participation, run=run)

    assert plan.electrical_signature_exempt is True


@pytest.mark.django_db
@override_settings(
    PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS=["https://ror.org/123456789"]
)
def test_risk_prevention_plan_does_not_update_exempt_on_save():
    user = lab_factories.StaffUserFactory()
    admin = lab_factories.StaffUserFactory()
    project = lab_factories.ProjectFactory(admin=admin)
    run = lab_factories.RunFactory(project=project)
    institution = lab_factories.InstitutionFactory(ror_id="https://ror.org/987654321")
    employer = lab_factories.EmployerFactory()
    participation = project.participation_set.create(
        user=user, institution=institution, employer=employer
    )

    plan = RiskPreventionPlan.objects.create(participation=participation, run=run)
    assert plan.electrical_signature_exempt is False

    participation.institution = lab_factories.InstitutionFactory(
        ror_id="https://ror.org/123456789"
    )
    participation.save()

    plan.save()
    plan.refresh_from_db()
    assert plan.electrical_signature_exempt is False
