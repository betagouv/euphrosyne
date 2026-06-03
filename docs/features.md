# Feature toggles

Euphrosyne supports enabling/disabling optional modules per deployment via the `EUPHROSYNE_FEATURES` environment variable.

## Behavior

- **Not set**: All available features are enabled (default behavior)
- **Set to empty string or whitespace**: NO features are enabled (all disabled)
- **Set to comma-separated list**: Only the specified features are enabled

This means that setting `EUPHROSYNE_FEATURES` to an empty string (`EUPHROSYNE_FEATURES=""`) is the only way to disable all optional features.

## Available features

- `data_management` — project data lifecycle management (archive, restore, and cool-storage immutability)
- `data_request` — data access workflow
- `lab_notebook` — digital lab notebook
- `radiation_protection` — radiation protection certification and prevention plans

Core apps (always enabled): `lab`, `euphro_auth`, `objectstorage`, `standard`, `certification`, `static_pages`, `orcid_oauth`, etc.

## Configuration

Example:

```
EUPHROSYNE_FEATURES=data_management,data_request,lab_notebook
```

Feature-specific settings (when the feature is enabled):

- `data_request`:
  - `DATA_REQUEST_ALLOWED_ORIGINS`
  - Optional comma-separated list of origins allowed to submit `POST /api/data-request/`, for example `DATA_REQUEST_ALLOWED_ORIGINS=https://euphrosyne-digilab-production.osc-secnum-fr1.scalingo.io`.
  - When configured, a missing or non-allowed `Origin` returns `403 Forbidden`. `Origin` contains only `scheme://host[:port]`, so configure the Digilab domain rather than a path such as `/fr/catalog/`.
  - This filters simple automated submissions, but is not a strong guarantee against a bot that forges the `Origin` header.
- `data_management`:
  - `DATA_COOLING_ENABLE`
  - See [project_data_lifecycle.md](project_data_lifecycle.md) for lifecycle flows, API contracts, and operational details.
- `radiation_protection`:
  - `RADIATION_PROTECTION_TALLY_SECRET_KEY`
  - `RADIATION_PROTECTION_RISK_ADVISOR_EMAIL`
  - `RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME`
  - `RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS`
  - `PARTICIPATION_EMPLOYER_FORM_EXEMPT_ROR_IDS`

## Project overrides

You can override any app default via a dict in Django settings:

```
RADIATION_PROTECTION_SETTINGS = {
    "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL": "advisor@example.com",
    "RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME": "Jane Advisor",
}
```
