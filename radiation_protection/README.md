# Radiation protection

Radiation protection is an optional Euphrosyne module providing certification checks,
risk prevention plans, and related notifications.

## Environment variables

- `RADIATION_PROTECTION_TALLY_SECRET_KEY`
- `RADIATION_PROTECTION_RISK_ADVISOR_EMAIL`
- `RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME`
- `RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS`
- `PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS` (comma-separated ROR IDs)

## Employer information workflow

When the `radiation_protection` optional module is installed, Euphrosyne applies
additional employer information checks to support site access, safety documents,
and risk prevention plans.

An on-site participation is considered incomplete when:

- the participation is on site;
- no employer is attached to the participation;
- the participant's institution is not exempt from the employer form requirement.

Remote participations are never part of this workflow. Lab admins are never
blocked by missing employer information. Project leaders follow the same rule as
other participants: they are blocked only when their own on-site participation is
incomplete.

Missing employer information does not block project creation, participation
management, or run scheduling. Instead, affected users are redirected to the
project employer completion page when they access the related project. Blocked
API requests return `403` with the completion URL so the frontend can guide the
user to the same page.

### Employer reminders

Employer reminders are sent by `python manage.py run_checks`, which calls the
radiation protection reminder command when the module is installed.

The reminder command targets runs starting exactly 7 days or 2 days from the
current local date. For each targeted run, it sends:

- one individual email to each incomplete on-site participant;
- one summary email to `RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS`,
  when at least one incomplete participation is found.

No reminder is sent when a run is scheduled.

### Risk prevention plans

`RiskPreventionPlan` objects are created only for participations that are ready
for radiation protection processing. A participation is ready when:

- it is on site;
- the user has a valid radiation protection certification;
- the run is scheduled and upcoming;
- an employer is present, or the institution is exempt from the employer and
  electrical signature workflow.

The Goodflag sending command keeps a final guard: non-exempt plans without
employer information are skipped and logged instead of letting the external
signature process fail.

### Electronic signature providers

#### Goodflag
- `GOODFLAG_API_BASE`
- `GOODFLAG_API_TOKEN`
- `GOODFLAG_USER_ID`
- `GOODFLAG_SIGNATURE_CONSENT_PAGE_ID`
- `GOODFLAG_SIGNATURE_PROFILE_ID`
- `GOODFLAG_TEMPLATE_ID`

## Project overrides

You can override defaults via Django settings:

```
RADIATION_PROTECTION_SETTINGS = {
    "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL": "advisor@example.com",
    "RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME": "Jane Advisor",
}
```
