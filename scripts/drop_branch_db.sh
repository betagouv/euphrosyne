#!/bin/bash

set -e

SCRIPTS_DIR="$(dirname "$0")"
PROJECT_DIR="$(dirname $SCRIPTS_DIR)"

source "$PROJECT_DIR"/.env
current_branch_name="$(git rev-parse --abbrev-ref HEAD)"
branch_name="${1:-"$current_branch_name"}"
branch_db_name="$DB_NAME""_""$($SCRIPTS_DIR/db_suffix_for_branch.sh $branch_name)"
psql postgres --host $DB_HOST --user $DB_USER -c "DROP DATABASE $branch_db_name;"
echo "⚰️  Dropped database $branch_db_name"
