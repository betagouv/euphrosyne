# Euphrosyne

Euphrosyne is a web application designed for managing and exploring scientific data from heritage science analyses. The platform facilitates project management, experimental documentation, and data visualization for scientific research on cultural heritage objects. This project is built with Django, a Python web framework, and modern JavaScript/TypeScript with Web Components.

For a comprehensive overview of the Euphrosyne ecosystem and its components, please refer to [EUPHROSYNE.md](EUPHROSYNE.md).

## Features

- **Project Management**: Organize scientific investigations on cultural heritage objects with configurable workflows
- **Object Management**: Document objects with materials, dating, provenance, and images
- **Experimental Methods**: Support for various analytical techniques with configurable parameters
- **Laboratory Notebook**: Digital documentation of experiments including measurement points and annotations
- **Data Management**: Secure storage and access control with search capabilities
- **Collaboration Tools**: User management with invitations and role-based permissions
- **Integration**: ORCID integration for researcher identity, Elasticsearch for search, cloud storage for data

## Installation

Follow these steps to install the dependencies required for Euphrosyne:

1. Install Python dependencies:

```
pip install -r requirements/[dev|prod].txt
```

Replace [dev|prod] with 'dev' for development environments and 'prod' for production environments.

2. Install JavaScript dependencies:

```
npm install
```

### Configuration

The project is configured using environment variables listed in the [.env.example](.env.example) file.

You can copy this file to a new `.env` file to easily set up your environment.

| Variable Name                                       | Description                                                                                                                                                                                                                                       |
| --------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| AZURE_STORAGE_CONNECTION_STRING                     | Azure Storage account connection string for static file storage                                                                                                                                                                                   |
| CORS_ALLOWED_ORIGINS                                | Access-Control-Allow-Origin header value for REST API endpoints                                                                                                                                                                                   |
| DJANGO_SETTINGS_MODULE                              | Python path to the Django settings module                                                                                                                                                                                                         |
| DB\_\*                                              | Database configuration variables                                                                                                                                                                                                                  |
| DJANGO_SECRET_KEY                                   | [Secret key](https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY) used by Django for cryptographic signing; also used to sign JWT tokens                                                                                   |
| DJANGO_DEBUG                                        | Optional. Django debug mode                                                                                                                                                                                                                       |
| ELASTICSEARCH_HOST                                  | Elasticsearch instance host (data catalog)                                                                                                                                                                                                        |
| ELASTICSEARCH_USERNAME                              | Elasticsearch credentials                                                                                                                                                                                                                         |
| ELASTICSEARCH_PASSWORD                              | Elasticsearch credentials                                                                                                                                                                                                                         |
| EMAIL_HOST                                          | Email service configuration                                                                                                                                                                                                                       |
| EMAIL_PORT                                          | Email service configuration                                                                                                                                                                                                                       |
| EMAIL_HOST_USER                                     | Email service configuration                                                                                                                                                                                                                       |
| EMAIL_HOST_PASSWORD                                 | Email service configuration                                                                                                                                                                                                                       |
| EUPHROSYNE_TOOLS_API_URL                            | URL to Euphrosyne Tools API                                                                                                                                                                                                                       |
| DEFAULT_FROM_EMAIL                                  | Default sender email address                                                                                                                                                                                                                      |
| CGU_ACCEPTANCE_DATE                                 | Optional. Deadline from which users must accept the new Terms of Use. If a user has not accepted by this date, they will be redirected to the acceptance page                                                                                     |
| FACILITY_NAME                                       | Optional. Full name of the facility. Used in templates, emails, and admin messages for branding                                                                                                                                                   |
| FACILITY_URL                                        | Optional. URL to the facility's website. Used in emails and other communications                                                                                                                                                                  |
| MATOMO_SITE_ID                                      | Matomo site ID for analytics                                                                                                                                                                                                                      |
| ORCID_USE_SANDBOX                                   | ORCID authentication environment selection. If set to 'true', sandbox environment is used. Defaults to false                                                                                                                                      |
| RADIATION_PROTECTION_TALLY_SECRET_KEY               | Secret key used to secure the webhook where Tally posts the results of the radiation protection quiz. It can be found on the integrations configuration page in the Tally form (via https://tally.so/dashboard). (via https://tally.so/dashboard) |
| RADIATION_PROTECTION_ADDITIONAL_NOTIFICATION_EMAILS | Aditional emails to notify when a user successfuly pass the radiation protection certification                                                                                                                                                    |
| SITE_URL                                            | The URL of this Euphrosyne instance                                                                                                                                                                                                               |
| SENTRY_DSN                                          | Optional. Sentry DSN. If omitted, Sentry will not be used                                                                                                                                                                                         |
| SENTRY_ENVIRONMENT                                  | Tag used to filter Sentry events. Possible choices: 'production', 'staging' or 'dev'                                                                                                                                                              |
| SOCIAL_AUTH_ORCID_KEY                               | ORCID application credentials for user authentication                                                                                                                                                                                             |
| SOCIAL_AUTH_ORCID_SECRET                            | ORCID application credentials for user authentication                                                                                                                                                                                             |

### Optional modules

Euphrosyne ships optional modules that can be enabled per instance. By default all optional modules are enabled. 

To enable specific modules, set `EUPHROSYNE_FEATURES` to a comma-separated list:

```
EUPHROSYNE_FEATURES=data_request,lab_notebook,radiation_protection
```

**Note**: 
- If `EUPHROSYNE_FEATURES` is **not set**: all optional modules are enabled by default
- If `EUPHROSYNE_FEATURES` is **set to an empty value** (e.g., `EUPHROSYNE_FEATURES=""`): all optional modules are disabled
- To enable only specific modules, explicitly list them in a comma-separated format

Available optional modules:

- `data_request` — data access workflow and approvals
- `lab_notebook` — digital lab notebook features
- `radiation_protection` — radiation protection certification and prevention plans (`radiation_protection/README.md`)

Optional project overrides can be provided as a dict in settings:

```
RADIATION_PROTECTION_SETTINGS = {
    "RADIATION_PROTECTION_RISK_ADVISOR_EMAIL": "advisor@example.com",
}
```

## Development

To start the Django development server, run:

```
./manage.py runserver
```

This will launch the server at http://localhost:8000.

To build the frontend files in development mode with auto-reload:

```
npm run build:dev
```

This will start Webpack and create the necessary JavaScript and CSS files for the frontend with automatic rebuilding on file changes.

### Frontend Architecture

#### JavaScript Module Management with Webpack

The Euphrosyne frontend is managed with Webpack for module bundling. JavaScript files are compiled from source files in the `./**/assets/js/pages/*.js` directories. Style files (CSS, SCSS, etc.) imported in the JavaScript code are bundled into a single `<filename>.css` file.

To reference JavaScript and CSS files in Django templates, use the following script and link tags:

```
<script src="{% static 'pages/<filename>.js' %}"></script>
<link rel="stylesheet" type="text/css" href="{% static "<filename>.css" %}">
```

### Contributing

Contributions to Euphrosyne are welcome! Please follow the code style guidelines in the CLAUDE.md file and ensure all tests pass before submitting pull requests.

### License

This project is licensed under the terms specified in the LICENSE file.
