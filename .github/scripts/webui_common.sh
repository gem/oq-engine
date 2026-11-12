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
# Nothing is installed system-wide and nothing needs sudo.
PORT=8800
BASE=http://127.0.0.1:$PORT
GPID=

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
  # The engine database is config.server.dbfile, which otherwise defaults
  # to ~/oqdata/db.sqlite3: point it into the scratch directory.
  cat > "$RUN/openquake.cfg" << EOF
[server]
dbfile = $RUN/oqdata/db.sqlite3
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
    "from openquake.baselib import config; print(config.server.dbfile)")
  case "$dbf" in
    "$RUN"/*) ;;
    *) fail "engine DB is $dbf, outside $RUN: refusing to continue" ;;
  esac

  cd "$REPO/openquake/server" || fail "no $REPO/openquake/server"
  "$VENV/bin/oq" engine --upgrade-db || fail "upgrade-db"
  "$VENV/bin/python" manage.py migrate || fail "migrate"
}

# Create a user with level 1 and the given password.
webui_create_user() {
  "$VENV/bin/python" manage.py createuser "$1" "$1@test.invalid" \
    --level 1 --password "$2" --no-email || fail "createuser $1"
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
