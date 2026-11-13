#!/usr/bin/env bash
# Adapt the WebUI systemd unit of a server or devel installation, which
# install.py writes with gunicorn, to the CI: 2 workers, a timeout of 120
# seconds, the settings in WORKING_DIRECTORY and MPLCONFIGDIR=/tmp for the
# calculations started by the WebUI. Needs root.
#
# Usage: webui_unit.sh WORKING_DIRECTORY   (the directory of openquake/server)
set -euo pipefail
UNIT=/etc/systemd/system/openquake-webui.service
# gunicorn is installed by install.py in server installations
[ -x /opt/openquake/venv/bin/gunicorn ] || { echo "no gunicorn"; exit 1; }
sed -i \
  -e "s|^WorkingDirectory=.*|WorkingDirectory=$1|" \
  -e "s|^Environment=$|Environment=MPLCONFIGDIR=/tmp|" \
  -e "s|^ExecStart=.*|ExecStart=/opt/openquake/venv/bin/gunicorn --bind 127.0.0.1:8800 --workers 2 --timeout 120 wsgi:application|" \
  "$UNIT"
systemctl daemon-reload
