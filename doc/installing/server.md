# The OpenQuake Engine Server and WebUI

## Advanced configurations

### Authentication support

The OpenQuake Engine server supports authentication provided by [Django](https://docs.djangoproject.com/en/stable/topics/auth/) and its backends.

Create a `openquake/server/local_settings.py` and add:
```python
LOCKDOWN = True
```

Upgrade the database to host users and sessions:

```bash
python -m openquake.server.manage syncdb
```

Add a new local superuser:
```bash
python -m openquake.server.manage createsuperuser
```

#### Authentication using PAM
Authentication can rely on system users through `PAM`, the [Pluggable Authentication Module](https://en.wikipedia.org/wiki/Pluggable_authentication_module). To use this feature the [django-pam](https://github.com/tehmaze/django-pam) extension must be installed and activated

To `openquake/server/local_settings.py` add:

```python
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'dpam.backends.PAMBackend',
)
```
The WebUI process owner must be member of the `shadow` group.

## Running in production

On a production system [nginx](http://nginx.org/en/) + [gunicorn](http://gunicorn.org/) is the recommended software stack to run the WebUI.

#### gunicorn

*gunicorn* can be installed either via `pip` or via the system packager (`apt`, `yum`, ...).

*gunicorn* must be started in the `openquake/server` directory with the following syntax:

```bash
gunicorn -w N wsgi:application
```

where `N` is the number of workers, which is usually equal to `(CPU threads)*2`.

*gunicorn* is usually managed by the OS init system. See an example for [supervisord](../../debian/supervisord/openquake-webui.conf) or [systemd](../../rpm/systemd/openquake-webui.service).

#### nginx

*gunicorn* does not serve static content itself thus a frontend like *nginx* is needed.

To the previous created `openquake/server/local_settings.py` add:

```python
STATIC_ROOT = '/var/www/webui'
```

then collect static files:

```bash
python -m openquake.server.manage collectstatic
```

*nginx* must be configured to act as a reverse proxy for *gunicorn* and to provide static content. A [sample configuration file](examples/nginx.md) is provided.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
