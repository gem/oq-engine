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

#### Configure the engine temporary folder

By default, the engine stores temporary files into the system temporary directory. In case you want to use a different directory, you can customize it through the `/opt/openquake/openquake.cfg` configuration file. For instance, after creating the folder `/opt/openquake/tmp`, add to `/opt/openquake/openquake/cfg`:

```yaml
[directory]
    custom_tmp = /opt/openquake/tmp
```

You can also setup a cron job in order to automatically delete old temporary files.

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

#### Upgrade the database to host users and sessions

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake /opt/openquake/venv/bin/python3 manage.py migrate
```

#### Install fixtures for cookie consent

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake /opt/openquake/venv/bin/python3 manage.py loaddata ./fixtures/0001_cookie_consent_required_plus_hide_cookie_bar.json
```

If the current installation requires Google Analytics, please add the `GOOGLE_ANALYTICS_TOKEN` to `local_settings.py` and install another optional fixture:

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake /opt/openquake/venv/bin/python3 manage.py loaddata ./fixtures/0002_cookie_consent_analytics.json
```

Required or optional cookies or groups of them can be added, removed or edited via the Django Admin interface.
New custom cookies can be managed similarly to what is done in `openquake/server/templates/engine/includes/cookie_analytics.html`.
Please refer to `https://django-cookie-consent.readthedocs.io/en/latest/` for further details on how to customize cookies in Django.

#### Add a new local superuser

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake /opt/openquake/venv/bin/python3 manage.py createsuperuser
```

#### Setup static files

To setup static files in Django, issue the following commands, making sure to refer to the actual folder where the engine was installed or cloned (see above):

```console
cd /opt/openquake/src/oq-engine/openquake/server
sudo -u openquake /opt/openquake/venv/bin/python3 manage.py collectstatic
```
The commands must be run as the `openquake` user and the installation must be of kind `server` or `devel_server`.
If, for any reason, the commands are not available in the path, you can use the following syntax:

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
sudo -u openquake /opt/openquake/venv/bin/python3 manage.py migrate
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

*gunicorn* is usually managed by the OS init system.

Please replace the value of ExecStart in the file `/etc/systemd/system/openquake-webui.service` with:
```console
WorkingDirectory=/opt/openquake/src/oq-engine/openquake/server
ExecStart=/opt/openquake/venv/bin/gunicorn --bind 127.0.0.1:8800 --workers 4 --timeout 1200 wsgi:application
```

*gunicorn* must be started in the `openquake/server` directory with the following syntax:

```console
gunicorn -w N wsgi:application
```

where `N` is the number of workers. We suggest `N = 4`.

### Using Environment Variables in systemd Units

Systemd has Environment directive which sets environment variables for executed processes. It takes a space-separated list of variable assignments. This option may be specified more than once in which case all listed variables will be set. If the same variable is set twice, the later setting will override the earlier setting. If the empty string is assigned to this option, the list of environment variables is reset, all prior assignments have no effect.

With example below you can configure dbserver daemon with the DJANGO_SETTINGS_MODULE variable. 

Just edit `/etc/systemd/system/openquake-dbserver.service` for openquake-dbserver.service:

```
[Service]
# Env Vars
Environment=DJANGO_SETTINGS_MODULE=openquake.server.settings

```

Then run `sudo systemctl daemon-reload` and `sudo systemct restart openquake-dbserver.service` to apply new environments to dbserver daemon.


### Limit systemd services with control group (slice)

If you need to set a limit on the resources available for the OpenQuake service, Systemd offers a simple solution to create resource limits for a service,
a unit type called "slice".

This is a control group, which may apply limits that affect all processes in this slice/control group.

To create a slice called webui.slice:

```console
systemctl edit openquake-webui.slice

[Unit]
Description=OpenQuake Webui Slice
Before=slices.target

[Slice]
MemoryAccounting=true
MemoryMax=10G
CPUAccounting=true
CPUQuota=50%
TasksMax=4096
```

Edit the webui.service file:
```console
systemctl edit --full openquake-webui.service
```

and add in the [Service] section:
```console
Slice=openquake-webui.slice
```

After changing systemd config files a reload of the daemon is required and a restart of the service:

```console
systemctl daemon-reload
systemctl stop openquake-webui.service
systemctl start openquake-webui.service
```

To check if the service is in the correct control group, run:

```console
systemctl status  openquake-webui.service
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
