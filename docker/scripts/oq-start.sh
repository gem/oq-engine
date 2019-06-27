#!/bin/bash

# This is required to load a custom  local_settings.py when 'oq webui' is used.
export PYTHONPATH=$HOME

/opt/openquake/bin/python3 -m openquake.server.dbserver &

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
    oq webui start 0.0.0.0:8800 &> /tmp/webui.log &
    /bin/bash
else
    # Headless mode
    oq webui start 0.0.0.0:8800 2>&1 | tee /tmp/webui.log
fi
