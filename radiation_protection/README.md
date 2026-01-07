# Radiation protection

Radiation protection is an optional Euphrosyne module providing certification checks,
risk prevention plans, and related notifications.

## Environment variables

- `RADIATION_PROTECTION_TALLY_SECRET_KEY`
- `RADIATION_PROTECTION_RISK_ADVISOR_EMAIL`
- `RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME`
- `RADIATION_PROTECTION_RISK_ADVISOR_EMAILS`
- `RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS`

## Project overrides

You can override defaults via Django settings:

```
RADIATION_PROTECTION_SETTINGS = {
    "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL": "advisor@example.com",
    "RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME": "Jane Advisor",
}
```
