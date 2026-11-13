#!/usr/bin/env bash
# Create WebUI users with level 1 and password level_1_password.
# The environment must be the one of the engine (settings, secret key).
#
# Usage: create_webui_users.sh PYTHON SERVER_DIR USER...
#   PYTHON      the python of the engine venv
#   SERVER_DIR  the directory openquake/server, where manage.py is
set -euo pipefail
python=$1
cd "$2"
shift 2
for user in "$@"; do
  "$python" manage.py createuser "$user" "$user@test.invalid" \
    --level 1 --password level_1_password --no-email
done
