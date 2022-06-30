#!/bin/bash

set -e

trap "kill 0" EXIT




datetime=$(date +'%Y-%m-%dT%H:%M')

production_db_url=$(scalingo --region osc-secnum-fr1 --app euphrosyne-production env | grep SCALINGO_POSTGRESQL_URL | tail -n1 | sed -E 's/^[^=]+=(.*)\?.*$/\1/g')
local_production_db_url=$(echo $production_db_url | sed -E 's/@[^/]+\//@localhost:10000\//')

dumpfile=dump-"euphrosyne-production-$datetime".pgsql


echo "🚇🟢 Opening tunnel to production db"
scalingo --region osc-secnum-fr1 --app euphrosyne-production db-tunnel SCALINGO_POSTGRESQL_URL >/dev/null &>/dev/null &
tunnel_pid=$!
sleep 2
echo "⬇️  Dumping from production db into file $dumpfile"
pg_dump --clean --if-exists --format c --dbname $local_production_db_url --no-owner --no-privileges --no-comments --exclude-schema 'information_schema' --exclude-schema '^pg_*' --file "$dumpfile"
kill $tunnel_pid
echo "⬇️ ✅ 🚇🔴"