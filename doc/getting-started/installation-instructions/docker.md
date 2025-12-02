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

Currently two different set of *TAGS* are provided. Images are hosted on [Docker Hub](https://hub.docker.com/r/openquake/engine/tags/).

### nightly

This container is updated on daily basis and contains the latest code with the latest features. As the nightly binary packages is only recommended for testing and to see what's the next stable version will have. It is not recommended for production.

```bash
$ docker pull docker.io/openquake/engine:nightly
```

### X.Y

For each stable release (starting with 2.2) a container is published and tagged with its release version. This contains the stable release of the OpenQuake Engine and its software stack. For the last stable release is also available the latest tag

```bash
$ docker pull docker.io/openquake/engine:3.23
```
```bash
$ docker pull docker.io/openquake/engine:latest
```


## Deployment

### Docker single node deployment

Pull an image from Docker Hub (see [available-tags] (https://hub.docker.com/r/openquake/engine/tags/) ):

```bash
$ docker pull docker.io/openquake/engine[:TAG]
```

#### Headless mode

This modality is recommended when only the [WebUI or the API server](server.md) is used (for example as the backend for the [OpenQuake QGIS plugin](https://plugins.qgis.org/plugins/svir/)).

```bash
$ docker run --name <containername> -d -p  -p 127.0.0.1:8800:8800  openquake/engine:nightly "oq webui start 0.0.0.0:8800 -s"
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
$ docker run --name <containername> -t -i -p 127.0.0.1:8800:8800 openquake/engine:nightly bash
```

The container prompt will appear, here you play with the `oq` [shell command](../running-calculations/unix.rst).

```bash
[openquake@b318358ee053 ~]$ oq --version
3.23.0
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

### Docker advanced options

#### Environment Variables

The Openquake image uses several environment variables.

LOCKDOWN

This environment variable is required and set to True to enable the webui authentication.
The default value is False, and it can also be undefined if the webui authentication is not necessary.

```bash
$ docker run -e LOCKDOWN=True openquake/engine:nightly "oq webui start 0.0.0.0:8800 -s"
```
If you don't set any other environment variables the default values for admin login, password and email are: 'admin', 'admin', 'admin@example.com'.

OQ_ADMIN_LOGIN

This variable defines the superuser admin login in the webui.

OQ_ADMIN_PASSWORD

This environment variable sets the superuser admin password for webui.

OQ_ADMIN_EMAIL

This environment variable sets the superuser admin email for webui.

WEBUI_PATHPREFIX

This variable ovverides the default prefix path (/engine) for the webui.

```bash
$ docker run --name openquake -p 127.0.0.1:8800:8800 -e LOCKDOWN=True -e OQ_ADMIN_LOGIN=example -e OQ_ADMIN_PASSWORD=example -e OQ_ADMIN_EMAIL=login@example.com openquake/engine:nightly "oq webui start 0.0.0.0:8800 -s"
```

This example runs a container named openquake using the openquake/engine:nightly image and sets the value for the environment variables.

This binds port 8800 of the container to TCP port 8800 on 127.0.0.1 of the host machine, so the webui is reachable from the host machine using the url: http://127.0.0.1:8800/engine.

```bash
$ docker run --name openquake -p 127.0.0.1:8080:8800 -e LOCKDOWN=True -e WEBUI_PATHPREFIX='/path' openquake/engine:nightly "oq webui start 0.0.0.0:8800 -s"
```

This example runs a container named openquake using the openquake/engine:nightly image and sets the value for the environment variables.

This binds port 8800 of the container to TCP port 8080 on 127.0.0.1 of the host machine, so the webui is reachable from host machine using the url: http://127.0.0.1:8080/path

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
