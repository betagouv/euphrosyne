set -e

SCRIPTS_DIR="$(dirname "$0")"
PROJECT_DIR="$(dirname $SCRIPTS_DIR)"

pipenv run "$PROJECT_DIR"/manage.py makemessages --all --verbosity 0 --no-location --no-obsolete
pipenv run "$PROJECT_DIR"/manage.py makemessages --all --verbosity 0 --no-location --no-obsolete -d djangojs
