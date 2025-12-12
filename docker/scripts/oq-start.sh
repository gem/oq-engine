#!/bin/bash
# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2019-2025 GEM Foundation
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

oq dbserver start &

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

if [ "$OQ_APPLICATION_MODE" = "RESTRICTED" ]; then
    oq_basedir=$(python -c "from openquake import baselib; print(baselib.__path__[0].rsplit('/', 2)[0])")
    for f in $(ls ${oq_basedir}/openquake/server/templates/registration/*.default.tmpl)
    do
        cp "$f" "${f%.default.tmpl}"
    done
	cd ${oq_basedir}/openquake/server
    python3 manage.py migrate
    if [ -n "$OQ_ADMIN_LOGIN" ]; then
        python3 manage.py createuser ${OQ_ADMIN_LOGIN} ${OQ_ADMIN_EMAIL} --level 2 --password ${OQ_ADMIN_PASSWORD} --no-email --staff --superuser
    else
        python3 manage.py createuser admin admin@example.com --level 2 --password admin --no-email --staff --superuser
    fi
fi
if [ -t 1 ]; then
    # TTY mode
    exec oq webui start 0.0.0.0:8800 -s &>> $HOME/oqdata/webui.log &
    /bin/bash
else
    # Headless mode
    exec oq --version
    exec oq webui start 0.0.0.0:8800 -s
fi
