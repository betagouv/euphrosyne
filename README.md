# euphrosyne

Euphrosyne est une application web qui permet d'ouvrir et d'explorer les données de NewAglaé, l'Accélérateur Grand Louvre d'Analyses Elémentaires. Ce projet est basé sur Django, un framework web en Python, et sur des Web Components Javascript compilés avec Webpack.

## Installation

Suivre les étapes suivantes pour installer les dépendances nécessaires au fonctionnement d'Euphrosyne :

1. Installer les dépendances python en exécutant la commande suivante :

```
pip install -r requirements/[dev|prod].txt
```

Remplacer [dev|prod] par dev pour les environnements de développement et prod pour les environnements de production.

2. Installer les dépendances javascript

```
npm install
```

### Configuration

La configuration du projet se fait via des variables d'environnement. Celles-ci sont listées dans le fichier [.env.example](.env.example).

Le contenu du fichier peut-être copié dans un nouveau fichier `.env` pour paramétrer facilement l'environnement.

| Nom de la variable                      | Description                                                                                                                                                                                                                    |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| DJANGO_SETTINGS_MODULE                  | Chemin Python vers le module settings Django.                                                                                                                                                                                  |
| DB\_\*                                  | Variables relatives à la configuration de la base de données.                                                                                                                                                                  |
| DJANGO_SECRET_KEY                       | [Clé secrète](https://docs.djangoproject.com/en/4.1/ref/settings/#std-setting-SECRET_KEY) utilisée par Django pour la signature cryptographique. Est également utilisé pour signer les tokens JWT (Euphrosyne Tools API).      |
| DJANGO_DEBUG                            | Optionnel. Mode debug de Django.                                                                                                                                                                                               |
| EMAIL_HOST                              | Configuration du service d'e-mail.                                                                                                                                                                                             |
| EMAIL_PORT                              | "                                                                                                                                                                                                                              |
| EMAIL_HOST_USER                         | "                                                                                                                                                                                                                              |
| EMAIL_HOST_PASSWORD                     | "                                                                                                                                                                                                                              |
| EUPHROSYNE_TOOLS_API_URL                | URL de Euphrosyne Tools                                                                                                                                                                                                        |
| DEFAULT_FROM_EMAIL                      | Adresse mail de l'expéditeur par défaut.                                                                                                                                                                                       |
| MATOMO_SITE_ID                          | ID du site sur Matomo.                                                                                                                                                                                                         |
| ORCID_USE_SANDBOX                       | Choix de l'environnment pour l'authentification ORCID. Si égale à 'true', l'environnement sandbox est utilisé. Default to false.                                                                                               |
| RADIATION_PROTECTION_CERTIFICATION_NAME | Nom de la certification New AGLAE de radioprotection dans la base de données (modèle `certification.certifications.models.Certification`)                                                                                      |
| RADIATION_PROTECTION_TALLY_SECRET_KEY   | Clé secrète utilisé pour sécuriser le webhook où Tally poste les résultats du quizz de radioprotection. Elle se trouve sur la page de configuration des integrations dans le formulaire Tally (via https://tally.so/dashboard) |
| SITE_URL                                | L'URL de cette instance d'Euphrosyne.                                                                                                                                                                                          |
| SENTRY_DSN                              | Optionnel. Sentry DSN. Si omis, Sentry ne sera pas utilisé.                                                                                                                                                                    |
| SENTRY_ENVIRONMENT                      | Tag utilisé pour filtrer les événements Sentry. Choix possibles : 'production', 'staging' or 'dev'.                                                                                                                            |
| SOCIAL_AUTH_ORCID_KEY                   | Credentials de l'application ORCID pour authentifier les utilisateurs.                                                                                                                                                         |
| SOCIAL_AUTH_ORCID_SECRET                | "                                                                                                                                                                                                                              |

## Développement

Pour lancer le serveur de développement Django, exécutez la commande suivante :

```
./manage.py runserver
```

Cela va lancer le serveur sur http://localhost:8000.

Pour créer les bundles des fichiers relatifs au frontend en mode développement, exécutez la commande suivante :

Pour créer les bundles des fichiers relatifs au frontend en mode développement, exécutez la commande suivante :

```
npm run build:dev
```

Cela va lancer Webpack et créer les fichiers javascript et css nécessaires pour le frontend.

### Frontend

#### Gestion des modules javascript par Webpack

Le frontend d'Euphrosyne est géré par Webpack, un outil de gestion de modules javascript. Les fichiers javascript sont compilés à partir des fichiers présents dans les dossiers `./**/assets/js/pages/*.js`. Les fichiers de style (css, scss, ...) importés dans le code javascript sont regroupés dans un fichier `<filename>.css`.

Pour faire référence aux fichiers javascript et css dans un template Django, vous pouvez utiliser les balises script et link suivantes :

```
<script src="{% static 'pages/<filename>.js' %}"></script>
<link rel="stylesheet" type="text/css" href="{% static "<filename>.css" %}">
```
