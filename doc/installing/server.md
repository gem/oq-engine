# The OpenQuake Engine Server and WebUI

## Advanced configurations

### Authentication support

The OpenQuake Engine server supports authentication provided by [Django](https://docs.djangoproject.com/en/stable/topics/auth/) and its backends.

Create a `/usr/share/openquake/engine/local_settings.py` and add:
```python
LOCKDOWN = True
```

Upgrade the database to host users and sessions:
```bash
$ cd /usr/share/openquake/engine
$ sudo -u openquake oq webui migrate 
```

Add a new local superuser:
```bash
$ cd /usr/share/openquake/engine
$ sudo -u openquake oq webui createsuperuser
```

#### Running from sources

When running the OpenQuake Engine from sources the `local_settings.py` file must be located under `openquake/server/local_settings.py` and `oq` commands must be as current user (without `sudo`).

if, for any reason, the `oq` command isn't available in the path you can use the following syntax:

```bash
$ python3 -m openquake.server.manage <subcommand> 
```

##### Groups support

Users can be part of groups. Members of the same group can have access to any calculation and output produced by any member of that group; only the owner of a calculation can delete it.


##### Users and groups management

Users and group can be managed via the Django admin interface, available at `/admin` when `LOCKDOWN` is enabled.


#### Authentication using PAM
Authentication can rely on system users through `PAM`, the [Pluggable Authentication Module](https://en.wikipedia.org/wiki/Pluggable_authentication_module). To use this feature [python-pam](https://github.com/FirefighterBlu3/python-pam) and [django-pam](https://github.com/cnobile2012/django-pam) extensions must be installed and activated. To activate them copy `openquake/server/local_settings.py.pam` to `openquake/server/local_settings.py` and restart the `WebUI` service.

This feature is available on _Linux only_ and the WebUI process owner must be member of the `shadow` group.

Mapping of unix groups isn't supported at the moment.

## Running in production

On a production system [nginx](http://nginx.org/en/) + [gunicorn](http://gunicorn.org/) is the recommended software stack to run the WebUI.

#### gunicorn

*gunicorn* can be installed either via `pip` or via the system packager (`apt`, `yum`, ...). When using `python-oq-libs` for RedHat or Debian *gunicorn* is already provided.

*gunicorn* must be started in the `openquake/server` directory with the following syntax:

```bash
gunicorn -w N wsgi:application
```

where `N` is the number of workers, which is usually equal to `(CPU threads)*2`.

*gunicorn* is usually managed by the OS init system. See an example for [systemd](../../debian/systemd/openquake-webui.service).

#### nginx

*gunicorn* does not serve static content itself thus a frontend like *nginx* is needed.

To the previous created `openquake/server/local_settings.py` add:

```python
STATIC_ROOT = '/var/www/webui'
```

then collect static files:

```bash
$ sudo oq webui collectstatic
```

*nginx* must be configured to act as a reverse proxy for *gunicorn* and to provide static content. A [sample configuration file](examples/nginx.md) is provided.

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
