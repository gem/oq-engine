(server)=

# Server and WebUI

## Advanced configurations and Authentication support

### Installation with the universal installer

The OpenQuake Engine server supports authentication provided by [Django](https://docs.djangoproject.com/en/stable/topics/auth/) and its backends.

When installing the OpenQuake Engine with the universal installer please refer to {ref}`Universal installer <universal>`.

The `local_settings.py` file must be located under the folder `openquake/server` of the oq-engine repository.

For example if you clone the repository in the folder `/opt/openquake/src/oq-engine/` you must place the file in `/opt/openquake/src/oq-engine/openquake/server`.

If you only download the install.py file and run the installation, the `local_settings.py` file must be located in `/opt/openquake/venv/lib/python3.11/site-packages/openquake/server` (replacing python3.11 with the actual python version).

Then, copy the contents of `openquake/server/local_settings.py.server` into `openquake/server/local_settings.py`.

#### Configure the STATIC_ROOT folder

STATIC_ROOT is the full, absolute path to your static files folder.
Please remember to create the folder `/var/www` and set the ownership to the user `openquake`.

```console
sudo mkdir /var/www
sudo chown -R openquake /var/www/
```

#### Configure the directory to store the server user access log

By default, user access information is logged through the standard Django logger.
In order to write such information to a file, for instance to be digested by Fail2Ban, the variable `WEBUI_ACCESS_LOG_DIR` is specified in `local_settings.py`.

In that case the file `webui-access.log` will be created inside the specified directory.
Please note that the directory must be created if it does not exist yet.
Furthermore, the user `openquake` must own that directory.

```console
sudo mkdir /var/log/oq-engine
sudo chown -R openquake /var/log/oq-engine
```

Upgrade the database to host users and sessions:

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake oq webui migrate
```
Add a new local superuser:

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake oq webui createsuperuser
```
To setup static files in Django, issue the following commands, making sure to refer to the actual folder where the engine was installed or cloned (see above):

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake oq webui collectstatic
```
The `oq` commands must be run as the `openquake` user and the installation must be of kind `server` or `devel_server`.
if, for any reason, the `oq` command isn't available in the path, you can use the following syntax:

```console
python3 -m openquake.server.manage <subcommand>
```

#### Groups support

Users can be part of groups. Members of the same group can have access to any calculation and output produced by any member of that group; only the owner of a calculation can delete it.


#### Users and groups management

Users and groups can be managed via the Django admin interface, available at `/admin` when `LOCKDOWN` is enabled.


#### Authentication using PAM
Authentication can rely on system users through `PAM`, the [Pluggable Authentication Module](https://en.wikipedia.org/wiki/Pluggable_authentication_module). To use this feature [python-pam](https://github.com/FirefighterBlu3/python-pam) and [django-pam](https://github.com/cnobile2012/django-pam) extensions must be installed and activated. To activate them copy the contents of `openquake/server/local_settings.py.pam` into `openquake/server/local_settings.py` and upgrade the database:

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake oq webui migrate
```

Then restart the `WebUI` service.

This feature is available on _Linux only_ and the WebUI process owner must be member of the `shadow` group.

Mapping of unix groups isn't supported at the moment.

## Running in production

On a production system, [nginx](http://nginx.org/en/) + [gunicorn](http://gunicorn.org/) is the recommended software stack to run the WebUI.

### gunicorn

*gunicorn* can be installed via `pip` in the venv of the OpenQuake engine. For example:

```console
sudo su -
source /opt/openquake/venv/bin/activate
pip install gunicorn
deactivate
```

*gunicorn* must be started in the `openquake/server` directory with the following syntax:

```console
gunicorn -w N wsgi:application
```

where `N` is the number of workers. We suggest `N = 4`.

*gunicorn* is usually managed by the OS init system.

Please replace the value of ExecStart in the file `/etc/systemd/system/openquake-webui.service` with:
```console
ExecStart=/opt/openquake/venv/bin/gunicorn --bind 127.0.0.1:8800 --workers 4 --timeout 1200 wsgi:application
```

### nginx

*gunicorn* does not serve static content itself thus a frontend like *nginx* is needed.

Please refer to the nginx installation istructions for your operating system.

*nginx* must be configured to act as a reverse proxy for *gunicorn* and to provide static
content (see [documentation](https://docs.gunicorn.org/en/stable/deploy.html)).

When the reverse proxy is configured, add the following to `openquake/server/local_settings.py`:
```python
USE_REVERSE_PROXY = True
```

***

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
