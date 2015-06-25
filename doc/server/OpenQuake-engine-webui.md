~~ DRAFT ~~

# Start the webui
content
# Start the calculation
content
# Use the webui
## Download the outputs
content
## Watch the log
content
## Remove a calculation
content
# Advanced use
## Authentication support
To `local_settings.py` add:
```python
LOCKDOWN = True
```
### Sessions and users DB bootstrap
```bash
DJANGO_SETTINGS_MODULE="openquake.server.settings" python manage.py syncdb --database=auth_db
```

### Add a new local superuser
```bash
DJANGO_SETTINGS_MODULE="openquake.server.settings" python manage.py createsuperuser --database=auth_db
```

### PAM
Process owner must be member of the `shadow` group.

To `local_settings.py` add:

```python
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'dpam.backends.PAMBackend',
)
```

## Running with supervisord

### Supervisord
[OpenQuake Engine WebUI supervisord configuration](supervisord.md)

### Nginx
To `local_settings.py` add:

```python
STATIC_ROOT = '/var/www/webui'
```

Collect static files:

```bash
DJANGO_SETTINGS_MODULE="openquake.server.settings" python manage.py collectstatic
```

[OpenQuake Engine WebUI nginx configuration](nginx.md)
