# Docker single node deployment

Pull an image from Docker Hub (see [available-tags](#available-tags)):

```bash
$ docker pull docker.io/openquake/engine[:TAG]
```

## Headless mode

This modality is recommended when only the [WebUI or the API server](../running/server.md) is used (for example as the backend for the [OpenQuake QGIS plugin](https://plugins.qgis.org/plugins/svir/)).

```bash
$ docker run --name <containername> -d -p 8800:8800 openquake/engine:latest
```

Then you can connect to [http://localhost:8800](http://localhost:8800) to be able to access the [WebUI or the API server](../running/server.md).

You can stop and start again your container with the following commands:

```bash
$ docker stop <containername>
```

```bash
$ docker start <containername>
```

## TTY mode
 
This modality provides the same features as the headless mode plus the ability to drive the OpenQuake Engine via the `oq` command on a terminal.

```bash
$ docker run --name <containername> -t -i -p 8800:8800 openquake/engine:latest
```

The container prompt will appear, here you play with the `oq` [shell command](../running/unix.md).

```bash
[openquake@b318358ee053 ~]$ oq --version
2.8.0
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

### Docker

- [Introduction](../installing/docker.md)
- [Cluster deployment](cluster.md)
- [Advanced options](advanced.md)
- [Build from sources](../../docker#build-openquake-docker-images)

***

## Getting help
If you need help or have questions/comments/feedback for us, you can:
  * Subscribe to the OpenQuake users mailing list: https://groups.google.com/forum/?fromgroups#!forum/openquake-users
  * Contact us on IRC: irc.freenode.net, channel #openquake
