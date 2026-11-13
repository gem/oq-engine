#!/usr/bin/env bash
# Check that the WebUI does not hang when several users use it at once,
# without root and without touching the engine database in ~/oqdata.
#
# What it does:
#   1. sets up a scratch engine database and settings (webui_common.sh);
#   2. creates four users u1..u4 (level 1, password level_1_password);
#   3. starts gunicorn with the CI settings (timeout 120, and 2 workers
#      unless OQ_WEBUI_WORKERS says otherwise);
#   4. runs webui_concurrent_users.py: the four users log in together,
#      each submits archive_ok.zip, waits for it, then browses the pages;
#   5. prints any worker problem found in the gunicorn log (WORKER TIMEOUT,
#      CRITICAL, ERROR, Traceback) and stops gunicorn.
#
# The exit status is the one of webui_concurrent_users.py: 0 if every
# check passed, 1 if some check failed (its output says which one and
# why: HANG, CALC STUCK or ERROR), and 1 also if the WebUI did not start.
#
# Environment variables (all optional):
#   OQ_VENV         venv where openquake.engine is installed from this
#                   repository (default: $HOME/openquake)
#   OQ_CONCURRENCY_DIR  scratch directory (default:
#                   $TMPDIR/oq-webui-concurrency, $TMPDIR defaulting to
#                   /tmp); it is emptied at each run
#   OQ_WEBUI_WORKERS  gunicorn workers (default: 2, as in the CI step)
#   ROUNDS          page-fetch rounds per user (default: 5)
#   TIMEOUT         seconds before one request counts as a HANG
#                   (default: 60)
#   CALC_TIMEOUT    seconds before a calculation counts as stuck
#                   (default: 300)
#
# Usage: .github/scripts/run_webui_concurrency.sh
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
VENV=${OQ_VENV:-$HOME/openquake}
RUN=${OQ_CONCURRENCY_DIR:-${TMPDIR:-/tmp}/oq-webui-concurrency}
ROUNDS=${ROUNDS:-5}
TIMEOUT=${TIMEOUT:-60}
CALC_TIMEOUT=${CALC_TIMEOUT:-300}
# shellcheck source=webui_common.sh
. "$HERE/webui_common.sh"
trap webui_stop EXIT

webui_setup
"$HERE/create_webui_users.sh" "$VENV/bin/python" "$REPO/openquake/server" \
  u1 u2 u3 u4 || fail "users"
webui_start || fail "webui not up"

echo "== 4 users at once, $ROUNDS rounds, request timeout ${TIMEOUT}s," \
  "calc timeout ${CALC_TIMEOUT}s"
"$VENV/bin/python" "$HERE/webui_concurrent_users.py" \
  --base "$BASE" --rounds "$ROUNDS" --timeout "$TIMEOUT" \
  --calc-timeout "$CALC_TIMEOUT" \
  --archive "$REPO/openquake/server/tests/data/archive_ok.zip" \
  --user u1:level_1_password --user u2:level_1_password --user u3:level_1_password --user u4:level_1_password
RC=$?

echo "== gunicorn log: worker problems"
PROBLEMS=$(grep -E "WORKER TIMEOUT|CRITICAL|ERROR|Traceback|Worker exiting" \
  "$RUN/gunicorn.log" | head -40)
if [ -n "$PROBLEMS" ]; then
  echo "$PROBLEMS"
else
  echo "(none)"
fi
echo "== gunicorn log: $(wc -l < "$RUN/gunicorn.log") lines in" \
  "$RUN/gunicorn.log"
echo "client exit status: $RC"
exit $RC
