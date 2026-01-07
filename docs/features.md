# Feature toggles

Euphrosyne supports enabling/disabling optional modules per deployment via the `EUPHROSYNE_FEATURES` environment variable.

## Behavior

- **Not set or empty**: All available features are enabled (default behavior)
- **Set to comma-separated list**: Only the specified features are enabled

This means that setting `EUPHROSYNE_FEATURES` to an empty string (`EUPHROSYNE_FEATURES=""`) has the same effect as not setting it at all—all features will be enabled.

## Available features

- `data_request` — data access workflow
- `lab_notebook` — digital lab notebook
- `radiation_protection` — radiation protection certification and prevention plans

Core apps (always enabled): `lab`, `euphro_auth`, `objectstorage`, `standard`, `certification`, `static_pages`, `orcid_oauth`, etc.

## Configuration

Example:

```
EUPHROSYNE_FEATURES=data_request,lab_notebook
```

Feature-specific settings (when the feature is enabled):

- `radiation_protection`:
  - `RADIATION_PROTECTION_TALLY_SECRET_KEY`
  - `RADIATION_PROTECTION_RISK_ADVISOR_EMAIL`
  - `RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME`
  - `RADIATION_PROTECTION_RISK_ADVISOR_EMAILS`
  - `RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS`

## Project overrides

You can override any app default via a dict in Django settings:

```
RADIATION_PROTECTION_SETTINGS = {
    "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL": "advisor@example.com",
    "RADIATION_PROTECTION_RISK_ADVISOR_FULLNAME": "Jane Advisor",
}
```
