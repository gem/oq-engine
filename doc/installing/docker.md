# Deploying the OpenQuake Engine Docker container

<img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px"> [![Build Status](https://ci.openquake.org/buildStatus/icon?job=builders/docker-builder)](https://ci.openquake.org/job/builders/docker-builder)

To be able to deploy and run the OpenQuake Engine Docker container you need **at least** Docker version **1.10**. 

A basic knowledge about [Docker](https://docs.docker.com/engine/) and how this kind of application containers work is also required.
For more information about operating system support (which includes Linux, macOS and specific versions of Windows) and on how to install Docker, please refer to the official [Docker website](https://www.docker.com/products/docker).

## Available tags

Currently two different set of *TAGS* are provided. Images are hosted on [Docker Hub](https://hub.docker.com/r/openquake/engine/tags/).

### master

This container is updated on weekly basis and contains the latest code with the latest features. As the nightly binary packages is only recommended for testing and to see what's the next stable version will have. It is not recommended for production.

```bash
$ docker pull docker.io/openquake/engine:latest
```

### X.Y

For each stable release (starting with 2.2) a container is published and tagged with its release version. This contains the stable release of the OpenQuake Engine and its software stack.

```bash
$ docker pull docker.io/openquake/engine:2.2
```

## Features provided

Each container includes:

- Python 3.6
- Python dependencies (numpy, scipy, h5py...)
- OpenQuake Engine and Hazardlib
- The `oq` command line tool
- The OpenQuake WebUI and API server (by default listening on port 8800)

Containers can be started in headless mode (only the WebUI access will be provided) or with a local console attached (required to run `oq` commands).

## Sources

If you want to customize container images, or you want to build your own, sources are provided on the [oq-containers/oq-docker](https://github.com/gem/oq-containers/tree/master/oq-docker) repo.


## Deploy and run

Pull an image from Docker Hub (see above about [TAG]):

```bash
$ docker pull docker.io/openquake/engine:[TAG]
```

### Headless mode

This modality is recommended when only the [WebUI or the API server](../running/server.md) is used (for example as the backend for the [OpenQuake QGIS plugin](https://plugins.qgis.org/plugins/svir/)).

```bash
$ docker run --name pleasegiveaname -d -p 8800:8800 openquake/engine:latest
```

Then you can connect to [http://localhost:8800](http://localhost:8800) to be able to access the [WebUI or the API server](../running/server.md).

You can stop and start again your container with the following commands:

```bash
$ docker stop pleasegiveaname
```

```bash
$ docker start pleasegiveaname
```

### TTY mode
 
This modality provides the same features as the headless mode plus the ability to drive the OpenQuake Engine via the `oq` command on a terminal.

```bash
$ docker run --name pleasegiveaname -t -i -p 8800:8800 openquake/engine:latest
```

The container prompt will appear, here you play with the `oq` [shell command](../running/unix.md).

```bash
[openquake@b318358ee053 ~]$ oq --version
2.2.0
```

After you have restarted you container (same commands as the headless mode) you can re-attach the container shell using:

```bash
$ docker attach pleasegiveaname
[openquake@b318358ee053 ~]$

```

## Remove a container or an image

To destroy a container, type:

```bash
$ docker rm pleasegiveaname
```

To remove its image:

```bash
$ docker rmi openquake/engine:[TAG]
```

You can print the list of containers and images using `$ docker ps -a` and `$ docker images`. For more details please refer to the [official Docker documentation](https://docs.docker.com/engine/).

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
