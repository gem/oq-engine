#!/usr/bin/env bash
# Emulate, without root, the "WebUI and calculation with Auth" step of
# .github/workflows/server_install.yaml
#
# What it does: starts gunicorn by hand from the repository (not from
# /opt/openquake nor from systemd), with a scratch engine database, and
# checks login, access log and calculation outputs as the workflow does.
# The setup is shared with run_webui_concurrency.sh via webui_common.sh.
#
# What it does not do: run install.py, useradd, sudo, write the systemd
# unit, or install gunicorn (it must already be in the venv, e.g. with
# pip install "gunicorn>=26.2").
#
# Environment variables (all optional):
#   OQ_VENV         venv where openquake.engine is installed from this
#                   repository (default: $HOME/openquake)
#   OQ_EMULATE_DIR  scratch directory for database, data, logs and
#                   settings (default: $TMPDIR/oq-emulate-server-install,
#                   $TMPDIR defaulting to /tmp)
#
# Usage: .github/scripts/emulate_server_install.sh
# The exit status is 0 only if every check passes.
set -uo pipefail
HERE=$(cd "$(dirname "$0")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
VENV=${OQ_VENV:-$HOME/openquake}
RUN=${OQ_EMULATE_DIR:-${TMPDIR:-/tmp}/oq-emulate-server-install}
# shellcheck source=webui_common.sh
. "$HERE/webui_common.sh"
trap webui_stop EXIT

webui_setup
webui_create_user openquake level_1_password
webui_start || fail "webui not up"

LOGIN_URL=$BASE/accounts/login/
COOKIES=$RUN/cookies.txt
CURL_BIN="curl -s -c $COOKIES -b $COOKIES -e $LOGIN_URL"
echo "== login"
$CURL_BIN $LOGIN_URL -o /dev/null
TOKEN="csrfmiddlewaretoken=$(grep csrftoken $COOKIES | sed 's/^.*csrftoken\s*//')"
status=$($CURL_BIN -w "%{http_code}" \
  -d "$TOKEN&username=openquake&password=level_1_password" \
  -X POST $LOGIN_URL -o /dev/null)
[ "$status" = "302" ] || fail "login returned $status"

echo "== access log non-empty"
[ -s "$WEBUI_ACCESS_LOG_DIR/webui-access.log" ] ||
  fail "empty access log"

echo "== run calculation"
"$VENV/bin/oq" engine --run \
  "$REPO/openquake/server/tests/data/archive_ok.zip" ||
  fail "oq engine --run"
sleep 10
status=$($CURL_BIN -w "%{http_code}" -G $BASE/engine/1/outputs \
  -o /dev/null)
[ "$status" = "200" ] || fail "outputs returned $status"

echo "PASS: webui up, login 302, access log written, outputs 200"
