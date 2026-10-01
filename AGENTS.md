# Repository checks before publishing a PR

Use `.github/workflows/test.yaml` as the source of truth for required checks.
Run commands from the repository root, with the project Python environment,
development dependencies, Django environment variables and GNU gettext available.

## Translation changes

Whenever adding or changing translated Python or template strings, generate the
catalogue with the exact command used by CI:

```sh
python manage.py makemessages --all --verbosity 0 --no-location --no-obsolete
```

For translated JavaScript or TypeScript strings, use the matching CI command:

```sh
python manage.py makemessages --all --verbosity 0 --no-obsolete --no-location -d djangojs --ignore 'node_modules/*' --ignore 'venv/*' --ignore 'euphrosyne/assets/dist/*' -e js,tsx,ts,jsx
```

Let Django generate the entries and their ordering; do not append entries by hand.
Fill in the new translations, then rerun the relevant command above to normalize
the catalogue's wrapping and ordering. Compile the catalogues:

```sh
python manage.py compilemessages
```

Include the intended `.po` and tracked `.mo` changes in the commit. After staging
the intended catalogue changes, rerun the relevant `makemessages` command and
verify that it produces no content changes relative to the index:

```sh
git diff -I'^"PO' --exit-code -- locale/*/LC_MESSAGES/django.po locale/*/LC_MESSAGES/djangojs.po
```

This ignores catalogue timestamp changes, as CI does. Fix any other difference by
regenerating and reviewing the catalogue before publishing; keep the CI check.

## Python type checks

Run mypy against all tracked Python files except migrations, including settings
and tests, rather than only the edited modules. Stage any intended new Python
files first so they are included in the tracked-file list:

```sh
python -m mypy $(git ls-files '*.py' ':(exclude)**/migrations/**')
```

Annotate empty settings collections explicitly when their type cannot be
inferred, for example `SOCIAL_AUTH_FIELDS_STORED_IN_SESSION: list[str] = []`.
