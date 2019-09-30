#!/bin/bash
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

# This is required to load a custom  local_settings.py when 'oq webui' is used.
export PYTHONPATH=$HOME

cleanup() {
    # SIGTERM is propagated to children.
    # Timeout is managed directly by Docker, via it's '-t' flag:
    # if SIGTERM does not teminate the entrypoint, after the time
    # defined by '-t' (default 10 secs) the container is killed
    kill $WEBUI_PID $DBSERVER_PID
}

waitfor() {
    # Make startup syncronous
    while ! pidof $1 >/dev/null; do
        sleep 1
    done
    pidof $1
}

oq dbserver start &
DBSERVER_PID=$(waitfor oq-dbserver)

# Wait the DbServer to come up; may be replaced with a "oq dbserver wait"
while :
do
    (echo > /dev/tcp/localhost/1908) >/dev/null 2>&1
    result=$?
    if [[ $result -eq 0 ]]; then
        break
    fi
    sleep 1
done

if [ -n "$LOCKDOWN" ]; then
    echo "LOCKDOWN = True" > $HOME/local_settings.py
    oq webui migrate
    echo "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@example.com', 'admin')" | oq shell 2>&1 >/dev/null
fi

if [ -t 1 ]; then
    # TTY mode
    oq webui start 0.0.0.0:8800 &>> $HOME/oqdata/webui.log &
    WEBUI_PID=$(waitfor oq-webui)
    /bin/bash
else
    # Headless mode
    oq webui start 0.0.0.0:8800 &
    WEBUI_PID=$(waitfor oq-webui)
    wait $WEBUI_PID
fi
