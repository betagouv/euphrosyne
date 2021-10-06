set -e

BASEDIR=$(dirname "$0")
source $(dirname $BASEDIR)/.env
branch_db_name="$DB_NAME""_""$($BASEDIR/db_suffix_for_branch.sh)"
psql postgres -c "CREATE DATABASE $branch_db_name with template $DB_NAME;"
echo "🐣 Created new database $branch_db_name from template $DB_NAME."
