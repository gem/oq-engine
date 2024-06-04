(server)=

# Server and WebUI

## Advanced configurations and Authentication support

### Installation with the universal installer

The OpenQuake Engine server supports authentication provided by [Django](https://docs.djangoproject.com/en/stable/topics/auth/) and its backends.

When installing the OpenQuake Engine with the universal installer the `local_settings.py` file must be located under the folder `openquake/server` of the oq-engine repository.

For example if you clone the repository in the folder `/opt/openquake/src/oq-engine/` you must place the file in `/opt/openquake/src/oq-engine/openquake/server`

If you only download install.py file and run the installation, the `local_settings.py` file must be located in `/opt/openquake/venv/lib/python3.11/site-packages/openquake/server` (replacing python3.11 with the actual python version)

Create a `local_settings.py` and add:
```python
APPLICATION_MODE = 'RESTRICTED'
```

Upgrade the database to host users and sessions:
```console
$ cd /opt/openquake/src/oq-engine/openquake/server
$ sudo -u openquake oq webui migrate
```

Add a new local superuser:
```console
$ cd /opt/openquake/src/oq-engine/openquake/server
$ sudo -u openquake oq webui createsuperuser
```

Setup static files in Django

Open the file `local_settings.py` and add:
```python
# Static Folder
STATIC_ROOT = '/var/www/webui'
```
STATIC_ROOT is the full, absolute path to your static files folder.
Please remember to create the folder /var/www and set the ownership to user openquake.

```console
sudo mkdir /var/www
sudo chown -R openquake /var/www/
```

Then issue the commands:

```console
$ cd /opt/openquake/src/oq-engine/openquake/server
$ sudo -u openquake oq webui collectstatic
```
The `oq` commands must be run as openquake user and the installation must be of kind `server` or `devel_server`.
if, for any reason, the `oq` command isn't available in the path you can use the following syntax:

```console
$ python3 -m openquake.server.manage <subcommand>
```
#### Groups support

Users can be part of groups. Members of the same group can have access to any calculation and output produced by any member of that group; only the owner of a calculation can delete it.


#### Users and groups management

Users and group can be managed via the Django admin interface, available at `/admin` when `LOCKDOWN` is enabled.


#### Authentication using PAM
Authentication can rely on system users through `PAM`, the [Pluggable Authentication Module](https://en.wikipedia.org/wiki/Pluggable_authentication_module). To use this feature [python-pam](https://github.com/FirefighterBlu3/python-pam) and [django-pam](https://github.com/cnobile2012/django-pam) extensions must be installed and activated. To activate them copy `openquake/server/local_settings.py.pam` to `openquake/server/local_settings.py` and restart the `WebUI` service.

This feature is available on _Linux only_ and the WebUI process owner must be member of the `shadow` group.

Mapping of unix groups isn't supported at the moment.

#### Add a web path prefix to webui

To add a web path prefix to the usual webui web path set ``WEBUI_PATHPREFIX`` variable into ``openquake/server/local_settings.py`` to a prefix path starting with ``/`` and ending without it (e.g. ``'/path/prefix'``); the same variable should be set as environment variable.

#### Configure the directory to store the server user access log

By default, user access information is logged through the standard Django logger. In order to write such information to a file, for instance to be digested by Fail2Ban, the variable `WEBUI_ACCESS_LOG_DIR` must be specified in `local_settings.py`, e.g.:
```python
WEBUI_ACCESS_LOG_DIR = '/var/log/oq-engine'
```
In that case the file `webui-access.log` will be created inside the specified directory.
Please note that the directory must be created if it does not exist yet, e.g.:
```console
$ sudo mkdir /var/log/oq-engine
```
Furthermore, the user `openquake` must own that directory.

## Running in production

On a production system [nginx](http://nginx.org/en/) + [gunicorn](http://gunicorn.org/) is the recommended software stack to run the WebUI.

### gunicorn

*gunicorn* can be installed either via `pip` in the venv of OpenQuake engine. For example:

```console
$ sudo su -
# source /opt/openquake/venv/bin/activate
# pip install gunicorn
# deactivate
```

*gunicorn* must be started in the `openquake/server` directory with the following syntax:

```console
gunicorn -w N wsgi:application
```

where `N` is the number of workers, we suggest `N = 4`.

*gunicorn* is usually managed by the OS init system. See an example for [systemd](https://github.com/gem/oq-engine/blob/master/debian/systemd/openquake-webui.service).

### nginx

*gunicorn* does not serve static content itself thus a frontend like *nginx* is needed.

To the previous created `openquake/server/local_settings.py` add:

```python
STATIC_ROOT = '/var/www/webui'
```

then collect static files:

```console
$ sudo oq webui collectstatic
```

*nginx* must be configured to act as a reverse proxy for *gunicorn* and to provide static content.

When the reverse proxy is configured, add the following to `openquake/server/local_settings.py`:
```python
USE_REVERSE_PROXY = True
```

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
