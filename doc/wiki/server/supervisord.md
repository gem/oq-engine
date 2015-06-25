# OpenQuake Engine WebUI supervisord configuration

To `/etc/supervisord/conf.d/webui.conf` add:

```ini
[program:webui]
; Installation from sources requires the PYTHONPATH to be set:
; environment=PYTHONPATH="/usr/local/openquake/oq-engine:/usr/local/openquake/oq-hazardlib:/usr/local/openquake/oq-nrmllib:/usr/local/openquake/oq-risklib",DJANGO_SETTINGS_MODULE="openquake.engine.settings",OQ_LOCAL_CFG_PATH="openquake_worker.cfg
environment=DJANGO_SETTINGS_MODULE="openquake.server.settings"
directory=/usr/lib/python2.7/dist-packages/openquake/server
; Using embedded django server
; command=python manage.py runserver 0.0.0.0:8800 --noreload
; Using gunicorn
command=gunicorn -w 2 wsgi:application
user=openquake
group=openquake
stdout_logfile=/var/log/openquake/oq-engine-webui.log
stderr_logfile=/var/log/openquake/oq-engine-webui.log
autostart=true
autorestart=true
startsecs=10
stopsignal=KILL
killasgroup=true
```
