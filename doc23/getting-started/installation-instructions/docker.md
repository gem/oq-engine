(docker)=

# Deploying the OpenQuake Engine Docker container

<img src="https://upload.wikimedia.org/wikipedia/commons/7/79/Docker_%28container_engine%29_logo.png" width="150px"> [![Build Status](https://ci.openquake.org/buildStatus/icon?job=builders/docker-builder)](https://ci.openquake.org/job/builders/docker-builder)

To be able to deploy and run the OpenQuake Engine Docker container you need **at least** Docker version **1.10**. 

A basic knowledge about [Docker](https://docs.docker.com/engine/) and how this kind of application containers work is also required.
For more information about operating system support (which includes Linux, macOS and specific versions of Windows) and on how to install Docker, please refer to the official [Docker website](https://www.docker.com/products/docker).

## Features provided

Each container includes:

- Python 3.10 from official docker image
- Python dependencies (numpy, scipy, h5py...)
- OpenQuake Engine and Hazardlib
- The `oq` command line tool
- The OpenQuake WebUI and API server (by default listening on port 8800)
- Single node and multi-node installation (with dynamic scaling)

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
$ docker pull docker.io/openquake/engine:3.11
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
$ docker run --name <containername> -d -p 8800:8800 openquake/engine:nightly "oq webui start"
```

Then you can connect to [http://localhost:8800](http://localhost:8800) to be able to access the [WebUI or the API server](server.md).

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
$ docker run --name <containername> -t -i -p 8800:8800 openquake/engine:nightly bash
```

The container prompt will appear, here you play with the `oq` [shell command](../running-calculations/unix.rst).

```bash
[openquake@b318358ee053 ~]$ oq --version
3.10.0
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

#### Authentication support

Authentication support for the WebUI/API can be enabled passing the `LOCKDOWN` environment variable to the Docker container:

```bash
$ docker run -e LOCKDOWN=enabled --name myoqcontainer -d -p 8800:8800 openquake/engine:nightly "oq webui start"
```

## Getting help
If you need help or have questions/comments/feedback for us, you can subscribe to the OpenQuake users mailing list: https://groups.google.com/g/openquake-users
