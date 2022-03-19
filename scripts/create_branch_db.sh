set -e

SCRIPTS_DIR="$(dirname "$0")"
PROJECT_DIR="$(dirname $SCRIPTS_DIR)"

source "$PROJECT_DIR"/.env
branch_db_name="$DB_NAME""_""$($SCRIPTS_DIR/db_suffix_for_branch.sh)"
psql postgres --host $DB_HOST --user $DB_USER --port ${DB_PORT:-5432} -c "CREATE DATABASE $branch_db_name with template $DB_NAME;"
echo "🐣 Created new database $branch_db_name from template $DB_NAME."
