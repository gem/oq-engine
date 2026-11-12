#!/usr/bin/env bash
# Emulate, without root, the server installation WebUI of
# .github/workflows/server_install.yaml
#
# What it does: starts gunicorn by hand from the repository (not from
# /opt/openquake nor from systemd), with a scratch engine database, creates
# the users of the workflow, and runs the same checks, server_checks.sh.
# The setup is shared with run_webui_concurrency.sh via webui_common.sh.
#
# What it does not do (the list is in the workflow, server_install.yaml,
# next to the server steps): install.py, useradd, sudo, the systemd unit,
# the journal, and the environment of systemd.
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
"$HERE/create_webui_users.sh" "$VENV/bin/python" "$REPO/openquake/server" \
  openquake user2 user3 user4 || fail "users"
webui_start || fail "webui not up"

"$HERE/server_checks.sh" --repo "$REPO" --base "$BASE" \
  --access-log-dir "$WEBUI_ACCESS_LOG_DIR" || fail "server checks"

echo "PASS: emulation of the server installation WebUI"
