#!/bin/bash

set -e

trap "kill 0" EXIT


pr_number=$1


datetime=$(date +'%Y-%m-%dT%H:%M')

staging_db_url=$(scalingo --app euphrosyne-staging env | grep SCALINGO_POSTGRESQL_URL | tail -n1 | sed -E 's/^[^=]+=(.*)\?.*$/\1/g')
local_staging_db_url=$(echo $staging_db_url | sed -E 's/@[^/]+\//@localhost:10000\//')

reviewapp_db_url=$(scalingo --app "euphrosyne-staging-pr$pr_number" env | grep SCALINGO_POSTGRESQL_URL | tail -n1 | sed -E 's/^[^=]+=(.*)\?.*$/\1/g')
local_reviewapp_db_url=$(echo $reviewapp_db_url | sed -E 's/@[^/]+\//@localhost:10000\//')

dumpfile=dump-"$datetime".pgsql




echo "🚇🟢 Opening tunnel to staging db"
scalingo --app euphrosyne-staging db-tunnel SCALINGO_POSTGRESQL_URL >/dev/null &>/dev/null &
tunnel_pid=$!
sleep 2
echo "⬇️  Dumping from staging db into file $dumpfile"
pg_dump --clean --if-exists --format c --dbname $local_staging_db_url --no-owner --no-privileges --no-comments --exclude-schema 'information_schema' --exclude-schema '^pg_*' --file "$dumpfile"
kill $tunnel_pid
echo "⬇️ ✅ 🚇🔴"

echo "🚇 🟢 Opening tunnel to review app pr$pr_number db"
scalingo --app euphrosyne-staging-pr$pr_number db-tunnel SCALINGO_POSTGRESQL_URL >/dev/null &>/dev/null &
tunnel_pid=$!
sleep 2
echo "⬆️  Restoring to pr$pr_number review app out of $dumpfile"
pg_restore --clean --if-exists --no-owner --no-privileges --no-comments --dbname $local_reviewapp_db_url "$dumpfile"
kill $tunnel_pid
echo "⬇️ ✅ 🚇🔴."

echo "🗑  Deleting $dumpfile"
rm -rf "$dumpfile"
