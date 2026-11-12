#!/usr/bin/env bash
# Checks of a running WebUI, shared by emulate_server_install.sh and by the
# server and devel installation workflows. The WebUI must already be
# running at --base; this script only tests it.
#
# It checks, in order:
#   1. the login page answers 200 (waits up to 240 s);
#   2. the login with --user and --password gives HTTP 302;
#   3. the access log in --access-log-dir is not empty;
#   4. with --journal: the journal of openquake-webui has the start-up
#      lines written by openquake/server/wsgi.py (needs root);
#   5. the --archive zip is submitted to /v1/calc/run and the job
#      completes within CALC_TIMEOUT seconds (default 300);
#   6. the outputs of that job, its results and the calc list answer 200.
#
# Usage:
#   webui_checks.sh --base URL --user NAME --password PW --archive ZIP \
#       --access-log-dir DIR [--journal]
#
# The exit status is 0 only if every check passes. It needs curl, jq and
# sed. The job submitted in check 5 is a new calculation in the database
# of the WebUI being tested.
set -uo pipefail
BASE= WUSER= WPASS= ARCHIVE= LOGDIR= JOURNAL=0
CALC_TIMEOUT=${CALC_TIMEOUT:-300}

fail() { echo "FAIL: $*"; exit 1; }

while [ $# -gt 0 ]; do
  case $1 in
    --base) BASE=$2; shift 2 ;;
    --user) WUSER=$2; shift 2 ;;
    --password) WPASS=$2; shift 2 ;;
    --archive) ARCHIVE=$2; shift 2 ;;
    --access-log-dir) LOGDIR=$2; shift 2 ;;
    --journal) JOURNAL=1; shift ;;
    *) echo "unknown option: $1"; exit 2 ;;
  esac
done
for var in BASE WUSER WPASS ARCHIVE LOGDIR; do
  [ -n "${!var}" ] || { echo "missing option for $var"; exit 2; }
done

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT
COOKIES=$TMP/cookies.txt
LOGIN=$BASE/accounts/login/

echo "== login page answers 200"
up=0
for _ in $(seq 1 120); do
  code=$(curl -s -o /dev/null -w '%{http_code}' "$LOGIN")
  if [ "$code" = 200 ]; then up=1; break; fi
  sleep 2
done
[ $up = 1 ] || fail "login page not up after 240 s"

echo "== login gives 302"
curl -s -c "$COOKIES" -b "$COOKIES" -o /dev/null "$LOGIN"
TOKEN=$(grep csrftoken "$COOKIES" | sed 's/^.*csrftoken\s*//')
status=$(curl -s -c "$COOKIES" -b "$COOKIES" -e "$LOGIN" \
  -d "csrfmiddlewaretoken=$TOKEN&username=$WUSER&password=$WPASS" \
  -X POST "$LOGIN" -o /dev/null -w '%{http_code}')
[ "$status" = 302 ] || fail "login returned $status"

echo "== access log is not empty"
[ -s "$LOGDIR/webui-access.log" ] ||
  fail "empty access log in $LOGDIR"
cat "$LOGDIR/webui-access.log"

if [ "$JOURNAL" = 1 ]; then
  echo "== journal has the start-up lines"
  journalctl -u openquake-webui --no-pager > "$TMP/journal.log"
  cat "$TMP/journal.log"
  for expected in "Using .*openquake.cfg" "Using .*db.sqlite3"; do
    grep -q "WARNING:root:$expected" "$TMP/journal.log" ||
      fail "missing log line in the journal: $expected"
  done
fi

echo "== submit $ARCHIVE and wait for it"
code=$(curl -s -c "$COOKIES" -b "$COOKIES" -H "X-CSRFToken: $TOKEN" \
  -F "archive=@$ARCHIVE" -o "$TMP/run.json" -w '%{http_code}' \
  "$BASE/v1/calc/run")
[ "$code" = 200 ] || fail "calc run returned $code"
job=$(jq -r '.job_id' "$TMP/run.json")
[ "$job" != null ] || fail "no job_id in $(cat "$TMP/run.json")"
echo "job $job"
status=
deadline=$((SECONDS + CALC_TIMEOUT))
while [ $SECONDS -lt $deadline ]; do
  status=$(curl -s -b "$COOKIES" "$BASE/v1/calc/$job/status" |
    jq -r '.status')
  case $status in complete|failed) break ;; esac
  sleep 2
done
[ "$status" = complete ] ||
  fail "job $job: status '$status' after ${CALC_TIMEOUT}s"

echo "== outputs, results and calc list answer 200"
for path in "/engine/$job/outputs" "/v1/calc/$job/results" \
    "/v1/calc/list"; do
  code=$(curl -s -b "$COOKIES" -o /dev/null -w '%{http_code}' \
    "$BASE$path")
  [ "$code" = 200 ] || fail "$path returned $code"
done

echo "PASS: login page 200, login 302, access log written, job $job"
echo "complete, outputs/results/calc list 200"
