#!/usr/bin/env bash
# Switch the WebUI systemd unit of a server or devel installation to gunicorn,
# as in doc/getting-started/installation-instructions/server.md, with
# MPLCONFIGDIR=/tmp for the calculations started by the WebUI. Needs root.
#
# Usage: webui_unit.sh WORKING_DIRECTORY   (the directory of openquake/server)
set -euo pipefail
UNIT=/etc/systemd/system/openquake-webui.service
# gunicorn is an optional dependency: install it in the venv, but not the
# openquake.engine[server] extra, which would replace the engine under test
/opt/openquake/venv/bin/pip install "gunicorn>=26.2"
sed -i \
  -e "s|^WorkingDirectory=.*|WorkingDirectory=$1|" \
  -e "s|^Environment=$|Environment=MPLCONFIGDIR=/tmp|" \
  -e "s|^ExecStart=.*|ExecStart=/opt/openquake/venv/bin/gunicorn --bind 127.0.0.1:8800 --workers 2 --timeout 120 wsgi:application|" \
  "$UNIT"
systemctl daemon-reload
