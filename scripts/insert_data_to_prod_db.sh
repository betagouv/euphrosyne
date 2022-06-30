#!/bin/bash

set -e

trap "kill 0" EXIT


dumpfile=$1


production_db_url=$(scalingo --region osc-secnum-fr1 --app euphrosyne-production env | grep SCALINGO_POSTGRESQL_URL | tail -n1 | sed -E 's/^[^=]+=(.*)\?.*$/\1/g')
local_production_db_url=$(echo $production_db_url | sed -E 's/@[^/]+\//@localhost:10000\//')

echo "🚇 🟢 Opening tunnel to production app db"
scalingo --region osc-secnum-fr1 --app euphrosyne-production db-tunnel SCALINGO_POSTGRESQL_URL >/dev/null &>/dev/null &
tunnel_pid=$!
sleep 2
echo "⬆️  Inserting to production app out of $dumpfile"
psql --dbname $local_production_db_url -a -f $dumpfile
kill $tunnel_pid
echo "⬇️ ✅ 🚇🔴."
