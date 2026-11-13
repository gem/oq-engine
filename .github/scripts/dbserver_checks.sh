#!/usr/bin/env bash
# Checks of the DbServer of a server or devel_server installation, once
# the services are running. Needs root (useradd, runuser, journalctl).
#
# 1. the openquake-dbserver and openquake-webui services are active;
# 2. the v0 API is served by the DbServer only, and only with the API key;
# 3. a calculation run with `oq engine --run` by a regular user (not
#    openquake, so without write access to the database) completes, and
#    its logs reach the database through the DbServer.
#
# Usage: dbserver_checks.sh JOB_DIR  (a directory containing a job.ini)
# The exit status is 0 only if every check passes.
set -uo pipefail
JOB_DIR=$1
DB=http://127.0.0.1:1908
WEBUI=http://127.0.0.1:8800
TESTER=oqtester

fail() { echo "FAIL: $*"; exit 1; }
code() { curl -s -o /dev/null -w '%{http_code}' "$@"; }

echo "== 1. services"
for service in openquake-dbserver openquake-webui; do
  systemctl is-active --quiet $service || {
    journalctl -u $service --no-pager | tail -30
    fail "$service is not active"; }
done
for _ in $(seq 1 60); do
  [ "$(code $DB/v0/ping)" = 200 ] && break
  sleep 2
done

echo "== 2. routes"
[ "$(code $DB/v0/ping)" = 200 ] || fail "the DbServer does not answer"
[ "$(code -X POST $DB/v0/db/engine_version)" = 403 ] ||
  fail "the DbServer accepts requests without the API key"
[ "$(code $DB/v1/ping)" = 404 ] || fail "the DbServer serves v1"
# with authentication enabled the WebUI redirects to the login page
[ "$(code $WEBUI/v0/ping)" != 200 ] || fail "the WebUI serves v0"

echo "== 3. oq engine --run by $TESTER"
id $TESTER >/dev/null 2>&1 || useradd -m $TESTER
JOB=$(mktemp -d)
cp -r "$JOB_DIR"/. "$JOB"
chmod -R a+rX "$JOB"
runuser -l $TESTER -c "oq engine --run $JOB/job.ini" ||
  fail "oq engine --run failed"
runuser -l $TESTER -c "oq engine --lhc" | tee /dev/stderr |
  grep -q complete || fail "the calculation of $TESTER is not complete"
journalctl -u openquake-dbserver --no-pager | grep -q "POST /v0/db/log" ||
  fail "the logs did not go through the DbServer"

echo "PASS: DbServer checks"
