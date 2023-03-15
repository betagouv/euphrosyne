# euphrosyne

Ouvrir les données de NewAglaé, l’Accélérateur Grand Louvre d'Analyses Elémentaires

## Installation

1. Installez les dépendances python

```
pip install -r requirements/[dev|prod].txt
```

2. Installez les dépendances javascript

```
npm install
```

### Configuration

La configuration du projet se fait via des variables d'environnement. Celles-ci sont listées dans le fichier [.env.example](.env.example).

Le contenu du fichier peut-être copié dans un nouveau fichier `.env` pour paramétrer facilement l'environnement.

| Nom de la variable       | Description                                                                                                                                                                                                               |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DJANGO_SETTINGS_MODULE   | Chemin Python vers le module settings Django.                                                                                                                                                                             |
| DB\_\*                   | Variables relatives à la configuration de la base de données.                                                                                                                                                             |
| DJANGO_SECRET_KEY        | [Clé secrète](https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY) utilisée par Django pour la signature cryptographique. Est également utilisé pour signer les tokens JWT (Euphrosyne Tools API). |
| DJANGO_DEBUG             | Optionnel. Mode debug de Django.                                                                                                                                                                                          |
| EMAIL_HOST               | Configuration du service d'e-mail.                                                                                                                                                                                        |
| EMAIL_PORT               | "                                                                                                                                                                                                                         |
| EMAIL_HOST_USER          | "                                                                                                                                                                                                                         |
| EMAIL_HOST_PASSWORD      | "                                                                                                                                                                                                                         |
| EUPHROSYNE_TOOLS_API_URL | URL de Euphrosyne Tools                                                                                                                                                                                                   |
| DEFAULT_FROM_EMAIL       | Adresse mail de l'expéditeur par défaut.                                                                                                                                                                                  |
| MATOMO_SITE_ID           | ID du site sur Matomo.                                                                                                                                                                                                    |
| ORCID_USE_SANDBOX        | Whether to use sandbox environment for ORCID authentication. Default to false.                                                                                                                                            |
| SITE_URL                 | This Euphrosyne website URL.                                                                                                                                                                                              |
| SENTRY_DSN               | Optional. Sentry DSN. Omit it to not use Sentry.                                                                                                                                                                          |
| SENTRY_ENVIRONMENT       | Tag use to filter Sentry event. Should be 'production', 'staging' or 'dev'.                                                                                                                                               |
| SOCIAL_AUTH_ORCID_KEY    | ORCID credentials to authenticate users based on this service.                                                                                                                                                            |
| SOCIAL_AUTH_ORCID_SECRET | "                                                                                                                                                                                                                         |

## Développement

1. Lancez le serveur de développement Django :

```
./manage.py runserver
```

2. Lancez Webpack en mode développement pour créer les _bundles_ des fichiers relatifs au frontend.

```
npm run build:dev
```

### Frontend

#### Gestion des modules javascript par Webpack

Webpack cherche les fichiers javascript présent dans les noms de dossiers `./**/assets/js/pages/*.js`.
Pour chaque fichier, un fichier javascript sera compilé et accessible dans un template django avec la balise `static` :

```
<script src="{% static 'pages/<filename>.js' %}"></script>
```

Si des fichiers de style (css, scss, ...) sont importés dans le code javascript, un fichier `<filename.css>` sera créé qui regroupera ces fichiers de style.
Il est possible d'y faire référence de la manière suivante :

```
<link rel="stylesheet" type="text/css" href="{% static "<filename>.css" %}">
```
