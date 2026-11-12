#!/usr/bin/env bash
# Emulate, without root, the "WebUI and calculation with Auth" step of
# .github/workflows/server_install.yaml
#
# What it does: starts gunicorn by hand from the repository (not from
# /opt/openquake nor from systemd), with a scratch engine database, runs
# a calculation with the command line, and then runs the WebUI checks of
# webui_checks.sh (the same ones the workflows run). The setup is shared
# with run_webui_concurrency.sh via webui_common.sh.
#
# What it does not do: run install.py, useradd, sudo, write the systemd
# unit, check the journal, or install gunicorn (it must already be in the
# venv, e.g. with pip install "gunicorn>=26.2").
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
ARCHIVE=$REPO/openquake/server/tests/data/archive_ok.zip
# shellcheck source=webui_common.sh
. "$HERE/webui_common.sh"
trap webui_stop EXIT

webui_setup
webui_create_user openquake level_1_password
webui_start || fail "webui not up"

echo "== run a calculation from the command line"
"$VENV/bin/oq" engine --run "$ARCHIVE" || fail "oq engine --run"

echo "== WebUI checks"
"$HERE/webui_checks.sh" --base "$BASE" --user openquake \
  --password level_1_password --archive "$ARCHIVE" \
  --access-log-dir "$WEBUI_ACCESS_LOG_DIR" || fail "WebUI checks"

echo "PASS: emulation of the server installation WebUI step"
