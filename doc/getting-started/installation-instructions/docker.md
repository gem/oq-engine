(docker)=

# Deploying Docker container

<img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px">

To be able to deploy and run the OpenQuake Engine Docker container you need **at least** Docker version **1.10**.

A basic knowledge about [Docker](https://docs.docker.com/engine/) and how this kind of application containers work is also required.
For more information about operating system support (which includes Linux, macOS and specific versions of Windows) and on how to install Docker, please refer to the official [Docker website](https://www.docker.com/products/docker).

## Features provided

Each container includes:

- Python 3.12 from official docker image
- Python dependencies (numpy, scipy, h5py...)
- OpenQuake Engine
- The `oq` command line tool
- The OpenQuake WebUI and API server (by default listening on port 8800)

## Available tags

Different sets of *TAGS* are provided (see below).
Images are hosted on [Docker Hub](https://hub.docker.com/r/openquake/engine/tags/).

### nightly

This container is updated on a daily basis and contains the latest code with the latest features. As the nightly binary packages is only recommended for testing and to see what the next stable version will have. It is not recommended for production.

```bash
$ docker pull docker.io/openquake/engine:nightly
```

### LTS

This container provides the long term support version of the OpenQuake Engine and its software stack. It is recommended for production.

```bash
$ docker pull docker.io/openquake/engine:LTS
```

### X.Y(.Z)

Whenever a new version of the OpenQuake Engine is released (starting from 2.2) a corresponding container providing the engine and its software stack is published and tagged. The last stable release is also available under the tag _latest_. If only the major and minor references (X.Y) are specified, the latest available corresponding version is pulled. Otherwise (X.Y.Z) the exact corresponding version is retrieved.

```bash
$ docker pull docker.io/openquake/engine:3.23
```
```bash
$ docker pull docker.io/openquake/engine:3.23.2
```
```bash
$ docker pull docker.io/openquake/engine:latest
```

## Deployment

### Docker single node deployment

Pull an image from Docker Hub (see [available-tags](https://hub.docker.com/r/openquake/engine/tags/)):

```bash
$ docker pull docker.io/openquake/engine[:TAG]
```

#### Headless mode

This modality is recommended when only the [WebUI or the API server](server.md) is used (for example as the backend for the [OpenQuake QGIS plugin](https://plugins.qgis.org/plugins/svir/)).

```bash
$ docker run --name <containername> -d -p 127.0.0.1:8800:8800  openquake/engine:nightly
```

Then you can connect to [http://127.0.0.1:8800](http://127.0.0.1:8800) to be able to access the [WebUI or the API server](server.md).

You can stop and start again your container with the following commands:

```bash
$ docker stop <containername>
```

```bash
$ docker start <containername>
```

#### TTY mode

This modality provides the same features as the headless mode plus the ability to drive the OpenQuake Engine via the `oq` command on a terminal.

```bash
$ docker run --name <containername> -t -i -p 127.0.0.1:8800:8800 openquake/engine:nightly 
```

The container prompt will appear, and you will have the possibility to run `oq` via the [command line interface](../running-calculations/unix.rst).

```bash
INFO:root:Creating the initial schema from 0000-base_schema.sql
INFO:root:Creating the versioning table revision_info
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0001-job.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0003-output.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0004-job.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0005-index.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0006-checksum.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0007-job.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0008-job-tag.sql
INFO:root:Executing /usr/src/oq-engine/openquake/server/db/schema/upgrades/0009-workflow.sql
INFO:root:Upgrade completed in 1.2584140300750732 seconds
WARNING:root:DB server started with /opt/openquake/bin/python3 on tcp://127.0.0.1:1908, pid 7
openquake@a4e28beda784:~$ oq --version
3.25.0

```

After you have restarted you container (same commands as the headless mode) you can re-attach the container shell using:

```bash
$ docker attach <containername>
[openquake@b318358ee053 ~]$

```

## Remove a container or an image

To destroy a container, type:

```bash
$ docker rm <containername>
```

To remove its image:

```bash
$ docker rmi openquake/<imagename>[:TAG]
```

You can print the list of containers and images using `$ docker ps -a` and `$ docker images`. For more details please refer to the [official Docker documentation](https://docs.docker.com/engine/).

## Docker advanced options

### Environment Variables

The Openquake image uses several environment variables:

`OQ_APPLICATION_MODE`

This optional variable overrides the WebUI `APPLICATION_MODE` (_PUBLIC_ by default, running the WebUI without authentication). If it is set to _RESTRICTED_, the authentication infrastructure will be enabled, restricting the access to authorized users.

`OQ_ADMIN_USERNAME`

This variable defines the superuser admin username in the WebUI

`OQ_ADMIN_PASSWORD`

This variable sets the superuser admin password for WebUI

`OQ_ADMIN_EMAIL`

This variable sets the superuser admin email for WebUI

`WEBUI_PATHPREFIX`

This variable overrides the default prefix path (`/engine`) for the WebUI

`EMAIL_BACKEND`

This variable specifies the backend used by Django to send emails (e.g. `django.core.mail.backends.smtp.EmailBackend`)

`EMAIL_HOST`

This variable specifies the host to use for sending emails (e.g. `smtp.gmail.com`)

`EMAIL_PORT`

This variable specifies the port to use for the SMTP server defined in EMAIL_HOST

`EMAIL_USE_TLS`

This variable specifies whether to use a TLS (secure) connection when talking to the SMTP server. This is used for explicit TLS connections, generally on port 587

`EMAIL_HOST_USER`

This variable specifies the username to use for the SMTP server defined in EMAIL_HOST

`EMAIL_HOST_PASSWORD`

This variable specifies the password to use for the SMTP server defined in EMAIL_HOST. This setting is used in conjunction with EMAIL_HOST_USER when authenticating to the SMTP server. If either of these settings is empty, Django won’t attempt authentication

`EMAIL_SUPPORT`

This variable specifies the email address to be used when replying to a Django email notification

`DJANGO_SETTINGS_MODULE`

This variable specifies the path to the python module containing Django settings, formatted in Python path syntax, e.g. `mysite.settings`. Note that the settings module should be on the Python sys.path.


To define all the environment variables, you can use a `.env` file with the following format:

```bash
OQ_APPLICATION_MODE=RESTRICTED
OQ_ADMIN_USERNAME=example
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

To run the docker (replacing `PATH` with the path to the directory containing the `.env` file):

```bash
$ docker run --name openquake -d -p 127.0.0.1:8800:8800 --env-file PATH/.env openquake/engine:nightly
```

This example runs a container named `openquake` using the `openquake/engine:nightly` image, and sets the value for the environment variables.

This binds port 8800 of the container to TCP port 8800 on 127.0.0.1 of the host machine, so the WebUI is reachable from the host machine using the url: `http://127.0.0.1:8800/engine`.

If the `WEBUI_PATHPREFIX` variable is specified (e.g. with the value `/path`), the WebUI is reachable from the host machine using the url: `http://127.0.0.1:8080/path` instead.

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the [OpenQuake users mailing list](https://groups.google.com/g/openquake-users).
