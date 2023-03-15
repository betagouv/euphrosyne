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
