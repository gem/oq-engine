
#  OpenQuake Docker images <img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px">


## End user documentation

The main documentation, intended for end users, is available under the [documentation area](../doc/installing/docker.md)


### Build the OpenQuake Engine docker

```bash
$ docker build -t openquake/engine -f Dockerfile.engine .
```

### Custom build args

```bash
--build-arg oq_branch=master      ## oq-engine branch
```

### Testing the image

If you want to use the nightly build instead of the latest, the files are in the docker folder.
To create a development image using the TAG nightly use the following command:

```bash
$ docker build -t openquake/engine:nightly -f Dockerfile.dev .
```

Please note that the nightly image is meant for testing purposes and not for production.

### Debug

It's possible to enter a container as `root`, for debug purposes, running

```bash
$ docker run -u 0 -t -i  openquake/engine:nightly /bin/bash
```

### Environment Variables
The Openquake image uses several environment variables

OQ_APPLICATION_MODE

This environment variable is required and set to RESTRICTED to enable the webui authentication.

OQ_ADMIN_LOGIN

This variable defines the superuser admin login in the webui

OQ_ADMIN_PASSWORD

This environment variable sets the superuser admin password for webui

OQ_ADMIN_EMAIL

This environment variable sets the superuser admin email for webui

WEBUI_PATHPREFIX

This variable overrides the default prefix path (/engine) for the webui

EMAIL_BACKEND
This variable specifies the backend used by Django to send emails (e.g. 'django.core.mail.backends.smtp.EmailBackend')

EMAIL_HOST
This variable specifies the host to use for sending email (e.g. 'smtp.gmail.com')

EMAIL_PORT
Port to use for the SMTP server defined in EMAIL_HOST

EMAIL_USE_TLS
Whether to use a TLS (secure) connection when talking to the SMTP server. This is used for explicit TLS connections, generally on port 587

EMAIL_HOST_USER
Username to use for the SMTP server defined in EMAIL_HOST

EMAIL_HOST_PASSWORD
Password to use for the SMTP server defined in EMAIL_HOST. This setting is used in conjunction with EMAIL_HOST_USER when authenticating to the SMTP server. If either of these settings is empty, Django won’t attempt authentication

EMAIL_SUPPORT
Email address to be used when replying to a Django email notification

DJANGO_SETTINGS_MODULE
When you use Django, you have to tell it which settings you’re using. Do this by using an environment variable, DJANGO_SETTINGS_MODULE.
The value of DJANGO_SETTINGS_MODULE should be in Python path syntax, e.g. mysite.settings. Note that the settings module should be on the Python sys.path.


To define all the environment variables, you can use a .env file in the following format:

```bash
OQ_APPLICATION_MODE=RESTRICTED
OQ_ADMIN_LOGIN=example
OQ_ADMIN_PASSWORD=example
OQ_ADMIN_EMAIL=login@example.com
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_SUPPORT=
DJANGO_SETTINGS_MODULE=openquake.server.settings
```

To run the docker:

```bash
$ docker run --name openquake -d -p 127.0.0.1:8800:8800 --env-file PATH/.env openquake/engine:nightly
```

This example runs a container named openquake using the openquake/engine:nightly image and set the value for the environment variables.

This binds port 8800 of the container to TCP port 8800 on 127.0.0.1 of the host machine, so the webui is reachable from host machine using the url: http://127.0.0.1:8800/engine

```bash
OQ_APPLICATION_MODE=RESTRICTED
OQ_ADMIN_LOGIN=example
OQ_ADMIN_PASSWORD=example
OQ_ADMIN_EMAIL=login@example.com
EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST=
EMAIL_PORT=
EMAIL_USE_TLS=
EMAIL_HOST_USER=
EMAIL_HOST_PASSWORD=
EMAIL_SUPPORT=
DJANGO_SETTINGS_MODULE=openquake.server.settings
WEBUI_PATHPREFIX='/path'
```
To run the docker:

```bash
$ docker run --name openquake -d -p 127.0.0.1:8080:8800 --env-file PATH/.env  openquake/engine:nightly
```

This example runs a container named openquake using the openquake/engine:nightly image and set the value for the environment variables.

This binds port 8800 of the container to TCP port 8080 on 127.0.0.1 of the host machine, so the webui is reachable from host machine using the url: http://127.0.0.1:8080/path
