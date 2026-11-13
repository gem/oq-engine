#!/usr/bin/env bash
# Shared helpers to run the WebUI locally without root, the way the
# "WebUI and calculation with Auth" step of server_install.yaml does.
#
# This file is sourced, not executed, by emulate_server_install.sh and
# run_webui_concurrency.sh. Before calling webui_setup the caller sets:
#   REPO  the repository root
#   VENV  a venv where openquake.engine is installed from REPO
#   RUN   a scratch directory: the engine database, data, logs and
#         settings are written there, never in ~/oqdata
#
# The WebUI is started by hand with gunicorn from REPO/openquake/server,
# with OQ_WEBUI_WORKERS workers (default 2, as in the CI step).
# The DbServer is started by hand with `oq dbserver start -f` on the port
# OQ_DBPORT (default 1908), from a scratch venv RUN/venv which reuses the
# packages of VENV but is marked as a devel_server installation, so that
# `oq engine --run` by the invoking user goes through the DbServer.
# Nothing is installed system-wide and nothing needs sudo.
PORT=8800
BASE=http://127.0.0.1:$PORT
DBPORT=${OQ_DBPORT:-1908}
DBBASE=http://127.0.0.1:$DBPORT
GPID=
DPID=

fail() { echo "FAIL: $*"; exit 1; }

# Create the scratch settings and engine database, then migrate.
webui_setup() {
  [ -x "$VENV/bin/gunicorn" ] ||
    fail "no gunicorn in $VENV, run: $VENV/bin/pip install 'gunicorn>=26.2'"
  rm -rf "$RUN/oqdata" "$RUN/log"
  mkdir -p "$RUN/settings" "$RUN/oqdata" "$RUN/log"
  # Settings are read from the first local_settings.py on sys.path, so
  # PYTHONPATH makes them load without touching the repository. CI writes
  # the same file into site-packages instead.
  cat > "$RUN/settings/local_settings.py" << 'EOF'
import os

APPLICATION_MODE = "RESTRICTED"
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"
WEBUI_ACCESS_LOG_DIR = os.environ["WEBUI_ACCESS_LOG_DIR"]
EOF
  # The engine database is config.dbserver.file, which otherwise defaults
  # to ~/oqdata/db.sqlite3: point it into the scratch directory.
  cat > "$RUN/openquake.cfg" << EOF
[dbserver]
file = $RUN/oqdata/db.sqlite3
host = 127.0.0.1
port = $DBPORT
EOF
  export OQ_DATADIR=$RUN/oqdata
  export WEBUI_ACCESS_LOG_DIR=$RUN/log
  export DJANGO_SECRET_KEY=local-test-only-secret
  export PYTHONPATH=$RUN/settings
  export OQ_CONFIG_FILE=$RUN/openquake.cfg
  # GITHUB_ACTIONS makes settings.py think it is a test run and skip
  # local_settings.py; the systemd unit in CI does not have it
  unset GITHUB_ACTIONS

  local dbf
  dbf=$("$VENV/bin/python" -c \
    "from openquake.baselib import config; print(config.dbserver.file)")
  case "$dbf" in
    "$RUN"/*) ;;
    *) fail "engine DB is $dbf, outside $RUN: refusing to continue" ;;
  esac

  cd "$REPO/openquake/server" || fail "no $REPO/openquake/server"
  "$VENV/bin/oq" engine --upgrade-db || fail "upgrade-db"
  "$VENV/bin/python" manage.py migrate || fail "migrate"
}

# Start gunicorn with the CI settings and wait until the login page
# answers 200 (at most 240 seconds). Sets GPID; returns 1 if not up.
webui_start() {
  # settings.py writes the access log only when getpass.getuser() is
  # "openquake" (getpass reads LOGNAME/USER); the process still runs as
  # the invoking user
  env USER=openquake LOGNAME=openquake "$VENV/bin/gunicorn" \
    --bind 127.0.0.1:$PORT --workers ${OQ_WEBUI_WORKERS:-2} --timeout 120 \
    wsgi:application > "$RUN/gunicorn.log" 2>&1 &
  GPID=$!
  local code
  for _ in $(seq 1 120); do
    code=$(curl -s -o /dev/null -w '%{http_code}' $BASE/accounts/login/)
    [ "$code" = "200" ] && return 0
    sleep 2
  done
  tail -50 "$RUN/gunicorn.log"
  return 1
}

# Stop gunicorn if it was started by webui_start.
webui_stop() {
  [ -n "$GPID" ] && kill "$GPID" 2>/dev/null
  wait 2>/dev/null
  GPID=
}

# Create RUN/venv, a venv using the packages of VENV but marked as a
# devel_server installation by the file OQ_ENGINE_INST_TYPE, as install.py
# does. Sets SPY to its python.
server_venv() {
  local purelib
  rm -rf "$RUN/venv"
  "$VENV/bin/python" -m venv --without-pip "$RUN/venv" || return 1
  echo devel_server > "$RUN/venv/OQ_ENGINE_INST_TYPE"
  purelib=$("$VENV/bin/python" -c \
    "import sysconfig; print(sysconfig.get_paths()['purelib'])")
  # addsitedir processes the .pth files of VENV (editable installs)
  echo "import site; site.addsitedir('$purelib')" > "$("$RUN/venv/bin/python" \
    -c "import sysconfig; print(sysconfig.get_paths()['purelib'])")/oq.pth"
  SPY=$RUN/venv/bin/python
  "$SPY" -c "from openquake.baselib import is_server_installation as s
assert s(), 'RUN/venv is not a server installation'" || return 1
}

# Start the DbServer as the user openquake (as systemd does) and wait
# until it answers (at most 60 seconds). Sets DPID; returns 1 if not up.
dbserver_start() {
  server_venv || return 1
  env USER=openquake LOGNAME=openquake "$SPY" -m openquake.commands \
    dbserver start -f > "$RUN/dbserver.log" 2>&1 &
  DPID=$!
  for _ in $(seq 1 30); do
    [ "$(curl -s -o /dev/null -w '%{http_code}' $DBBASE/v0/ping)" = 200 ] &&
      return 0
    sleep 2
  done
  tail -50 "$RUN/dbserver.log"
  return 1
}

# Stop the DbServer if it was started by dbserver_start.
dbserver_stop() {
  [ -n "$DPID" ] && kill "$DPID" 2>/dev/null && wait "$DPID" 2>/dev/null
  DPID=
}

# Stop the DbServer first, since webui_stop waits for all the children.
all_stop() {
  dbserver_stop
  webui_stop
}

# Run `oq engine --run JOB_INI` as the invoking user, a regular user of
# the server installation RUN/venv: the database is reached through the
# DbServer. Returns 1 if the calculation does not complete.
cli_calc() {
  "$SPY" -m openquake.commands engine --run "$1" > "$RUN/cli_calc.log" 2>&1 ||
    { tail -30 "$RUN/cli_calc.log"; return 1; }
  "$SPY" -m openquake.commands engine --lhc | tail -1 | grep -q complete ||
    { "$SPY" -m openquake.commands engine --lhc; return 1; }
}

# The checks of the DbServer, as in dbserver_checks.sh: the v0 API is
# served by the DbServer only and with the API key, and a calculation of
# a regular user completes with its logs going through the DbServer.
dbserver_checks() {
  local code="curl -s -o /dev/null -w %{http_code}"
  [ "$($code $DBBASE/v0/ping)" = 200 ] || fail "the DbServer does not answer"
  [ "$($code -X POST $DBBASE/v0/db/engine_version)" = 403 ] ||
    fail "the DbServer accepts requests without the API key"
  [ "$($code $DBBASE/v1/ping)" = 404 ] || fail "the DbServer serves v1"
  # with authentication enabled the WebUI redirects to the login page
  [ "$($code $BASE/v0/ping)" != 200 ] || fail "the WebUI serves v0"
  cli_calc "$1" || fail "oq engine --run through the DbServer"
  grep -q "POST /v0/db/log" "$RUN/dbserver.log" ||
    fail "the logs did not go through the DbServer"
}
