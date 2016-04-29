# OpenQuake Engine Celery supervisord configuration

To `/etc/supervisord/conf.d/celeryd.conf` add:

```ini
[program:celery]
; Installation from sources requires the PYTHONPATH to be set:
;environment=PYTHONPATH="/usr/local/openquake/oq-engine:/usr/local/openquake/oq-hazardlib:/usr/local/openquake/oq-nrmllib:/usr/local/openquake/oq-risklib",DJANGO_SETTINGS_MODULE="openquake.server.settings"

; Precise
;command=celeryd --purge
; Trusty
command=celery worker --purge -Ofair

; This must be set to the oq-engine installation dir
; /usr/share/openquake/engine is the default for installation from packages
directory=/usr/share/openquake/engine
user=celery
group=celery
stdout_logfile=/var/log/celery/celeryd.log
stderr_logfile=/var/log/celery/celeryd.log

; Autostart should be false on cluster workers
;autostart=false
autostart=true

autorestart=true
startsecs=10

; Stop the process using "KILL" instead of "TERM"
stopsignal=KILL
killasgroup=true

; Trusty only
stopasgroup=true
```
