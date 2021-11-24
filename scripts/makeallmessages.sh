set -e

SCRIPTS_DIR="$(dirname "$0")"
PROJECT_DIR="$(dirname $SCRIPTS_DIR)"

python "$PROJECT_DIR"/manage.py makemessages -v 0 -a --no-location --no-obsolete
